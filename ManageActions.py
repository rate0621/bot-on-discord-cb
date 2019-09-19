import os, re
from datetime import datetime, timedelta, timezone
import discord
import pandas as pd

import time

import common_lib.PriDb  as PriDb
import common_lib.Common as Common

class ManageActions:
    def __init__(self):
        pass



    def check_and_action(self, req):

        # NOTE:
        # <@478542546537283594> hoge という形でreq.contentに入ってくるため、hoge以前の文字列を削除
        #message = re.sub('\<.+\> ', '', req.content)

        # NOTE:
        # サーバに所属するメンバーを管理するテーブルの作成、および、メンバーの追加
#        if re.match("^init$", message):
#            pridb = PriDb.PriDb()
#            pridb.create_server_table(req.server.id)
#
#            for m in req.server.members:
#                pridb.insert_member(
#                    req.server.id,
#                    m.id,
#                    m.name,
#                    m.joined_at.strftime("%Y/%m/%d %H:%M:%S")
#                )

        cm = Common.Common()
        ws = cm.get_gsfile('clan_members')
        df = cm.create_gsdf(ws)

        # シートclan_membersの内容を初期化（クリア）
        col_lastnum = len(df.columns)
        row_lastnum = len(df.index)

        cell_list = ws.range('A2:'+cm.toAlpha(col_lastnum)+str(row_lastnum + 1))
        for cell in cell_list:
            cell.value = ''

        ws.update_cells(cell_list)
        time.sleep(5)
        df_col = df.columns
        del df

        # 新たにサーバ上にいるメンバーを格納したDataFrameを作成
        df = pd.DataFrame(index=[], columns=df_col)
        for m in req.server.members:
            s = pd.Series([m.id, m.name], index=df_col)
            df = df.append(s, ignore_index=True)

        col_lastnum = len(df.columns)
        row_lastnum = len(df.index)

        cell_list = ws.range('A2:'+cm.toAlpha(col_lastnum)+str(row_lastnum + 1))
        for cell in cell_list:
            val = df.iloc[cell.row - 2][cell.col - 1]
            cell.value = val

        ws.update_cells(cell_list)



if __name__ == "__main__":
    ma = ManageActions()
    ma.check_and_action('dummy')
