import os, sys
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import Common



class ClanBattle():
    def __init__(self):
        pass

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
        cm = Common.Common()
        tl = ['boss_reserve', 'attack_log']
        for t in tl:
            ws = cm.get_gsfile(t)
            df = cm.create_gsdf(ws)

            col_lastnum = len(df.columns)
            row_lastnum = len(df.index)

            cell_list = ws.range('A2:'+cm.toAlpha(col_lastnum)+str(row_lastnum + 1))
            for cell in cell_list:
                cell.value = ''

            ws.update_cells(cell_list)

    def sheet_clear(self, t):
        cm = Common.Common()
        ws = cm.get_gsfile(t)
        df = cm.create_gsdf(ws)

        col_lastnum = len(df.columns)
        row_lastnum = len(df.index)

        cell_list = ws.range('A2:'+cm.toAlpha(col_lastnum)+str(row_lastnum + 1))
        for cell in cell_list:
            cell.value = ''

        ws.update_cells(cell_list)



    def get_bosses(self):
        cm = Common.Common()
        ws = cm.get_gsfile('boss_master')
        df = cm.create_gsdf(ws)

        return df[['boss_number', 'boss_name']].values


    def boss_reserve(self, user_id, boss_num):
        _datetime = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        cm = Common.Common()
        ws = cm.get_gsfile('boss_reserve')
        df = cm.create_gsdf(ws)

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

            cell_list = ws.range('A2:'+cm.toAlpha(col_lastnum)+str(row_lastnum + 1))
            for cell in cell_list:
                val = df.iloc[cell.row - 2][cell.col - 1]
                cell.value = val

            ws.update_cells(cell_list, value_input_option='USER_ENTERED')
            print ('予約完了')

    def get_current_boss(self):
        cm = Common.Common()
        boss_df  = cm.create_gsdf(cm.get_gsfile('current_boss'))
        boss_num = boss_df.at[0, 'boss_number']
        boss_hp  = boss_df.at[0, 'hit_point']

        boss_master_df = cm.create_gsdf(cm.get_gsfile('boss_master'))
        boss_name = boss_master_df.loc[boss_master_df.boss_number == boss_num, 'boss_name']

        return boss_num, boss_name.item(), boss_hp

    def attack(self, user_id):
        '''
        凸の宣言
        '''
        attack_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        cm = Common.Common()
        boss_num, boss_name, boss_hp = self.get_current_boss()

        ws = cm.get_gsfile('attack_log')
        df = cm.create_gsdf(ws)
        col_lastnum = len(df.columns)

        append_row_num = len(ws.col_values(1)) + 1
        val_list = [attack_time, user_id, '=VLOOKUP(B'+str(append_row_num)+',clan_members!A2:B200,2,False)', boss_num, '', 0, 0, 0]

        cell_list  = ws.range('A'+str(append_row_num)+':'+cm.toAlpha(col_lastnum)+str(append_row_num))
        for (cell, val) in zip(cell_list, val_list):
            if val == '':
                continue

            cell.value = val

        # value_input_option='USER_ENTERED' を入れることで、スプシの関数をそのまま埋め込むことができる
        ws.update_cells(cell_list, value_input_option='USER_ENTERED')

    def attack_check(self, user_id):
        cm = Common.Common()
        ws = cm.get_gsfile('attack_log')
        df = cm.create_gsdf(ws)

        # @をつけると変数を埋め込むことができる
        if len(df.query("user_id == @user_id & damage == 0")):
            return 1
        else:
            return 0

    def attack_cancel(self, user_id):
        cm = Common.Common()
        ws = cm.get_gsfile('attack_log')
        df = cm.create_gsdf(ws)

        #queryで取得した結果の末尾のレコードを削除する
        df.drop(index=df.query("user_id == @user_id & damage == 0").index[-1], inplace=True)

        # スプシからデータを取得すると数値になってしまうため変換する
        df['datetime'] = df['datetime'].map(cm.excel_date)
        df['datetime'] = df['datetime'].astype(str)

        col_lastnum = len(df.columns)
        row_lastnum = len(df.index)

        self.sheet_clear('attack_log')
        cell_list = ws.range('A2:'+cm.toAlpha(col_lastnum)+str(row_lastnum + 1))
        for cell in cell_list:
            val = df.iloc[cell.row - 2][cell.col - 1]
            cell.value = val

        ws.update_cells(cell_list, value_input_option='USER_ENTERED')

    def get_attack_count(self):
        cm = Common.Common()
        ws = cm.get_gsfile('attack_log')
        df = cm.create_gsdf(ws)

        # スプシからデータを取得すると数値になってしまうため変換する
        df['datetime'] = df['datetime'].map(cm.excel_date)
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
        cm = Common.Common()
        boss_num, boss_name, boss_hp = self.get_current_boss()
        ws = cm.get_gsfile('current_boss')
        df = cm.create_gsdf(ws)

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

            cell_list = ws.range('A2:'+cm.toAlpha(col_lastnum)+str(row_lastnum + 1))
            for cell in cell_list:
                val = df.iloc[cell.row - 2][cell.col - 1]
                cell.value = val

            ws.update_cells(cell_list, value_input_option='USER_ENTERED')

        return is_carry_over


    def finish_attack(self, user_id, damage, is_carry_over):
        '''
        ダメージ情報を更新
        '''
        cm = Common.Common()
        ws = cm.get_gsfile('attack_log')
        df = cm.create_gsdf(ws)

        # スプシをそのまま読み込むと文字列（object）型になってしまうためfloatに変換
        l = ['boss_number', 'damage', 'score', 'is_carry_over']
        df[l] = df[l].astype('float')

        df.loc[(df.user_id == user_id) & (df.damage == 0), 'is_carry_over'] = is_carry_over
        df.loc[(df.user_id == user_id) & (df.damage == 0), 'damage']        = damage

        col_lastnum = len(df.columns)
        row_lastnum = len(df.index)

        cell_list = ws.range('A2:'+cm.toAlpha(col_lastnum)+str(row_lastnum + 1))
        for cell in cell_list:
            val = df.iloc[cell.row - 2][cell.col - 1]
            cell.value = val

        ws.update_cells(cell_list, value_input_option='USER_ENTERED')


    def reserved_check(self, user_id, boss_num=None):
        cm = Common.Common()
        ws = cm.get_gsfile('boss_reserve')
        df = cm.create_gsdf(ws)

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
        cm = Common.Common()
        ws = cm.get_gsfile('boss_reserve')
        df = cm.create_gsdf(ws)

        return df.query("boss_number == @boss_num & is_attack == 0").user_id.tolist()


    def get_all_reserved_users(self, boss_array):
        cm = Common.Common()
        ws = cm.get_gsfile('boss_reserve')
        df = cm.create_gsdf(ws)

        dic = {}
        for boss in boss_array:
            dic.setdefault(boss[0], [])
            for u in df.query("boss_number == @boss[0] & is_attack == 0").user_id.tolist():
                dic.setdefault(boss[0], []).append(u)

        return dic

    def reserved_clear(self, user_id, boss_num=None):
        cm = Common.Common()
        ws = cm.get_gsfile('boss_reserve')
        df = cm.create_gsdf(ws)
        if boss_num is None:
            df.loc[(df.user_id == user_id) & (df.is_attack == 0), 'is_attack'] = 1
        else:
            boss_num = int(boss_num)
            df.loc[(df.user_id == user_id) & (df.is_attack == 0) & (df.boss_number == boss_num), 'is_attack'] = 1

        col_lastnum = len(df.columns)
        row_lastnum = len(df.index)

        cell_list = ws.range('A2:'+cm.toAlpha(col_lastnum)+str(row_lastnum + 1))
        for cell in cell_list:
            val = df.iloc[cell.row - 2][cell.col - 1]
            cell.value = val

        ws.update_cells(cell_list, value_input_option='USER_ENTERED')


    def lotate_boss(self):
        cm = Common.Common()
        boss_num, boss_name, boss_hp = self.get_current_boss()
        ws = cm.get_gsfile('current_boss')
        df = cm.create_gsdf(ws)

        # スプシをそのまま読み込むと文字列（object）型になってしまうためfloatに変換
        l = ['boss_number', 'hit_point']
        df[l] = df[l].astype('float')

        df.iloc[0, 0] += 1

        if df.iloc[0, 0] > 5:
            df.iloc[0, 0] = 1

        ws2 = cm.get_gsfile('boss_master')
        df2 = cm.create_gsdf(ws2)

        # スプシをそのまま読み込むと文字列（object）型になってしまうためfloatに変換
        l = ['boss_number', 'max_hit_point']
        df2[l] = df2[l].astype('float')

        # なにかもっといいやりかたがあるはずだがうまく行かないのでいったんこれですすめる(.item()を使うといけるかも)
        df.iloc[0, 1] = df2.loc[df.iloc[0, 0] - 1, 'max_hit_point']

        col_lastnum = len(df.columns)
        row_lastnum = len(df.index)

        cell_list = ws.range('A2:'+cm.toAlpha(col_lastnum)+str(row_lastnum + 1))
        for cell in cell_list:
            val = df.iloc[cell.row - 2][cell.col - 1]
            cell.value = val

        ws.update_cells(cell_list, value_input_option='USER_ENTERED')


if __name__ == '__main__':
    cb = ClanBattle()
    #cb.boss_reserve('478542546537283594', 5)
    #cb.all_clear()
    #cb.attack('474761974832431148')
    #cb.attack_cancel('474761974832431148')
    #cb.finish_attack('478542546537283594', 12000000)
    #cb.lotate_boss()
    a = cb.get_bosses()
    cb.get_reserved_users(a)
    #a, b, c = cb.get_current_boss()
    #cb.reserved_check('474761974832431148', 3)
    #print (cb.get_attack_count())
    #cb.get_today_from_and_to()



