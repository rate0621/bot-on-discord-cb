import os, re
from datetime import datetime, timedelta, timezone
import discord

import common_lib.PriDb as PriDb

class ManageActions:
    def __init__(self):
        pass



    def check_and_action(self, req):


        # NOTE:
        # <@478542546537283594> hoge という形でreq.contentに入ってくるため、hoge以前の文字列を削除
        message = re.sub('\<.+\> ', '', req.content)

        # NOTE:
        # サーバに所属するメンバーを管理するテーブルの作成、および、メンバーの追加
        if re.match("^init$", message):
            pridb = PriDb.PriDb()
            pridb.create_server_table(req.server.id)

            for m in req.server.members:
                pridb.insert_member(
                    req.server.id,
                    m.id,
                    m.name,
                    m.joined_at.strftime("%Y/%m/%d %H:%M:%S")
                )

