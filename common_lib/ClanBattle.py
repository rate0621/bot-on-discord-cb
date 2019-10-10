import os, sys
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


here = os.path.join( os.path.dirname(os.path.abspath(__file__)))
sys.path.append(here)
from GspreadWrapper import GspreadWrapper


SHEETS_AND_COLUMS = {
    'clan_members': ['user_id', 'user_name'],
    'boss_master' : ['event_month', 'boss_number', 'boss_name', 'max_hit_point', 'target'],
    'boss_reserve': ['datetime', 'user_id', 'user_name', 'boss_number', 'is_attack'],
    'attack_log'  : ['datetime', 'user_id', 'user_name', 'boss_number', 'boss_name', 'damage', 'score', 'is_carry_over'],
    'carry_over'  : ['datetime', 'user_id', 'user_name', 'boss_number', 'boss_name', 'time'],
    'current_boss': ['boss_number', 'hit_point']
}

class ClanBattle(GspreadWrapper):
    def __init__(self):
        TYPE           = os.getenv("GS_TYPE",           "")
        CLIENT_EMAIL   = os.getenv("GS_CLIENT_EMAIL",   "")
        PRIVATE_KEY    = os.getenv("GS_PRIVATE_KEY",    "")
        PRIVATE_KEY_ID = os.getenv("GS_PRIVATE_KEY_ID", "")
        CLIENT_ID      = os.getenv("GS_CLIENT_ID",      "")

        key_dict = {
            'type'          : TYPE,
            'client_email'  : CLIENT_EMAIL,
            'private_key'   : PRIVATE_KEY,
            'private_key_id': PRIVATE_KEY_ID,
            'client_id'     : CLIENT_ID,
        }

        super().__init__(key_dict)

    def init(self):
        #gw = GspreadWrapper.GspreadWrapper()

        # 必要なシート(とカラム)の作成
        for sheet in SHEETS_AND_COLUMS:
            self.check_sheet_exists_and_create(sheet)
            ws = self.get_gsfile(sheet)

            for i, col in enumerate(SHEETS_AND_COLUMS[sheet]):
                label = self.toAlpha(i + 1) + str(1)
                ws.update_acell(label, col)


    def get_today_from_and_to(self):
        today = datetime.now() - timedelta(hours=5)
        tomorrow = today + timedelta(days=1)
        f = today.strftime("%Y/%m/%d 05:00:00")
        t = tomorrow.strftime("%Y/%m/%d 04:59:00")
        return f, t


    def all_clear(self):
        '''
        クラバト用のDB（スプシ）の内容をすべて空っぽにする。主に開発時にのみ使う。
        '''
        #gw = GspreadWrapper.GspreadWrapper()
        tl = ['boss_reserve', 'attack_log']
        for t in tl:
            ws = self.get_gsfile(t)
            df = self.create_gsdf(ws)

            col_lastnum = len(df.columns)
            row_lastnum = len(df.index)

            cell_list = ws.range('A2:'+self.toAlpha(col_lastnum)+str(row_lastnum + 1))
            for cell in cell_list:
                cell.value = ''

            ws.update_cells(cell_list)


    def sheet_clear(self, t):
        #gw = GspreadWrapper.GspreadWrapper()
        ws = self.get_gsfile(t)
        df = self.create_gsdf(ws)

        col_lastnum = len(df.columns)
        row_lastnum = len(df.index)

        cell_list = ws.range('A2:'+self.toAlpha(col_lastnum)+str(row_lastnum + 1))
        for cell in cell_list:
            cell.value = ''

        ws.update_cells(cell_list)


    def get_bosses(self):
        #gw = GspreadWrapper.GspreadWrapper()
        ws = self.get_gsfile('boss_master')
        df = self.create_gsdf(ws)

        return df[['boss_number', 'boss_name', 'target']].values


    def boss_reserve(self, user_id, boss_num):
        _datetime = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        #gw = GspreadWrapper.GspreadWrapper()
        ws = self.get_gsfile('boss_reserve')
        df = self.create_gsdf(ws)

        # スプシをそのまま読み込むと文字列（object）型になってしまうためfloatに変換
        l = ['boss_number', 'is_attack']
        df[l] = df[l].astype('float')

        if self.reserved_check(user_id, boss_num):
            print ('すでに予約済みです')
        else:
            print ('予約します')

            append_row_num = len(ws.col_values(1)) + 1
            s = pd.Series([_datetime, user_id, '=VLOOKUP(B'+str(append_row_num)+',clan_members!A2:B200,2,False)', boss_num, 0], index=df.columns)

            # MEMO: appendするときはnameを指定しないとエラーになるが、ignore_index=True とすることで連番を振ってくれる
            df = df.append(s, ignore_index=True)

            col_lastnum = len(df.columns)
            row_lastnum = len(df.index)

            cell_list = ws.range('A2:'+self.toAlpha(col_lastnum)+str(row_lastnum + 1))
            for cell in cell_list:
                val = df.iloc[cell.row - 2][cell.col - 1]
                cell.value = val

            ws.update_cells(cell_list, value_input_option='USER_ENTERED')
            print ('予約完了')

    def get_current_boss(self):
        #gw = GspreadWrapper.GspreadWrapper()
        boss_df  = self.create_gsdf(self.get_gsfile('current_boss'))
        boss_num = boss_df.at[0, 'boss_number']
        boss_hp  = boss_df.at[0, 'hit_point']

        boss_master_df = self.create_gsdf(self.get_gsfile('boss_master'))
        boss_name = boss_master_df.loc[boss_master_df.boss_number == boss_num, 'boss_name']

        return boss_num, boss_name.item(), boss_hp

    def attack(self, user_id):
        '''
        凸の宣言
        '''
        attack_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        #self.gc = GspreadWrapper.GspreadWrapper()
        boss_num, boss_name, boss_hp = self.get_current_boss()

        ws = self.get_gsfile('attack_log')
        df = self.create_gsdf(ws)
        col_lastnum = len(df.columns)

        append_row_num = len(ws.col_values(1)) + 1
        val_list = [attack_time, user_id, '=VLOOKUP(B'+str(append_row_num)+',clan_members!A2:B200,2,False)', boss_num, '', 0, 0, 0]

        cell_list  = ws.range('A'+str(append_row_num)+':'+self.toAlpha(col_lastnum)+str(append_row_num))
        for (cell, val) in zip(cell_list, val_list):
            if val == '':
                continue

            cell.value = val

        # value_input_option='USER_ENTERED' を入れることで、スプシの関数をそのまま埋め込むことができる
        ws.update_cells(cell_list, value_input_option='USER_ENTERED')

    def attack_check(self, user_id):
        #gw = GspreadWrapper.GspreadWrapper()
        ws = self.get_gsfile('attack_log')
        df = self.create_gsdf(ws)

        # @をつけると変数を埋め込むことができる
        if len(df.query("user_id == @user_id & damage == 0")):
            return 1
        else:
            return 0

    def attack_cancel(self, user_id):
        #gw = GspreadWrapper.GspreadWrapper()
        ws = self.get_gsfile('attack_log')
        df = self.create_gsdf(ws)

        #queryで取得した結果の末尾のレコードを削除する
        df.drop(index=df.query("user_id == @user_id & damage == 0").index[-1], inplace=True)

        # 上の処理でdropするとvlookupの関数の値がずれてしまうため治す
        df.reset_index(drop=True, inplace=True)
        for i in df.index.values:
            df.iloc[i]['user_name'] = '=VLOOKUP(B' + str(i + 2) + ',clan_members!A2:B200,2,False)'


        # スプシからデータを取得すると数値になってしまうため変換する
        df['datetime'] = df['datetime'].map(self.excel_date)
        df['datetime'] = df['datetime'].astype(str)

        col_lastnum = len(df.columns)
        row_lastnum = len(df.index)

        self.sheet_clear('attack_log')
        cell_list = ws.range('A2:'+self.toAlpha(col_lastnum)+str(row_lastnum + 1))
        for cell in cell_list:
            val = df.iloc[cell.row - 2][cell.col - 1]
            cell.value = val

        ws.update_cells(cell_list, value_input_option='USER_ENTERED')

    def get_attack_count(self):
        #gw = GspreadWrapper.GspreadWrapper()
        ws = self.get_gsfile('attack_log')
        df = self.create_gsdf(ws)

        # スプシからデータを取得すると数値になってしまうため変換する
        df['datetime'] = df['datetime'].map(self.excel_date)
        df['datetime'] = pd.to_datetime(df['datetime'])

        f, t = self.get_today_from_and_to()

        #queryで取得した結果の末尾のレコードを削除する
        return len(df[(df.datetime >= f) & (df.datetime <= t) & (df.is_carry_over == 0)])


    def update_current_boss(self, damage):
        '''
        current_bossの情報を更新する。
        もし、撃破した場合は、その返り値を返す。
        '''
        is_carry_over = 0

        # さきにcurrent_bossの情報更新
        #gw = GspreadWrapper.GspreadWrapper()
        boss_num, boss_name, boss_hp = self.get_current_boss()
        ws = self.get_gsfile('current_boss')
        df = self.create_gsdf(ws)

        # スプシをそのまま読み込むと文字列（object）型になってしまうためfloatに変換
        l = ['boss_number', 'hit_point']
        df[l] = df[l].astype('float')

        df.loc[df.boss_number == boss_num, 'hit_point'] = df.loc[df.boss_number == boss_num, 'hit_point'] - damage

        # ボスのHPが０かマイナスになったかチェック。やり方については以下を参考
        # https://teratail.com/questions/151694
        if ((df.loc[df.boss_number == boss_num, 'hit_point'].item() > 0) - (df.loc[df.boss_number == boss_num, 'hit_point'].item() < 0)) <= 0:
            self.lotate_boss()
            is_carry_over = 1
        else:
            col_lastnum = len(df.columns)
            row_lastnum = len(df.index)

            cell_list = ws.range('A2:'+self.toAlpha(col_lastnum)+str(row_lastnum + 1))
            for cell in cell_list:
                val = df.iloc[cell.row - 2][cell.col - 1]
                cell.value = val

            ws.update_cells(cell_list, value_input_option='USER_ENTERED')

        return is_carry_over


    def finish_attack(self, user_id, damage, is_carry_over):
        '''
        ダメージ情報を更新
        '''
        #gw = GspreadWrapper.GspreadWrapper()
        ws = self.get_gsfile('attack_log')
        df = self.create_gsdf(ws)

        # スプシをそのまま読み込むと文字列（object）型になってしまうためfloatに変換
        l = ['boss_number', 'damage', 'score', 'is_carry_over']
        df[l] = df[l].astype('float')

        df.loc[(df.user_id == user_id) & (df.damage == 0), 'is_carry_over'] = is_carry_over
        df.loc[(df.user_id == user_id) & (df.damage == 0), 'damage']        = damage

        col_lastnum = len(df.columns)
        row_lastnum = len(df.index)

        cell_list = ws.range('A2:'+self.toAlpha(col_lastnum)+str(row_lastnum + 1))
        for cell in cell_list:
            val = df.iloc[cell.row - 2][cell.col - 1]
            cell.value = val

        ws.update_cells(cell_list, value_input_option='USER_ENTERED')


    def reserved_check(self, user_id, boss_num=None):
        #gw = GspreadWrapper.GspreadWrapper()
        ws = self.get_gsfile('boss_reserve')
        df = self.create_gsdf(ws)

        if boss_num is None:
            w = "user_id == @user_id & is_attack == 0"
        else:
            boss_num = int(boss_num)
            w = "user_id == @user_id & boss_number == @boss_num & is_attack == 0" 

        # @をつけると変数を埋め込むことができる
        if len(df.query(w)):
            return 1
        else:
            return 0

    def get_reserved_users(self, boss_num):
        #gw = GspreadWrapper.GspreadWrapper()
        ws = self.get_gsfile('boss_reserve')
        df = self.create_gsdf(ws)

        return df.query("boss_number == @boss_num & is_attack == 0").user_id.tolist()


    def get_all_reserved_users(self, boss_array):
        #gw = GspreadWrapper.GspreadWrapper()
        ws = self.get_gsfile('boss_reserve')
        df = self.create_gsdf(ws)

        dic = {}
        for boss in boss_array:
            dic.setdefault(boss[0], [])
            for u in df.query("boss_number == @boss[0] & is_attack == 0").user_id.tolist():
                dic.setdefault(boss[0], []).append(u)

        return dic

    def get_carry_over_users(self):
        #gw = GspreadWrapper.GspreadWrapper()
        ws = self.get_gsfile('carry_over')
        df = self.create_gsdf(ws)

        df.set_index('user_id', inplace=True)
        return df

    def reserved_clear(self, user_id, boss_num=None):
        #gw = GspreadWrapper.GspreadWrapper()
        ws = self.get_gsfile('boss_reserve')
        df = self.create_gsdf(ws)
        if boss_num is None:
            df.loc[(df.user_id == user_id) & (df.is_attack == 0), 'is_attack'] = 1
        else:
            boss_num = int(boss_num)
            df.loc[(df.user_id == user_id) & (df.is_attack == 0) & (df.boss_number == boss_num), 'is_attack'] = 1

        col_lastnum = len(df.columns)
        row_lastnum = len(df.index)

        cell_list = ws.range('A2:'+self.toAlpha(col_lastnum)+str(row_lastnum + 1))
        for cell in cell_list:
            val = df.iloc[cell.row - 2][cell.col - 1]
            cell.value = val

        ws.update_cells(cell_list, value_input_option='USER_ENTERED')

    def get_remaining_atc_count(self):
        #gw = GspreadWrapper.GspreadWrapper()
        ws = self.get_gsfile('attack_log')
        df = self.create_gsdf(ws)

        # スプシからデータを取得すると数値になってしまうため変換する
        df['datetime'] = df['datetime'].map(self.excel_date)
        df['datetime'] = pd.to_datetime(df['datetime'])

        f, t = self.get_today_from_and_to()

        #queryで取得した結果の末尾のレコードを削除する
        return 90 - len(df[(df.datetime >= f) & (df.datetime <= t) & (df.is_carry_over == 0)])


    def lotate_boss(self):
        #gw = GspreadWrapper.GspreadWrapper()
        boss_num, boss_name, boss_hp = self.get_current_boss()
        ws = self.get_gsfile('current_boss')
        df = self.create_gsdf(ws)

        # スプシをそのまま読み込むと文字列（object）型になってしまうためfloatに変換
        l = ['boss_number', 'hit_point']
        df[l] = df[l].astype('float')

        df.iloc[0, 0] += 1

        if df.iloc[0, 0] > 5:
            df.iloc[0, 0] = 1

        ws2 = self.get_gsfile('boss_master')
        df2 = self.create_gsdf(ws2)

        # スプシをそのまま読み込むと文字列（object）型になってしまうためfloatに変換
        l = ['boss_number', 'max_hit_point']
        df2[l] = df2[l].astype('float')

        # なにかもっといいやりかたがあるはずだがうまく行かないのでいったんこれですすめる(.item()を使うといけるかも)
        df.iloc[0, 1] = df2.loc[df.iloc[0, 0] - 1, 'max_hit_point']

        col_lastnum = len(df.columns)
        row_lastnum = len(df.index)

        cell_list = ws.range('A2:'+self.toAlpha(col_lastnum)+str(row_lastnum + 1))
        for cell in cell_list:
            val = df.iloc[cell.row - 2][cell.col - 1]
            cell.value = val

        ws.update_cells(cell_list, value_input_option='USER_ENTERED')

    def insert_carry_over(self, user_id, time):
        #gw = GspreadWrapper.GspreadWrapper()
        ws = self.get_gsfile('carry_over')
        df = self.create_gsdf(ws)
        boss_num, boss_name, boss_hp = cb.get_current_boss()

        _datetime = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        append_row_num = len(ws.col_values(1)) + 1
        s = pd.Series([_datetime, user_id, '=VLOOKUP(B'+str(append_row_num)+',clan_members!A2:B200,2,False)', boss_num, '', time], index=df.columns)

        # MEMO: appendするときはnameを指定しないとエラーになるが、ignore_index=True とすることで連番を振ってくれる
        df = df.append(s, ignore_index=True)

        col_lastnum = len(df.columns)
        row_lastnum = len(df.index)

        cell_list = ws.range('A2:'+self.toAlpha(col_lastnum)+str(row_lastnum + 1))
        for cell in cell_list:
            val = df.iloc[cell.row - 2][cell.col - 1]
            cell.value = val

        ws.update_cells(cell_list, value_input_option='USER_ENTERED')



