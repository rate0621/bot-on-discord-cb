import os, sys
import sqlite3
#import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import calendar
import MySQLdb
import math
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

        self.BOSSHP_MASTER = {
            'LEVEL1': {
                1: 600,
                2: 800,
                3: 1000,
                4: 1200,
                5: 1500,
            },
            'LEVEL2': {
                1: 600,
                2: 800,
                3: 1000,
                4: 1200,
                5: 1500,
            },
            'LEVEL3': {
                1: 1200,
                2: 1400,
                3: 1700,
                4: 1900,
                5: 2200,
            },
            'LEVEL4': {
                1: 2200,
                2: 2300,
                3: 2700,
                4: 2900,
                5: 3100,
            },
            'LEVEL5': {
                1: 14500,
                2: 15000,
                3: 17500,
                4: 19500,
                5: 21000,
            },
        }


        self.conn = MySQLdb.connect(**args)


    def get_today_from_and_to(self):
        today = datetime.now() - timedelta(hours=5)
        tomorrow = today + timedelta(days=1)
        f = today.strftime("%Y/%m/%d 05:00:00")
        t = tomorrow.strftime("%Y/%m/%d 04:59:00")
        return f, t

    def get_yesterday_from_and_to(self):
        f = datetime.now() - timedelta(hours=5) - timedelta(days=1)
        t = f + timedelta(days=1)
        f = f.strftime("%Y/%m/%d 05:00:00")
        t = t.strftime("%Y/%m/%d 04:59:00")
        return f, t

    def get_month_from_and_to(self):
        this_month = date.today()
        if this_month.month == 12:
            f = date(this_month.year, this_month.month, 1)
            t = date(this_month.year, this_month.month, 31)
        else:
            f = date(this_month.year, this_month.month, 1)
            t = date(this_month.year, this_month.month+1, 1) - timedelta(days=1)

        return f, t


    def get_bosses(self):
        '''
        開催月のボス情報をマスタから取得
        '''
        cur = self.conn.cursor()
        #f, t = self.get_month_from_and_to()

        cur.execute("SELECT id, boss_name, target FROM boss")
        boss_list = []
        for row in cur.fetchall():
            boss_list.append({'id': row[0], 'boss_name': row[1], 'target': row[2]})

        return boss_list


    def boss_reserve(self, user_id, boss_num, option=None):
        _datetime = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        if self.reserved_check(user_id, boss_num):
            print ('すでに予約済みです')
        else:
            print ('予約します')

            cur = self.conn.cursor()
            cur.execute("INSERT INTO boss_reserve (reserved_at, discord_user_id, boss_id, is_attack, is_cancel) VALUES (%s, %s, %s, %s, 0)", (_datetime, user_id, boss_num, 0))

            if not option is None:
                cur.execute("INSERT INTO boss_reserve_option (boss_reserve_id, option_text) VALUES (%s, %s)", (cur.lastrowid, option))

            self.conn.commit()
            print ('予約完了')


    def reserved_check(self, user_id, boss_num=None):
        cur = self.conn.cursor()

        if boss_num is None:
            cur.execute("SELECT * FROM boss_reserve WHERE discord_user_id = %s AND is_attack = 0 AND is_cancel = 0", (user_id,))
        else:
            boss_num = int(boss_num)
            cur.execute("SELECT * FROM boss_reserve WHERE discord_user_id = %s AND boss_id = %s AND is_attack = 0 AND is_cancel = 0", (user_id, boss_num))

        if cur.rowcount > 0:
            return True
        else:
            return False

    def reserved_clear(self, user_id, boss_num):
        '''
        予約していたユーザが凸し終わったときの処理
        '''
        cur = self.conn.cursor()
        cur.execute("UPDATE boss_reserve SET is_attack = 1 WHERE discord_user_id = %s AND boss_id = %s AND is_cancel = 0", (user_id, boss_num))
        self.conn.commit()


    def reserved_cancel(self, user_id, boss_num=None):
        '''
        ユーザが凸キャンセルしたときの処理
        '''
        cur = self.conn.cursor()

        if boss_num is None:
            cur.execute("UPDATE boss_reserve SET is_cancel = 1 WHERE discord_user_id = %s  AND is_attack = 0", (user_id,))
        else:
            cur.execute("UPDATE boss_reserve SET is_cancel = 1 WHERE discord_user_id = %s AND boss_id = %s AND is_attack = 0", (user_id, boss_num))

        self.conn.commit()

    def get_reserved_users(self, boss_num):
        cur = self.conn.cursor()
        cur.execute("SELECT br.discord_user_id, cm.member_name, bro.option_text FROM boss_reserve br INNER JOIN clan_member cm ON br.discord_user_id = cm.discord_user_id  LEFT JOIN boss_reserve_option bro ON br.id = bro.boss_reserve_id WHERE boss_id = %s AND is_attack = 0 AND is_cancel = 0", (boss_num,))

        l = []
        rows = cur.fetchall()
        for row in rows:
            if row[2] is None:
                l.append({'discord_user_id': row[0], 'member_name': row[1], 'option': ''})
            else:
                l.append({'discord_user_id': row[0], 'member_name': row[1], 'option': row[2]})

        return l


    def get_all_reserved_users(self):
        boss_array = self.get_bosses()

        dic = {}
        for boss in boss_array:
            dic.setdefault(boss['id'], [])
            for u in self.get_reserved_users(boss['id']):
                #dic.setdefault(boss['id'], []).append(u['member_name'])
                #dic.setdefault(boss['id'], {'member_name': u['member_name'], 'option': u['option']})
                dic[boss['id']].append({'member_name': u['member_name'], 'option': u['option']})

        return dic


    def get_current_boss(self):
        cur = self.conn.cursor()
        cur.execute("SELECT c.boss_id, b.boss_name, c.hit_point, c.loop_count FROM current_boss c INNER JOIN boss b ON c.boss_id = b.id")

        r = cur.fetchone()
        d = {'boss_id': r[0], 'boss_name': r[1], 'hit_point': r[2], 'loop_count': r[3]}
        return d

    def get_boss_status(self):
        cur = self.conn.cursor()
        cur.execute("SELECT bs.boss_id, b.boss_name, bs.hit_point, bs.loop_count FROM boss_status bs INNER JOIN boss b ON bs.boss_id = b.id")

        rows = cur.fetchall()

        dic = {}
        for row in rows:
            level = 1
            if row[3] <= 3:
                level = 1
            elif row[3] <= 10:
                level = 2
            elif row[3] <= 31:
                level = 3
            elif row[3] <= 41:
                level = 4
            else:
                level = 5
                
            dic.setdefault(row[0], {'boss_name': row[1], 'hit_point': row[2], 'loop_count': row[3], 'level': level})

        max_level = max([int(i["loop_count"]) for i in dic.values()])
        return dic

    def attack(self, user_id, boss_num, is_carry_over=None):
        '''
        凸の宣言
        '''
        attack_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        #cb_dict = self.get_current_boss()
        bs_dict = self.get_boss_status()

        cur = self.conn.cursor()
        if is_carry_over:
            cur.execute("INSERT INTO attack_log (attack_time, discord_user_id, boss_id, damage, score, is_carry_over, loop_count, attack_weight) VALUES (%s, %s, %s, 0, 0, 0, %s, %s)", (attack_time, user_id, boss_num, bs_dict[int(boss_num)]['loop_count'], 0.5))
        else:
            cur.execute("INSERT INTO attack_log (attack_time, discord_user_id, boss_id, damage, score, is_carry_over, loop_count, attack_weight) VALUES (%s, %s, %s, 0, 0, 0, %s, %s)", (attack_time, user_id, boss_num, bs_dict[int(boss_num)]['loop_count'], 1))

        self.conn.commit()


    def attack_check(self, user_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM attack_log WHERE discord_user_id = %s AND damage = 0", (user_id,))

        if cur.rowcount > 0:
            return True
        else:
            return False


    def attack_cancel(self, user_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM attack_log WHERE discord_user_id = %s AND damage = 0", (user_id,))
        self.conn.commit()

    def get_attacked_boss_num(self, user_id):
        f, t = self.get_today_from_and_to()
        cur = self.conn.cursor()
        cur.execute("SELECT boss_id FROM attack_log WHERE discord_user_id = %s AND attack_time BETWEEN %s AND %s ORDER BY attack_time DESC LIMIT 1", (user_id, f, t))
        boss_num = cur.fetchone()[0]
        return boss_num
        

    def finish_attack(self, user_id, damage, is_carry_over):
        '''
        ダメージ情報を更新
        '''

        f, t = self.get_today_from_and_to()

        cur = self.conn.cursor()
        cur.execute("SELECT attack_weight FROM attack_log WHERE discord_user_id = %s AND attack_time BETWEEN %s AND %s ORDER BY attack_time DESC LIMIT 1", (user_id, f, t))
        attack_weight = cur.fetchone()

        # attack_logのweightが0.5だった場合、持ち越しでの凸なので、carry_overテーブルの内容を更新する
        if attack_weight[0] == 0.5:
            cur.execute("UPDATE carry_over SET is_attack = 1 WHERE discord_user_id = %s AND carried_at BETWEEN %s AND %s ORDER BY carried_at DESC LIMIT 1", (user_id, f, t))


        if is_carry_over:
            cur.execute("UPDATE attack_log SET damage = %s, is_carry_over = %s, attack_weight = 0.5 WHERE discord_user_id = %s AND damage = 0", (damage, is_carry_over, user_id))
        else:
            cur.execute("UPDATE attack_log SET damage = %s, is_carry_over = %s WHERE discord_user_id = %s AND damage = 0", (damage, is_carry_over, user_id))

        self.conn.commit()



#    def update_current_boss(self, damage):
#        '''
#        current_bossの情報を更新する。
#        もし、撃破した場合は、その返り値を返す。
#        また、5ボスを討伐（一周）したか否かのフラグも返す。
#        '''
#        is_carry_over = 0
#        is_round      = False
#        cb_dict = self.get_current_boss()
#        cur = self.conn.cursor()
#
#        # ボスのHPが０かマイナスになったかチェック。やり方については以下を参考
#        # https://teratail.com/questions/151694
#        if ((cb_dict['hit_point'] - damage > 0) - (cb_dict['hit_point'] - damage < 0)) <= 0:
#            is_round      = self.lotate_boss()
#            is_carry_over = 1
#        else:
#            cur.execute("UPDATE current_boss SET hit_point = hit_point - %s", (damage,))
#            self.conn.commit()
#
#        return is_carry_over, is_round

    def update_boss_status(self, damage, boss_num):
        is_carry_over = 0
        is_round      = False
        bs_dict = self.get_boss_status()
        cur = self.conn.cursor()
        
        # ボスのHPが０かマイナスになったかチェック。やり方については以下を参考
        # https://teratail.com/questions/151694
        if ((bs_dict[int(boss_num)]['hit_point'] - damage > 0) - (bs_dict[int(boss_num)]['hit_point'] - damage < 0)) <= 0:
            self.increment_boss_loop_count(boss_num)
            is_carry_over = 1
        else:
            cur.execute("UPDATE boss_status SET hit_point = hit_point - %s WHERE boss_id = %s", (damage, boss_num))
            self.conn.commit()

        return is_carry_over


    def get_attack_count(self):
        f, t = self.get_today_from_and_to()

        cur = self.conn.cursor()
        cur.execute("SELECT SUM(attack_weight) FROM attack_log WHERE damage > 0 AND attack_time BETWEEN %s AND %s", (f, t))

        val = cur.fetchone()[0]
        if val is None:
            attack_count = 0
        else:
            attack_count = val

        return attack_count



    def get_carry_over_users(self):
        f, t = self.get_today_from_and_to()

        cur = self.conn.cursor()
        cur.execute("SELECT cm.member_name, co.boss_id, co.time FROM carry_over co INNER JOIN clan_member cm ON co.discord_user_id = cm.discord_user_id WHERE co.is_attack = 0 AND carried_at BETWEEN %s AND %s", (f, t))

        rows = cur.fetchall()

        dic = {}
        for row in rows:
            dic.setdefault(row[0], [])
            dic[row[0]].append({'attacked_boss': row[1], 'time': row[2]})

        return dic

    def check_carry_over(self, user_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM carry_over WHERE discord_user_id = %s AND is_attack = 0", (user_id,))

        if cur.rowcount > 0:
            return True
        else:
            return False


    def finish_carry_over(self, user_id):
        cur = self.conn.cursor()
        cur.execute("UPDATE carry_over SET is_attack = 1 WHERE discord_user_id = %s AND is_attack = 0", (user_id,))
        self.conn.commit()


    def get_remaining_atc_count(self):
        attack_count = self.get_attack_count()

        return 90 - attack_count


    def lotate_boss(self, boss_num):
#        cb_dict = self.get_current_boss()
#
#        cb_dict['boss_id'] += 1
#
#        is_round = False
#        if cb_dict['boss_id'] > 5:
#            cb_dict['boss_id']     = 1
#            cb_dict['loop_count'] += 1
#            is_round = True
#
        cur = self.conn.cursor()
#        cur.execute("SELECT id, max_hit_point FROM boss WHERE id = %s", (cb_dict['boss_id'],))
#
#        boss_number, max_hit_point = cur.fetchone()

        cur.execute("UPDATE boss_status SET loop_count = loop_count + 1 WHERE boss_id = %s", (boss_num,))
        self.conn.commit()

#        return is_round

    def increment_boss_loop_count(self, boss_num):
        boss_num = int(boss_num)
        bs_dict = self.get_boss_status()
        level   = self.get_boss_level(bs_dict[boss_num]['loop_count'])
        level_key = 'LEVEL' + str(level)
        self.BOSSHP_MASTER[level_key][boss_num]

        #bs_dict[int(boss_num)]['loop_count'] += 1

        cur = self.conn.cursor()
#        cur.execute("SELECT id, max_hit_point FROM boss WHERE id = %s", (boss_num,))
#        boss_number, max_hit_point = cur.fetchone()
        
        cur.execute("UPDATE boss_status SET hit_point = %s, loop_count = loop_count + 1 WHERE boss_id = %s", (self.BOSSHP_MASTER[level_key][boss_num] * 10000, boss_num))
        self.conn.commit()
        

    def get_around_count(self):
        cb_dict = self.get_current_boss()
        f, t = self.get_month_from_and_to()
        target_loop_count = cb_dict['loop_count'] - 1

        cur = self.conn.cursor()
        cur.execute("SELECT SUM(attack_weight) FROM attack_log WHERE attack_time BETWEEN %s AND %s AND loop_count = %s GROUP BY loop_count", (f, t, target_loop_count))

        around_attack_count = cur.fetchone()[0]
        return around_attack_count

    def get_all_around_count(self):
        f, t = self.get_month_from_and_to()

        cur = self.conn.cursor()
        cur.execute("SELECT loop_count, SUM(attack_weight) FROM attack_log WHERE attack_time BETWEEN %s AND %s GROUP BY loop_count", (f, t))

        rows = cur.fetchall()
        dic = {}
        for row in rows:
            dic.setdefault(row[0], {'attack_count': row[1]})

        return dic


    def insert_carry_over(self, user_id, boss_num, time):
        print ('持ち越し入れます')
        _datetime = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        cur = self.conn.cursor()
        cur.execute("INSERT INTO carry_over (carried_at, discord_user_id, boss_id, time, is_attack) VALUES (%s, %s, %s, %s, 0)", (_datetime, user_id, boss_num, time))

        self.conn.commit()

    def update_carry_over(self, user_id, time):
        print ('持ち越し時間更新します')
        f, t = self.get_today_from_and_to()
        cur = self.conn.cursor()
        cur.execute("UPDATE carry_over SET time = %s WHERE carried_at BETWEEN %s AND %s AND discord_user_id = %s AND time = 0", (time, f, t, user_id))

        self.conn.commit()

    def get_today_members_attack_count(self):
        f, t = self.get_today_from_and_to()
        cur = self.conn.cursor()
        cur.execute(" \
            SELECT \
                cm.discord_user_id, \
                cm.member_name, \
                IFNULL(ac.attack_count, 0) AS attack_count \
            FROM \
                clan_member cm \
            LEFT JOIN( \
                SELECT \
                    discord_user_id, \
                    SUM(attack_weight) attack_count \
                FROM \
                    attack_log \
                WHERE \
                    attack_time BETWEEN %s AND %s \
                GROUP BY \
                    discord_user_id \
            ) ac \
            ON cm.discord_user_id = ac.discord_user_id \
            WHERE \
                cm.is_member = 1 \
        ", (f, t))

        rows = cur.fetchall()
        dic = {}
        for row in rows:
            dic.setdefault(row[0], {'member_name': row[1], 'attack_count': row[2]})
        
        return dic

    def get_yesterday_members_attack_count(self):
        f, t = self.get_yesterday_from_and_to()
        cur = self.conn.cursor()
        cur.execute(" \
            SELECT \
                cm.discord_user_id, \
                cm.member_name, \
                IFNULL(ac.attack_count, 0) AS attack_count \
            FROM \
                clan_member cm \
            LEFT JOIN( \
                SELECT \
                    discord_user_id, \
                    SUM(attack_weight) attack_count \
                FROM \
                    attack_log \
                WHERE \
                    attack_time BETWEEN %s AND %s \
                GROUP BY \
                    discord_user_id \
            ) ac \
            ON cm.discord_user_id = ac.discord_user_id \
            WHERE \
                cm.is_member = 1 \
        ", (f, t))

        rows = cur.fetchall()
        dic = {}
        for row in rows:
            dic.setdefault(row[0], {'member_name': row[1], 'attack_count': row[2]})
        
        return dic

    def get_three_attack_members(self, ma_dic):
        m_array = []
        for user_id in ma_dic:
            if ma_dic[user_id]['attack_count'] >= 3:
                m_array.append(ma_dic[user_id]['member_name'])

        return m_array

    def get_not_three_attack_members(self, ma_dic):
        m_array = []
        for user_id in ma_dic:
            if ma_dic[user_id]['attack_count'] < 3:
                m_array.append(ma_dic[user_id]['member_name'] + '  残り:' + str(3 - ma_dic[user_id]['attack_count']))

        return m_array

    def get_carry_time(self, damages):
        time      = 0
        hit_point = self.get_current_boss()['hit_point']
        for d in damages:
            d = d * 10000
            if hit_point > d:
                hit_point = hit_point - d
            else:
                time = math.ceil(90 - (hit_point * 90 / d - 20))
                break

        return time

    def get_damage_memo(self, channel_id):
        cur = self.conn.cursor()
        cur.execute("SELECT dm.id, dm.message_id, dm.damage, cm.member_name, dm.said_time FROM damage_memo dm INNER JOIN clan_member cm ON dm.discord_user_id = cm.discord_user_id WHERE dm.id IN ( SELECT MAX(id) FROM damage_memo WHERE channel_id = %s GROUP BY message_id, discord_user_id)", (channel_id, ))

        l = []
        rows = cur.fetchall()
        for row in rows:
            l.append({'id': row[0], 'message_id': row[1], 'damage': row[2], 'member_name': row[3], 'said_time': row[4]})

        return l

#        if cur.rowcount > 0:
#            r = cur.fetchone()
#            d = {'message_id': r[0], 'damage': r[1], 'discord_user_id': r[2]}
#            return d
#        else:
#            return None


    def get_damage_memo_message_id(self, channel_id):
        cur = self.conn.cursor()
        cur.execute("SELECT message_id FROM damage_memo WHERE channel_id = %s LIMIT 1", (channel_id,))

        r = cur.fetchone()
        return r[0] if r is not None else 0


    def is_damage_memo_empty(self, channel_id):
        cur = self.conn.cursor()
        cur.execute("SELECT message_id, damage, discord_user_id FROM damage_memo WHERE channel_id = %s", (channel_id,))
        return True if cur.rowcount == 0 else False

    def insert_damage_memo(self, message_id, channel_id, user_id=None, damage=0):
        said_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        cur = self.conn.cursor()
        cur.execute("INSERT INTO damage_memo (message_id, discord_user_id, damage, said_time, channel_id) VALUES (%s, %s, %s, %s, %s)", (message_id, user_id, damage, said_time, channel_id))
        self.conn.commit()

    def delete_damage_memo(self, channel_id):
        cur = self.conn.cursor()
        print (channel_id)
        cur.execute("DELETE FROM damage_memo WHERE channel_id = %s", (channel_id,))
        self.conn.commit()

#    def delete_damage_memo(self, discord_user_id):
#        cur = self.conn.cursor()
#        cur.execute("DELETE FROM damage_memo WHERE discord_user_id = %s", (discord_user_id,))
#        self.conn.commit()

    def get_member_id_from_damege_memo_id(self, damage_memo_id):
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT member_id FROM damage_memo WHERE id = %s", (damage_memo_id,))
        r = cur.fetchone()
        return r[0] if r is not None else 0

#    def update_boss_hp(self, level):
#        level_key = 'LEVEL' + str(level)
#
#        cur = self.conn.cursor()
#        print ('ボスのマスタを更新')
#        for boss_num in self.BOSSHP_MASTER[level_key]:
#            cur.execute("UPDATE boss SET max_hit_point = %s WHERE id = %s", (self.BOSSHP_MASTER[level_key][boss_num] * 10000, boss_num))
#            self.conn.commit()
#
#        # NOTE: current_bossはマスタが更新される前に更新されてしまっているため、このタイミングでマスタのHPをあわせる
#        print ('current_bossの内容を更新')
#        cur.execute("UPDATE current_boss SET hit_point = %s WHERE id = 1", (self.BOSSHP_MASTER[level_key][1] * 10000,))
#        self.conn.commit()
        
    def update_boss_hp(self, boss_num):
        boss_num = int(boss_num)
        bs_dict = self.get_boss_status()
        level   = self.get_boss_level(bs_dict[boss_num]['loop_count'])
        level_key = 'LEVEL' + str(level)

        print ('boss_statusを更新')
        cur = self.conn.cursor()
        cur.execute("UPDATE boss_status SET hit_point = %s WHERE boss_id = %s", (self.BOSSHP_MASTER[level_key][boss_num] * 10000, boss_num))
        self.conn.commit()

#        for boss_num in self.BOSSHP_MASTER[level_key]:
#            cur.execute("UPDATE boss SET max_hit_point = %s WHERE id = %s", (self.BOSSHP_MASTER[level_key][boss_num] * 10000, boss_num))
#            self.conn.commit()
#
#        # NOTE: current_bossはマスタが更新される前に更新されてしまっているため、このタイミングでマスタのHPをあわせる
#        print ('current_bossの内容を更新')
#        cur.execute("UPDATE current_boss SET hit_point = %s WHERE id = 1", (self.BOSSHP_MASTER[level_key][1] * 10000,))
#        self.conn.commit()
        

    def get_boss_level(self, loop_count):
        if loop_count >= 1 and loop_count <= 3:
            return 1
        elif loop_count >= 4 and loop_count <= 10:
            return 2
        elif loop_count >= 11 and loop_count <= 30:
            return 3
        elif loop_count >= 31 and loop_count <= 38:
            return 4
        elif loop_count >= 39:
            return 5
        else:
            return 0


    def change_boss_hp(self, boss_num, hp):
        cur = self.conn.cursor()
        cur.execute("UPDATE boss_status SET hit_point = %s WHERE boss_id = %s", (hp, boss_num))
        self.conn.commit()
        
    def change_loop_count(self, boss_num, loop_count):
        cur = self.conn.cursor()
        cur.execute("UPDATE boss_status SET loop_count = %s WHERE boss_id = %s", (loop_count, boss_num))
        self.conn.commit()
        


if __name__ == '__main__':
    cb = ClanBattle()
    
    user_id = '474761974832431148'
    #user_id =  '478542546537283594'
    #user_id =  '523048909833109504'
    boss_num = 2
    time = 50
    damage = 15000000

#    print (cb.get_bosses())

### 予約確認 ###
#    cb.get_boss_status()
###

### 持ち越し確認
#    cb.get_carry_over_users()
###

### ボスHP更新 ###
    cb.update_boss_hp(5)
###

### メンバー全員の凸数確認 ###
#    member_attack_dic    = cb.get_today_members_attack_count()
#    member_attack_dic    = cb.get_yesterday_members_attack_count()
#    three_attack_members = cb.get_three_attack_members(member_attack_dic)
#    not_three_attack_members = cb.get_not_three_attack_members(member_attack_dic)
#    print (three_attack_members)
#    print ('====')
#    print (not_three_attack_members)
############
 
#    cb.boss_reserve(user_id, 5)
#    print (cb.reserved_check(user_id))


#    if cb.reserved_check(user_id):
#        print ('reserved')
#        cb.reserved_clear(user_id, 5)
#    else:
#        print ('no reserve')

#    print (cb.get_all_reserved_users())

#    print (cb.get_current_boss())
#    cb.lotate_boss()
#    print (cb.get_current_boss())

### 単純な1凸 ###
#    if not cb.attack_check(user_id):
#        cb.attack(user_id)
#    #cb.attack_cancel(user_id)
#
#    is_carry_over, is_round = cb.update_current_boss(damage)
#    cb.finish_attack(user_id, damage, is_carry_over)
#    if is_round:
#        around_count = cb.get_around_count()
#        print ('一周にかかった凸数は、' + str(around_count) + 'です。')
#################

### 周回確認 ###
#    round_dic = cb.get_all_around_count()
#    mes = "各周にかかった凸数はこちら。" + "\n" + '```' + "\n"
#    for r_key in round_dic:
#        mes += str(r_key) + '週目=> ' + str(round_dic[r_key]['attack_count']) + "\n"
#    mes += '```'
#
#    print (mes)
#############

    #print (cb.check_carry_over('476229869001375744'))

    #print (cb.get_attack_count())
    #print (cb.get_remaining_atc_count())

#    cb.insert_carry_over(user_id, boss_num, time)
#    print (cb.get_carry_over_users())



