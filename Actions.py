import sys, os, re
import random
from datetime import datetime, timedelta, timezone
import discord
import gspread
import response.Priconne as Pri

import common_lib.ClanBattle as ClanBattle

CLANBATTLE_HELP = '''
```
パウロスでもわかる機能説明

### 凸宣言　「凸 1」
    ボスに凸する前に必ず宣言する。

### 持ち越しでの凸宣言 「持ち越し凸 1」
    ボスに凸する前に必ず宣言する。

### 凸完了報告　「凸完了　114514」（与えたダメージ）
    ボスに与えたダメージを記載する。

### 凸キャンセル　「凸キャンセル」
    凸宣言をキャンセルする。

### 予約　「予約　1」(予約したいボスの番号１〜５)
    予約したいボスがいるならこれで。
    予約しておけば、そのボスが回ってきたときにbotがメンションを飛ばしてくれます。
    また、「予約 1 持ち越しで900万ダメージ予定」みたいな形でメモを残すことも可能です。

### 予約キャンセル　「予約キャンセル」
    予約したあとにやっぱりキャンセルしたくなったらこれで。
    凸宣言のキャンセルと間違わないように。

### 予約確認 「予約確認」
    誰々が予約しているかが表示される。
    ついでに各ボスの目標凸数も表示される。

### 持ち越し確認 「持ち越し確認」
    現時点で誰が何個持ち越しを抱えているかの一覧が表示されます。

### 凸数確認　「凸数確認」
    その日の凸数が表示される。

### 完凸チェック 「完凸チェック」
    その日完凸してる猛者が表示される。

### 未完凸チェック　「未完凸チェック」
    その日にまだ３凸していない騎士くんが表示される。

### 強制退場 「強制退場」
    ネビアちゃんが管理しているボス情報を一歩すすめる。
    例えば、本当は現在はライライなんだけど、ダメージ入力をミスったりして、ボス情報が更新されないときとかに使うとよろし。

### 周回確認 「周回確認」

### 持ち越し計算 「持ち越し計算 500 400」
    同凸で叩いたときの、持ち越し時間が計算をしてくれる。
    上記の例だと、500万→400万の順番で叩いたときの持ち越し時間が表示される。
    入力した値に10000かけた値で計算する点に注意。

### （ダメージメモ板で）「ダメージメモ」
    「ダメージメモ」と打つとアキノさんがメモを開いてくれる。
    その状態で「900」とか「100」とだけ打つとダメージメモにそれを反映してくれる。（投稿したダメージは消える）
   もし投稿したあとに凸を通したりしたら「0」を打てばダメージメモ上から自分のダメージが消える。
   bikiniを押すとアキノさんがダメージメモを閉じる。

```
'''

class Actions:
    def __init__(self):
        self.res      = None
        self.res_type = None

    def check_and_response(self, req):
        here = os.path.join( os.path.dirname(os.path.abspath(__file__)))

        # クラバト関連のアクションはここ
        CLANBATTLE_CHANNEL = os.getenv("CLANBATTLE_CHANNEL", "")
        if str(req.channel.id) == CLANBATTLE_CHANNEL:
            if re.search("^凸\s+\d+$", req.content):
                m = re.search("^凸\s+(\d+)$", req.content)
                boss_num = m.group(1)
                boss_num = boss_num.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))

                cb = ClanBattle.ClanBattle()
                self.res_type = 'text'
                if cb.attack_check(str(req.author.id)):
                    self.res = Pri.SENGEN_ZUMI
                else:
                    bs_dict = cb.get_boss_status()
                    self.res = req.author.name + 'が' + bs_dict[int(boss_num)]['boss_name'] + Pri.TOTU_SURUWA

                    cb.attack(req.author.id, boss_num)

                return self.res_type, self.res

            if re.search("^持ち越し凸\s+\d+$", req.content):
                m = re.search("^持ち越し凸\s+(\d+)$", req.content)
                boss_num = m.group(1)
                boss_num = boss_num.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))

                cb = ClanBattle.ClanBattle()
                self.res_type = 'text'
                if cb.attack_check(str(req.author.id)):
                    self.res = Pri.SENGEN_ZUMI
                else:
                    bs_dict = cb.get_boss_status()
                    self.res = req.author.name + 'が' + bs_dict[int(boss_num)]['boss_name'] + Pri.TOTU_SURUWA

                    is_carry_over = True
                    cb.attack(req.author.id, boss_num, is_carry_over)

                return self.res_type, self.res

            if re.search("^凸完了\s+\d+$", req.content):
                cb = ClanBattle.ClanBattle()
                self.res_type = 'text'
                if cb.attack_check(str(req.author.id)):
                    m = re.search("^凸完了\s+(\d+)$", req.content)
                    
                    damage = m.group(1)
                    damage = damage.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
                    boss_num = cb.get_attacked_boss_num(req.author.id)

                    # ボスが撃破される前に情報を取得
                    cb_dict = cb.get_current_boss()

                    # 凸予約していた場合、凸したフラグを立てる
                    if cb.reserved_check(str(req.author.id), boss_num):
                        cb.reserved_clear(str(req.author.id), boss_num)