if __name__ == '__main__':
    cb = ClanBattle()
    user_id = '474761974832431148'
    ### 初期化
    #cb.init()
    #exit()
    ###

    #cb.boss_reserve('478542546537283594', 5)
    #cb.all_clear()

#    ### 「凸」→「凸完了」したときの動作
#    damage = 8000000
#    cb.attack(user_id)
#    is_defeat = cb.update_current_boss(damage)
#    cb.finish_attack(user_id, damage, is_defeat)
#    exit()
#    ###

    ### 「凸キャンセル」
#    cb.attack('474761974832431148')
#    cb.attack_cancel('474761974832431148')
    ###

    ### 「予約確認」
    co_users_df = cb.get_carry_over_users()

    b_df      = cb.get_bosses()
    user_dict = cb.get_all_reserved_users(b_df)
    boss_num, boss_name, boss_hp = cb.get_current_boss()

    message = "予約状況はこんな感じね。\n```\n"
    for k, b in zip(user_dict, b_df):
        if k == boss_num:
            message += "【" + str(k) + "】(目安:" + str(b[2]) + ")" + " ←イマココ(残り、" + str(boss_hp) + ") \n"
        else:
            message += "【" + str(k) + "】(目安:" + str(b[2]) + ")\n"

        for i, u in enumerate(user_dict[k]):
            if (u in co_users_df.index):
                message += "    " + u + " ((持ち越し:" + str(co_users_df.at[u, 'time']) + ")" + "\n"
            else:
                message += "    " + u + "\n"

    message += "残り凸数は、" + str(cb.get_remaining_atc_count()) + "よ。\n"
    message += "```"

    print (message)
    ###

    ### 「持ち越し　114514」
    #cb.insert_carry_over(user_id, 50)


    #a, b, c = cb.get_current_boss()
    #cb.reserved_check('474761974832431148', 3)
    #print (cb.get_attack_count())
    #cb.get_today_from_and_to()



