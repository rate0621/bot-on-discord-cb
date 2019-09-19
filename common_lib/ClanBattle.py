import os, sys
import sqlite3
import pandas as pd
from datetime import datetime

import Common

class ClanBattle():
    def __init__(self):
        pass


    def get_bosses(self):
        ws = self.get_gsfile('boss_master')


    def boss_reserve(self, month, user_id, boss_num):
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
            s = pd.Series([month, user_id, '=VLOOKUP(B'+str(append_row_num)+',clan_members!A2:B200,2,False)', boss_num, 0], index=df.columns)

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

    def finish_attack(self, user_id, damage):
        '''
        ダメージ情報を更新
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


        # 凸予約していた場合、凸したフラグを立てる
        if self.reserved_check(user_id, boss_num):
            self.reserved_clear(user_id, boss_num)


    def reserved_check(self, user_id, boss_num):
        cm = Common.Common()
        ws = cm.get_gsfile('boss_reserve')
        df = cm.create_gsdf(ws)

        # @をつけると変数を埋め込むことができる
        if len(df.query("user_id == @user_id & boss_number == @boss_num & is_attack == 0")):
            return 1
        else:
            return 0


    def reserved_clear(self, user_id, boss_num):
        cm = Common.Common()
        ws = cm.get_gsfile('boss_reserve')
        df = cm.create_gsdf(ws)
        df.loc[(df.user_id == user_id) & (df.is_attack == 0), 'is_attack'] = 1

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
    #cb.boss_reserve('2019/08', '478542546537283594', 5)
    #cb.attack('478542546537283594')
    #cb.finish_attack('478542546537283594', 12000000)
    #cb.lotate_boss()
    a, b, c = cb.get_current_boss()
    print (a)
    print (b)
    print (c)



