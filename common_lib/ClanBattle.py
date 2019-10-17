import os, sys
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import calendar
import MySQLdb
from contextlib import closing

here = os.path.join( os.path.dirname(os.path.abspath(__file__)))
sys.path.append(here)

class ClanBattle():
    def __init__(self):

        args = {
            "host"   : os.getenv("DB_HOST", ""),
            "user"   : os.getenv("DB_USER", ""),
            "passwd" : os.getenv("DB_PASS", ""),
            "db"     : os.getenv("DB_NAME", ""),
            "charset" : os.getenv("DB_CHARSET", ""),
        }

        self.conn = MySQLdb.connect(**args)


    def get_today_from_and_to(self):
        today = datetime.now() - timedelta(hours=5)
        tomorrow = today + timedelta(days=1)
        f = today.strftime("%Y/%m/%d 05:00:00")
        t = tomorrow.strftime("%Y/%m/%d 04:59:00")
        return f, t

    def get_month_from_and_to(self):
        this_month = date.today()
        f = date(this_month.year, this_month.month, 1)
        t = date(this_month.year, this_month.month+1, 1) - timedelta(days=1)

        return f, t


    def get_bosses(self):
        '''
        開催月のボス情報をマスタから取得
        '''
        cur = self.conn.cursor()
        f, t = self.get_month_from_and_to()

        cur.execute("SELECT boss_number, boss_name, target FROM boss WHERE event_month BETWEEN %s AND %s", (f, t))
        boss_list = []
        for row in cur.fetchall():
            boss_list.append({'boss_number': row[0], 'boss_name': row[1], 'target': row[2]})

        return boss_list


    def boss_reserve(self, user_id, boss_num):
        _datetime = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        if self.reserved_check(user_id, boss_num):
            print ('すでに予約済みです')
        else:
            print ('予約します')

            cur = self.conn.cursor()
            cur.execute("INSERT INTO boss_reserve (reserved_at, user_id, boss_number, is_attack, is_cancel) VALUES (%s, %s, %s, %s, 0)", (_datetime, user_id, boss_num, 0))

            self.conn.commit()
            print ('予約完了')


    def reserved_check(self, user_id, boss_num=None):
        cur = self.conn.cursor()

        if boss_num is None:
            cur.execute("SELECT * FROM boss_reserve WHERE user_id = %s AND is_attack = 0 AND is_cancel = 0", (user_id,))
        else:
            boss_num = int(boss_num)
            cur.execute("SELECT * FROM boss_reserve WHERE user_id = %s AND boss_number = %s AND is_attack = 0 AND is_cancel = 0", (user_id, boss_num))

        if cur.rowcount > 0:
            return True
        else:
            return False

    def reserved_clear(self, user_id, boss_num):
        '''
        予約していたユーザが凸し終わったときの処理
        '''
        cur = self.conn.cursor()
        cur.execute("UPDATE boss_reserve SET is_attack = 1 WHERE user_id = %s AND boss_number = %s AND is_cancel = 0", (user_id, boss_num))
        self.conn.commit()


    def reserved_cancel(self, user_id, boss_num=None):
        '''
        ユーザが凸キャンセルしたときの処理
        '''
        cur = self.conn.cursor()

        if boss_num is None:
            cur.execute("UPDATE boss_reserve SET is_cancel = 1 WHERE user_id = %s  AND is_attack = 0", (user_id,))
        else:
            cur.execute("UPDATE boss_reserve SET is_cancel = 1 WHERE user_id = %s AND boss_number = %s AND is_attack = 0", (user_id, boss_num))

        self.conn.commit()

    def get_reserved_users(self, boss_num):
        cur = self.conn.cursor()
        cur.execute("SELECT br.user_id, cm.user_name FROM boss_reserve br INNER JOIN clan_members cm ON br.user_id = cm.user_id WHERE boss_number = %s AND is_attack = 0 AND is_cancel = 0", (boss_num,))

        l = []
        rows = cur.fetchall()
        for row in rows:
            l.append({'user_id': row[0], 'user_name': row[1]})

        return l


    def get_all_reserved_users(self):
        boss_array = self.get_bosses()

        dic = {}
        for boss in boss_array:
            dic.setdefault(boss['boss_number'], [])
            for u in self.get_reserved_users(boss['boss_number']):
                dic.setdefault(boss['boss_number'], []).append(u['user_name'])

        return dic


    def get_current_boss(self):
        cur = self.conn.cursor()
        cur.execute("SELECT c.boss_number, b.boss_name, c.hit_point FROM current_boss c INNER JOIN boss b ON c.boss_number = b.boss_number")

        r = cur.fetchone()
        d = {'boss_number': r[0], 'boss_name': r[1], 'hit_point': r[2]}
        return d

    def attack(self, user_id):
        '''
        凸の宣言
        '''
        attack_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        cb_dict = self.get_current_boss()

        cur = self.conn.cursor()
        cur.execute("INSERT INTO attack_log (attack_time, user_id, boss_number, damage, score, is_carry_over) VALUES (%s, %s, %s, 0, 0, 0)", (attack_time, user_id, cb_dict['boss_number']))

        self.conn.commit()


    def attack_check(self, user_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM attack_log WHERE user_id = %s AND damage = 0", (user_id,))

        if cur.rowcount > 0:
            return True
        else:
            return False


    def attack_cancel(self, user_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM attack_log WHERE user_id = %s AND damage = 0", (user_id,))
        self.conn.commit()


    def finish_attack(self, user_id, damage, is_carry_over):
        '''
        ダメージ情報を更新
        '''
        cur = self.conn.cursor()
        cur.execute("UPDATE attack_log SET damage = %s, is_carry_over = %s WHERE user_id = %s AND damage = 0", (damage, is_carry_over, user_id))
        self.conn.commit()



    def update_current_boss(self, damage):
        '''
        current_bossの情報を更新する。
        もし、撃破した場合は、その返り値を返す。
        '''
        is_carry_over = 0
        cb_dict = self.get_current_boss()
        cur = self.conn.cursor()

        # ボスのHPが０かマイナスになったかチェック。やり方については以下を参考
        # https://teratail.com/questions/151694
        if ((cb_dict['hit_point'] - damage > 0) - (cb_dict['hit_point'] - damage < 0)) <= 0:
            self.lotate_boss()
            is_carry_over = 1
        else:
            cur.execute("UPDATE current_boss SET hit_point = hit_point - %s", (damage,))
            self.conn.commit()
            

        return is_carry_over


    def get_attack_count(self):
        f, t = self.get_today_from_and_to()

        cur = self.conn.cursor()
        cur.execute("SELECT * FROM attack_log WHERE damage > 0 AND is_carry_over = 0 AND attack_time BETWEEN %s AND %s", (f, t))
        return cur.rowcount



    def get_carry_over_users(self):
        cur = self.conn.cursor()
        cur.execute("SELECT cm.user_name, co.boss_number, co.time FROM carry_over co INNER JOIN clan_members cm ON co.user_id = cm.user_id")

        rows = cur.fetchall()

        dic = {}
        for row in rows:
            dic.setdefault(row[0], {'attacked_boss': row[1], 'time': row[2]})

        return dic

    def check_carry_over(self, user_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM carry_over WHERE user_id = %s AND is_attack = 0", (user_id,))

        if cur.rowcount > 0:
            return True
        else:
            return False


    def finish_carry_over(self, user_id):
        cur = self.conn.cursor()
        cur.execute("UPDATE carry_over SET is_attack = 1 WHERE user_id = %s AND is_attack = 0", (user_id,))
        self.conn.commit()


    def get_remaining_atc_count(self):
        f, t = self.get_today_from_and_to()

        cur = self.conn.cursor()
        cur.execute("SELECT * FROM attack_log WHERE attack_time BETWEEN %s AND %s AND is_carry_over = 0", (f, t))

        return 90 - cur.rowcount


    def lotate_boss(self):
        cb_dict = self.get_current_boss()

        cb_dict['boss_number'] += 1

        if cb_dict['boss_number'] > 5:
            cb_dict['boss_number'] = 1

        cur = self.conn.cursor()
        cur.execute("SELECT boss_number, max_hit_point FROM boss WHERE boss_number = %s", (cb_dict['boss_number'],))

        boss_number, max_hit_point = cur.fetchone()

        cur.execute("UPDATE current_boss SET boss_number = %s, hit_point = %s", (boss_number, max_hit_point))
        self.conn.commit()
        

    def insert_carry_over(self, user_id, boss_num, time):
        print ('持ち越し入れます')
        _datetime = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        cur = self.conn.cursor()
        cur.execute("INSERT INTO carry_over (carried_at, user_id, boss_number, time, is_attack) VALUES (%s, %s, %s, %s, 0)", (_datetime, user_id, boss_num, time))

        self.conn.commit()

    def get_today_members_attack_count(self):
        f, t = self.get_today_from_and_to()
        cur = self.conn.cursor()
        cur.execute(" \
            SELECT \
                cm.user_id, \
                cm.user_name, \
                IFNULL(ac.attack_count, 0) AS attack_count \
            FROM \
                clan_members cm \
            LEFT JOIN( \
                SELECT \
                    user_id, \
                    COUNT(user_id) attack_count \
                FROM \
                    attack_log \
                WHERE \
                    is_carry_over = 0 \
                    AND \
                    attack_time BETWEEN %s AND %s \
                GROUP BY \
                    user_id \
            ) ac \
            ON cm.user_id = ac.user_id \
            WHERE \
                cm.is_member = 1 \
        ", (f, t))

        rows = cur.fetchall()
        dic = {}
        for row in rows:
            dic.setdefault(row[0], {'user_name': row[1], 'attack_count': row[2]})
        
        return dic

    def get_three_attack_members(self, ma_dic):
        m_array = []
        for user_id in ma_dic:
            if ma_dic[user_id]['attack_count'] == 3:
                m_array.append(ma_dic[user_id]['user_name'])

        return m_array

    def get_not_three_attack_members(self, ma_dic):
        m_array = []
        for user_id in ma_dic:
            if ma_dic[user_id]['attack_count'] < 3:
                m_array.append(ma_dic[user_id]['user_name'] + '  残り:' + str(ma_dic[user_id]['attack_count']))

        return m_array


if __name__ == '__main__':
    cb = ClanBattle()
    #user_id = '474761974832431148'
    #user_id =  '478542546537283594'
    user_id =  '523048909833109504'
    boss_num = 2
    time = 50
    damage = 5000000

    #print (cb.get_bosses())
    member_attack_dic    = cb.get_today_members_attack_count()
    three_attack_members = cb.get_three_attack_members(member_attack_dic)
    not_three_attack_members = cb.get_not_three_attack_members(member_attack_dic)
    print (three_attack_members)
    print (not_three_attack_members)
 
    #cb.boss_reserve(user_id, 5)
    #print (cb.reserved_check(user_id))
#    if cb.reserved_check(user_id):
#        print ('reserved')
#        cb.reserved_clear(user_id)
#    else:
#        print ('no reserve')

    #print (cb.get_all_reserved_users())

    #print (cb.get_current_boss())

#    if not cb.attack_check(user_id):
#        cb.attack(user_id)
#    #cb.attack_cancel(user_id)
#
#    is_carry_over = cb.update_current_boss(damage)
#    cb.finish_attack(user_id, damage, is_carry_over)

    #print (cb.get_attack_count())
    #print (cb.get_carry_over_users())


    #print (cb.get_remaining_atc_count())

    #cb.insert_carry_over(user_id, boss_num, time)
    #cb.get_carry_over_users()