#                    # 持ち越しで叩いた場合、フラグをたてる
#                    if cb.check_carry_over(str(req.author.id)):
#                        cb.finish_carry_over(str(req.author.id))

                    is_defeat = cb.update_boss_status(int(damage), boss_num)
                    bs_dict = cb.get_boss_status()

                    suf_message = ''
                    if is_defeat:
                        cb.update_boss_hp(boss_num)
                        cb.insert_carry_over(str(req.author.id), boss_num, 0)

                        user_list = cb.get_reserved_users(boss_num)
                        call_message = bs_dict[int(boss_num)]['boss_name'] + Pri.JIKAN_YO + "\n"
                        if not user_list == []:
                            for u in user_list:
                                call_message += req.guild.get_member(int(u['discord_user_id'])).mention + "\n"

                        suf_message = call_message
                    else:
                        suf_message = bs_dict[int(boss_num)]['boss_name'] + '残り' + str(bs_dict[int(boss_num)]['hit_point']) + Pri.NOKORI_YO

                    cb.finish_attack(str(req.author.id), int(damage), is_defeat)

#                    if is_around:
#                        around_count = cb.get_around_count()
#                        suf_message += 'ちなみにこの' + str(cb_dict['loop_count'] - 1) + '週目の討伐にかかった凸数は、' + str(around_count) + Pri.TOTSUSUU_YO
#
#                        boss_level = cb.get_boss_level(cb_dict['loop_count'])
#                        cb.update_boss_hp(boss_level)


                    self.res = Pri.OTSUKARE_SAMA + "\n" + suf_message
                else:
                    self.res = Pri.SENGEN_SITENAI
                    

                return self.res_type, self.res

            if re.search("^予約\s+\d+", req.content):
                cb = ClanBattle.ClanBattle()
                m = re.search("^予約\s+(\d+)\s(.*)$", req.content)
                option = None
                if m is None:
                    m = re.search("^予約\s+(\d+)$", req.content)
                    boss_number = m.group(1)
                else:
                    boss_number = m.group(1)
                    option = m.group(2)

                # 半角に置換
                boss_number = boss_number.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
                cb.boss_reserve(str(req.author.id), int(boss_number), option)

                self.res_type = 'text'
                self.res      = Pri.YOYAKU_KANRYOU

                return self.res_type, self.res

            if (re.search("^予約キャンセル$", req.content) or re.search("^予約キャンセル\s+\d+$", req.content)):
                cb = ClanBattle.ClanBattle()
                self.res_type = 'text'

                m = re.search("^予約キャンセル\s+(\d+)$", req.content)
                if m:
                    boss_number = m.group(1)
                    boss_number = boss_number.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
                else:
                    boss_number = None

                if cb.reserved_check(str(req.author.id), boss_number):
                    cb.reserved_cancel(str(req.author.id), boss_number)
                    self.res = Pri.YOYAKU_CANCEL

                else:
                    self.res = Pri.YOYAKU_SITENAI
                    
                return self.res_type, self.res

            if re.search("^予約確認$", req.content):
                cb = ClanBattle.ClanBattle()
                
                co_users = cb.get_carry_over_users()
                b_array     = cb.get_bosses()
                user_dict   = cb.get_all_reserved_users()
                bs_dict     = cb.get_boss_status()

                # bs_dictの中から、最小のlevelを取り出す
                min_loop_count = min([int(i["loop_count"]) for i in bs_dict.values()])
                level = cb.get_boss_level(min_loop_count)

                message = Pri.YOYAKU_JOUKYOU + "\n```\n"
                if min_loop_count <= 3:
                    message += "現在:" + str(level) + "段階目 " + "(2段階目は4〜10)\n"
                elif min_loop_count <= 10:
                    message += "現在:" + str(level) + "段階目 " + "(3段階目は11〜30)\n"
                elif min_loop_count <= 31:
                    message += "現在:" + str(level) + "段階目 " + "(4段階目は31〜40)\n"
                elif min_loop_count <= 41:
                    message += "現在:" + str(level) + "段階目 " + "(5段階目は41〜)\n"
                else:
                    message += "\n"

                for k, b, bs in zip(user_dict, b_array, bs_dict):
