import os, re
import random
from datetime import datetime, timedelta, timezone
import discord
import gspread

import common_lib.ClanBattle as ClanBattle

CLANBATTLE_HELP = '''
```
パウロスでもわかる機能説明

### 凸宣言　「凸」
    ボスに凸する前に必ず宣言する。

### 凸完了報告　「凸完了　114514」（与えたダメージ）
    ボスに与えたダメージを記載する。
    事前に凸予約していた場合、完了報告することで自動でキャンセルされる。
    数字は全角でも半角でもOK。

### 持ち越し宣言　「持ち越し　70」
    ボスを〆たら持ち越し時間を教えてあげてください。
    その状態でボスを予約すると、予約確認時に持ち越し秒数が表示されて幸せになれます。

### 凸キャンセル　「凸キャンセル」
    凸宣言をキャンセルする。

### 予約　「予約　1」(予約したいボスの番号１〜５)
    予約したいボスがいるならこれで。
    予約しておけば、そのボスが回ってきたときにbotがメンションを飛ばしてくれます。

    多分何件でも予約できるけど良識の範囲内で。

### 予約キャンセル　「予約キャンセル」
    予約したあとにやっぱりキャンセルしたくなったらこれで。
    凸宣言のキャンセルと間違わないように。

### 予約確認 「予約確認」
    誰々が予約しているかが表示される。
    ついでに各ボスの目標凸数も表示される。

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
        if req.channel.id == CLANBATTLE_CHANNEL:
            if re.search("^凸$", req.content):
                cb = ClanBattle.ClanBattle()
                self.res_type = 'text'
                if cb.attack_check(str(req.author.id)):
                    self.res = 'すでに凸宣言済みのようね。'
                else:
                    cb_dict = cb.get_current_boss()
                    self.res = req.author.name + 'が' + cb_dict['boss_name'] + 'に凸するわ。'

                    cb.attack(req.author.id)

                return self.res_type, self.res

            if re.search("^凸完了\s+\d+$", req.content):
                cb = ClanBattle.ClanBattle()
                self.res_type = 'text'
                if cb.attack_check(str(req.author.id)):
                    m = re.search("^凸完了\s+(\d+)$", req.content)
                    
                    damage = m.group(1)
                    damage = damage.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))

                    # ボスが撃破される前に情報を取得
                    cb_dict = cb.get_current_boss()

                    # 凸予約していた場合、凸したフラグを立てる
                    if cb.reserved_check(str(req.author.id), cb_dict['boss_id']):
                        cb.reserved_clear(str(req.author.id), cb_dict['boss_id'])

                    # 持ち越しで叩いた場合、フラグをたてる
                    if cb.check_carry_over(str(req.author.id)):
                        cb.finish_carry_over(str(req.author.id))

                    is_defeat, is_around = cb.update_current_boss(int(damage))
                    cb_dict = cb.get_current_boss()

                    suf_message = ''
                    if is_defeat:
                        user_list = cb.get_reserved_users(cb_dict['boss_id'])
                        call_message = cb_dict['boss_name'] + "の時間よー！\n"
                        if not user_list == []:
                            for u in user_list:
                                call_message += req.server.get_member(u['member_id']).mention

                        suf_message = call_message
                    else:
                        suf_message = cb_dict['boss_name'] + '残り' + str(cb_dict['hit_point']) + 'よ。'

                    cb.finish_attack(str(req.author.id), int(damage), is_defeat)

                    if is_around:
                        around_count = cb.get_around_count()
                        suf_message += 'ちなみにこの' + str(cb_dict['loop_count'] - 1) + '週目の討伐にかかった凸数は、' + str(around_count) + 'よ。'

                    self.res = 'お疲れさま！' + "\n" + suf_message
                else:
                    self.res = '凸宣言していないようね。'
                    

                return self.res_type, self.res

            if re.search("^予約\s+\d+$", req.content):
                cb = ClanBattle.ClanBattle()
                m = re.search("^予約\s+(\d+)$", req.content)
                
                boss_number = m.group(1)
                # 半角に置換
                boss_number = boss_number.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
                cb.boss_reserve(str(req.author.id), int(boss_number))

                self.res_type = 'text'
                self.res      = '予約完了。ボスが回ってきたら教えてあげるわ。すぐに凸れるように模擬はしておくのよ。'

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
                    self.res = '予約キャンセルしておいたわよ'

                else:
                    self.res = 'あなた予約していないわよ。寝ぼけてるの？'
                    
                return self.res_type, self.res

            if re.search("^予約確認$", req.content):
                cb = ClanBattle.ClanBattle()
                
                co_users = cb.get_carry_over_users()
                b_array     = cb.get_bosses()
                user_dict   = cb.get_all_reserved_users()
                cb_dict     = cb.get_current_boss()

                message = "予約状況はこんな感じね。\n```\n"
                for k, b in zip(user_dict, b_array):
                    if k == cb_dict['boss_id']:
                        message += "【" + str(k) + "】(目標凸数:" + str(b['target']) + ")" + " ←イマココ(残り、" + str(cb_dict['hit_point']) + ") \n"
                    else:
                        message += "【" + str(k) + "】(目標凸数:" + str(b['target']) + ")\n"

                    for i, u in enumerate(user_dict[k]):
                        if (u in co_users):
                            message += "    " + u + "  (持ち越し:" + str(co_users[u]['time']) + "秒)" + "\n"
                        else:
                            message += "    " + u + "\n"

                message += "残り凸数は、" + str(cb.get_remaining_atc_count()) + "よ。\n"
                message += "```"

                self.res_type = 'text'
                self.res      = message

                return self.res_type, self.res


            if re.search("^凸キャンセル$", req.content):
                cb = ClanBattle.ClanBattle()
                if cb.attack_check(str(req.author.id)):
                    cb.attack_cancel(str(req.author.id))
                    self.res_type = 'text'
                    self.res      = '凸宣言キャンセルしておいたわよ'

                else:
                    self.res_type = 'text'
                    self.res      = '・・・そもそもあなた凸宣言してないわよ'

                return self.res_type, self.res

            if re.search("^凸数確認$", req.content):
                cb = ClanBattle.ClanBattle()
                attack_count = cb.get_attack_count()
                mes = '今日は今のところ' + str(attack_count) + '凸ね(持ち越しはカウントしてないからね)'

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
                last_boss_number = cb_dict['boss_id'] - 1
                if last_boss_number == 0:
                    last_boss_number = 5

                cb.insert_carry_over(str(req.author.id), last_boss_number, int(time))

                self.res_type = 'text'
                self.res      = '持ち越し時間把握したわ。吐く場所はしっかり考えておくのよ。'

                return self.res_type, self.res
                    
            if re.search("^完凸チェック$", req.content):
                cb = ClanBattle.ClanBattle()
                member_attack_dic = cb.get_today_members_attack_count()
                three_attack_members = cb.get_three_attack_members(member_attack_dic)

                if three_attack_members == []:
                    message = "今日はまだ誰も３凸終えてないわね。・・・大丈夫・・・？"
                else:
                    message = "今日完凸してるメンバーは以下よ\n```\n"
                    for m in three_attack_members:
                        message += m + "\n"

                    message += '```'

                self.res_type = 'text'
                self.res      = message

            if re.search("^未完凸チェック$", req.content):
                cb = ClanBattle.ClanBattle()
                member_attack_dic = cb.get_today_members_attack_count()
                not_three_attack_members = cb.get_not_three_attack_members(member_attack_dic)

                message = "今日まだ未完凸のメンバーは以下よ\n```\n"
                for m in not_three_attack_members:
                    message += m + "\n"

                message += '```'

                self.res_type = 'text'
                self.res      = message

            if re.search("^前日完凸チェック$", req.content):
                cb = ClanBattle.ClanBattle()
                member_attack_dic = cb.get_yesterday_members_attack_count()
                not_three_attack_members = cb.get_not_three_attack_members(member_attack_dic)

                message = "昨日３凸出来なかったメンバーは以下よ。\nただ、持ち越しで処理した場合は凸としてカウントされないからね。```\n"
                for m in not_three_attack_members:
                    message += m + "\n"

                message += "```\nもし、持ち越しで処理とかしてないのに「３凸したのに表示されてるよ！」って人がいたらクラマスに文句を言うといいわ。\nまた、完凸できてた場合に表示してほしいご褒美画像があれば募集してるそうよ。・・・ビキニ以外でね・・・。"

                self.res_type = 'text'
                self.res      = message

            if re.search("^強制退場$", req.content):
                cb = ClanBattle.ClanBattle()
                cb.lotate_boss()
                cb_dict = cb.get_current_boss()

                user_list = cb.get_reserved_users(cb_dict['boss_id'])
                call_message = cb_dict['boss_name'] + "の時間よー！\n"
                if not user_list == []:
                    for u in user_list:
                        call_message += req.server.get_member(u['member_id']).mention

                self.res_type = 'text'
                self.res      = call_message

            if re.search("^周回確認$", req.content):
                cb = ClanBattle.ClanBattle()
                round_dic = cb.get_all_around_count()
                mes = "各周にかかった凸数はこちら。" + "\n" + '```' + "\n"
                for r_key in round_dic:
                    mes += str(r_key) + '週目=> ' + str(round_dic[r_key]['attack_count']) + "\n"

                mes += '```'

                self.res_type = 'text'
                self.res      = mes

            if re.search("^ヘルプ$", req.content):
                self.res_type = 'text'
                self.res      = CLANBATTLE_HELP
                return self.res_type, self.res

        return self.res_type, self.res
                


if __name__ == '__main__':
    pass
#  act = Actions()
#  print (act.have_characters('チャット'))

