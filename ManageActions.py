import os, re
from datetime import datetime, timedelta, timezone
import discord
import pandas as pd
import MySQLdb
from contextlib import closing

import time

import common_lib.PriDb  as PriDb
import common_lib.Common as Common

class ManageActions:
    def __init__(self):
        pass



    def check_and_action(self, req):

        message = re.sub('\<.+\> ', '', req.content)
        # サーバに所属するメンバーを管理するテーブルの作成、および、メンバーの追加
        if re.match("^init$", message):

            args = {
                "host"    : os.getenv("DB_HOST", ""),
                "user"    : os.getenv("DB_USER", ""),
                "passwd"  : os.getenv("DB_PASS", ""),
                "db"      : os.getenv("DB_NAME", ""),
                "charset" : os.getenv("DB_CHARSET", ""),
            }
            
            with closing(MySQLdb.connect(**args)) as conn:
                cur = conn.cursor()
                cur.execute("TRUNCATE TABLE clan_members")

                for m in req.server.members:
                    is_member = 0
                    for r in m.roles:
                        # TODO:環境変数からとってくるようにする
                        if r.id == '631094092050202626':
                            is_member = 1

                    cur.execute("INSERT INTO clan_members (user_id, user_name, is_member) VALUES (%s, %s, %s)", (m.id, m.name, is_member))

                conn.commit()



if __name__ == "__main__":
    ma = ManageActions()
    ma.check_and_action('dummy')