#                    if k == cb_dict['boss_id']:
#                        message += "【" + str(k) + "】(目標凸数:" + str(b['target']) + ")" + " ←イマココ(残り、" + str(cb_dict['hit_point']) + ") \n"
#                    else:
#                        message += "【" + str(k) + "】(目標凸数:" + str(b['target']) + ")\n"
                    message += "【" + str(k) + "-" + str(bs_dict[bs]['loop_count']) + "】(残りHP:" + str(bs_dict[bs]['hit_point']) + ")\n"

                    for u in user_dict[k]:
#                        if (u['member_name'] in co_users):
#                            message += "    " + u['member_name'] + "  (持ち越し:" + str(co_users[u['member_name']]['time']) + "秒)" + "\n"
#                        else:
                        if u['option'] == '':
                            message += "    " + u['member_name'] + "\n"
                        else:
                            message += "    " + u['member_name'] +  "(" + u['option'] + ")" + "\n"

                message += "残り凸数は、" + str(cb.get_remaining_atc_count()) + Pri.NOKORI_YO + "\n"
                message += "```"

                self.res_type = 'text'
                self.res      = message

                return self.res_type, self.res


            if re.search("^凸キャンセル$", req.content):
                cb = ClanBattle.ClanBattle()
                if cb.attack_check(str(req.author.id)):
                    cb.attack_cancel(str(req.author.id))
                    self.res_type = 'text'
                    self.res      = Pri.TOTU_CANCEL
                else:
                    self.res_type = 'text'
                    self.res      = Pri.TOTU_SENGEN_NASHI

                return self.res_type, self.res

            if re.search("^凸数確認$", req.content):
                cb = ClanBattle.ClanBattle()
                attack_count = cb.get_attack_count()
                mes = Pri.TOTSUSU_KAKUNIN_NOW + str(attack_count) + Pri.TOTSUSU_KAKUNIN_TOTSUNE

                self.res_type = 'text'
                self.res      = mes

                return self.res_type, self.res
                    
            if re.search("^持ち越し\s+\d+$", req.content):
                cb = ClanBattle.ClanBattle()
                m = re.search("^持ち越し\s+(\d+)$", req.content)
                time = m.group(1)
                # 半角に置換
                time = time.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))

                cb_dict = cb.get_current_boss()
                cb.update_carry_over(str(req.author.id), last_boss_number, int(time))

                self.res_type = 'text'
                self.res      = Pri.MOCHIKOSHI_HAAKU

                return self.res_type, self.res

            if re.search("^持ち越し確認$", req.content):
                cb = ClanBattle.ClanBattle()
                co_users = cb.get_carry_over_users()
                message = ''
                for user in co_users:
                    message += user + ":" + str(len(co_users[user])) + "\n"
                    
                self.res_type = 'text'
                self.res      = message

            if re.search("^完凸チェック$", req.content):
                cb = ClanBattle.ClanBattle()
                member_attack_dic = cb.get_today_members_attack_count()
                three_attack_members = cb.get_three_attack_members(member_attack_dic)

                if three_attack_members == []:
                    message = Pri.ALL_MITOTSU
                else:
                    message = Pri.KANTOTSU_MEMBERS + "\n```\n"
                    for m in three_attack_members:
                        message += m + "\n"

                    message += '```'

                self.res_type = 'text'
                self.res      = message

            if re.search("^未完凸チェック$", req.content):
                cb = ClanBattle.ClanBattle()
                member_attack_dic = cb.get_today_members_attack_count()
                not_three_attack_members = cb.get_not_three_attack_members(member_attack_dic)

                message = Pri.MITOTSU_MEMBERS + "\n```\n"
                for m in not_three_attack_members:
                    message += m + "\n"

                message += '```'

                self.res_type = 'text'
                self.res      = message

            if re.search("^前日完凸チェック$", req.content):
                cb = ClanBattle.ClanBattle()
                member_attack_dic = cb.get_yesterday_members_attack_count()
                not_three_attack_members = cb.get_not_three_attack_members(member_attack_dic)

                message = Pri.ZENJITSU_MIKANTOTSU + "\n```\n"
                for m in not_three_attack_members:
                    message += m + "\n"

                message += "```"

                self.res_type = 'text'
                self.res      = message

            if re.search("^強制退場\s\d$", req.content):
                cb = ClanBattle.ClanBattle()
                m = re.search("^強制退場\s+(\d+)$", req.content)
                boss_num = m.group(1)
                # 半角に置換
                boss_num = boss_num.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))

                cb.increment_boss_loop_count(boss_num)
                bs_dict = cb.get_boss_status()

                user_list = cb.get_reserved_users(boss_num)
                call_message = bs_dict[int(boss_num)]['boss_name'] + Pri.JIKAN_YO + "\n"
                if not user_list == []:
                    for u in user_list:
                        call_message += req.guild.get_member(int(u['discord_user_id'])).mention + "\n"


#                boss_level = cb.get_boss_level(cb_dict['loop_count'])
#                cb.update_boss_hp(boss_level)

                self.res_type = 'text'
                self.res      = call_message

            if re.search("^周回確認$", req.content):
                cb = ClanBattle.ClanBattle()
                round_dic = cb.get_all_around_count()
                mes = Pri.SHUKAI_KAKUNIN + "\n" + '```' + "\n"
                for r_key in round_dic:
                    mes += str(r_key) + '週目=> ' + str(round_dic[r_key]['attack_count']) + "\n"

                mes += '```'

                self.res_type = 'text'
                self.res      = mes

            if re.search("^持ち越し計算", req.content):
                cb      = ClanBattle.ClanBattle()
                cb_dict = cb.get_current_boss()
                # 与えられたメッセージから、数値の部分だけ抽出
                damages = []
                [damages.append(int(s)) for s in req.content.split() if s.isdigit()]

                carry_time = cb.get_carry_time(damages)
                if carry_time == 0:
                    mes = Pri.TOUBATSU_HUKA
                else:
                    mes = Pri.MOCHIKOSHI_TIME_NOW_HP + str(cb_dict['hit_point']) + "\n" + Pri.MOCHIKOSHI_TIME_SONOJUNBAN + str(carry_time) + Pri.MOCHIKOSHI_TIME_BYO_NO_MOCHIKOSHI

                self.res_type = 'text'
                self.res      = mes

            if re.search("^ヘルプ$", req.content):
                self.res_type = 'text'
                self.res      = CLANBATTLE_HELP
                return self.res_type, self.res

        CLANBATTLE_DAMAGELOG_CHANNEL = []
        CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL1", ""))
        CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL2", ""))
        CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL3", ""))
        CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL4", ""))
        CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL5", ""))
        if str(req.channel.id) in CLANBATTLE_DAMAGELOG_CHANNEL:
            cb = ClanBattle.ClanBattle()
            dm = cb.is_damage_memo_empty(req.channel.id)
            if re.search("^ダメージメモ$", req.content):
                if cb.is_damage_memo_empty(req.channel.id) is True:
                    # ダメージメモのレコード作成時は、一度メッセージを投稿してからじゃないと、
                    # これからeditしていくメッセージのIDが拾えないため投稿後に、レコードを作成する。
                    bs_dict = cb.get_boss_status()
                    current_boss_num = CLANBATTLE_DAMAGELOG_CHANNEL.index(str(req.channel.id)) + 1
                    self.res_type = 'damage_memo'
                    self.res      = "さて、皆様いくら献上いただけるのかしら？\n```\n" + bs_dict[current_boss_num]['boss_name'] + '残りHP：' + str(bs_dict[current_boss_num]['hit_point']) + "\n```"
                    return self.res_type, self.res
                else:
                    self.res_type = 'text'
                    self.res      = "すでにダメージメモを開いてるようですわ。"
                    return self.res_type, self.res

            if re.search("^\d+$", req.content):
                if cb.is_damage_memo_empty(req.channel.id) is True:
                    # ダメージメモのレコード作成時は、一度メッセージを投稿してからじゃないと、
                    # これからeditしていくメッセージのIDが拾えないため投稿後に、レコードを作成する。
                    self.res_type = 'text'
                    self.res      = "ダメージメモが開かれてないみたいですわ。 `ダメージメモ` と高らかに宣言してくださいまし。"
                    return self.res_type, self.res

                damage = re.search("^(\d+)$", req.content).group(1)
                # 半角に置換
                damage = damage.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))

                m_id = cb.get_damage_memo_message_id(req.channel.id)
                cb.insert_damage_memo(message_id=m_id, user_id=req.author.id, damage=damage, channel_id=req.channel.id)

                bs_dict = cb.get_boss_status()
                current_boss_num = CLANBATTLE_DAMAGELOG_CHANNEL.index(str(req.channel.id)) + 1
                mes = "さて、皆様いくら献上いただけるのかしら？\n```\n" + bs_dict[current_boss_num]['boss_name'] + '残りHP：' + str(bs_dict[current_boss_num]['hit_point']) + "\n"

                dm_list = cb.get_damage_memo(req.channel.id)
                sum_damage = 0
                for dm in dm_list:
                    if dm['damage'] == 0: continue
                    mes += str(dm['id']) + '.' + dm['member_name'] + ': ' + str(dm['damage']) + "\n"
                    sum_damage = sum_damage + dm['damage']
                sum_damage = sum_damage * 10000
                mes += "--------\n予測ボス残りHP： " + str(bs_dict[current_boss_num]['hit_point'] - sum_damage) + "\n"
                mes += "```"

                self.res_type = 'edit'
                self.res = mes
                return self.res_type, self.res

            if re.search("^削除\s+\d+$", req.content):
                if cb.is_damage_memo_empty() is True:
                    # ダメージメモのレコード作成時は、一度メッセージを投稿してからじゃないと、
                    # これからeditしていくメッセージのIDが拾えないため投稿後に、レコードを作成する。
                    self.res_type = 'text'
                    self.res      = "ダメージメモが開かれてないみたいですわ。 `ダメージメモ` と高らかに宣言してくださいまし。"
                    return self.res_type, self.res

                m = re.search("^削除\s+(\d+)$", req.content)
                delete_id = m.group(1)
                delete_member_id = cb.get_member_id_from_damege_memo_id(delete_id)
                cb.delete_damage_memo(delete_member_id)

                cb_dict = cb.get_current_boss()
                mes = "さて、皆様いくら献上いただけるのかしら？\n```\n" + cb_dict['boss_name'] + '残りHP：' + str(cb_dict['hit_point']) + "\n"

                dm_list = cb.get_damage_memo()
                sum_damage = 0
                for dm in dm_list:
                    if dm['damage'] == 0: continue
                    mes += str(dm['id']) + '.' + dm['member_name'] + ': ' + str(dm['damage']) + "\n"
                    sum_damage = sum_damage + dm['damage']
                sum_damage = sum_damage * 10000
                mes += "--------\n予測ボス残りHP： " + str(cb_dict['hit_point'] - sum_damage) + "\n"
                mes += "```"

                self.res_type = 'edit'
                self.res = mes
                return self.res_type, self.res

        if re.search("^体力修正\s+\d+\s+\d+$", req.content):
            m = re.search("^体力修正\s+(\d+)\s+(\d+)$", req.content)
            cb = ClanBattle.ClanBattle()
            cb.change_boss_hp(m.group(1), m.group(2))

        if re.search("^周回修正\s+\d+\s+\d+$", req.content):
            m = re.search("^周回修正\s+(\d+)\s+(\d+)$", req.content)
            cb = ClanBattle.ClanBattle()
            cb.change_loop_count(m.group(1), m.group(2))

                
        return self.res_type, self.res
                
    def insert_damage_memo(self, m):
        cb = ClanBattle.ClanBattle()
        cb.insert_damage_memo(message_id=m.id, user_id=m.author.id, channel_id=m.channel.id)


if __name__ == '__main__':
    pass
#  act = Actions()
#  print (act.have_characters('チャット'))

