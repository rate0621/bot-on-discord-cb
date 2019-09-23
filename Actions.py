import os, re
import random
from datetime import datetime, timedelta, timezone
import discord
import gspread

import common_lib.Common     as Common
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

### 凸キャンセル　「凸キャンセル」
    凸宣言をキャンセルする。

### 凸予約　「凸予約　1」(予約したいボスの番号１〜５)
    予約したいボスがいるならこれで。
    予約しておけば、そのボスが回ってきたときにbotがメンションを飛ばしてくれます。

    多分何件でも予約できるけど良識の範囲内で。

### 凸予約キャンセル　「凸予約キャンセル」
    予約したあとにやっぱりキャンセルしたくなったらこれで。
    凸宣言のキャンセルと間違わないように。

### 予約確認　「予約確認　1」（確認したいボスの番号）
    誰々が予約しているかが表示される。

### 凸数確認　「凸数確認」
    その日の凸数が表示される。

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
                    boss_num, boss_name, boss_hp = cb.get_current_boss()
                    self.res = req.author.name + 'が' + boss_name + 'に凸するわ。自分を信じていってらっしゃい。'

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
                    boss_num, boss_name, boss_hp = cb.get_current_boss()

                    # 凸予約していた場合、凸したフラグを立てる
                    if cb.reserved_check(str(req.author.id), boss_num):
                        cb.reserved_clear(str(req.author.id), boss_num)

                    is_defeat = cb.update_current_boss(int(damage))
                    boss_num, boss_name, boss_hp = cb.get_current_boss()

                    suf_message = ''
                    if is_defeat:
                        user_list = cb.get_reserved_users(boss_num)
                        call_message = boss_name + "の時間よー！\n"
                        if not user_list == []:
                            for u in user_list:
                                call_message += req.server.get_member(u).mention

                        suf_message = call_message
                    else:
                        suf_message = boss_name + '残り' + str(boss_hp) + 'よ。'

                    cb.finish_attack(str(req.author.id), int(damage), is_defeat)

                    self.res = 'お疲れさま！' + "\n" + suf_message
                else:
                    self.res = '凸宣言していないようね。'
                    

                return self.res_type, self.res

            if re.search("^凸予約\s+\d+$", req.content):
                cb = ClanBattle.ClanBattle()
                m = re.search("^凸予約\s+(\d+)$", req.content)
                
                boss_number = m.group(1)
                # 半角に置換
                boss_number =boss_number.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
                cb.boss_reserve(str(req.author.id), int(boss_number))

                self.res_type = 'text'
                self.res      = '予約完了。ボスが回ってきたら教えてあげるわ。'

                return self.res_type, self.res

            if re.search("^凸予約キャンセル$", req.content):
                cb = ClanBattle.ClanBattle()
                self.res_type = 'text'
                if cb.reserved_check(str(req.author.id)):
                    cb.reserved_clear(str(req.author.id))
                    self.res = '予約キャンセルしておいたわよ'

                else:
                    self.res = 'あなた何も予約していないわよ。寝ぼけてるの？'
                    
                return self.res_type, self.res

            if re.search("^予約確認\s+\d+$", req.content):
                cb = ClanBattle.ClanBattle()
                m = re.search("^予約確認\s+(\d+)$", req.content)
                
                boss_number = m.group(1)
                # 半角に置換
                boss_number =boss_number.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
                user_list = cb.get_reserved_users(int(boss_number))
                reservers = ''
                if not user_list == []:
                    for u in user_list:
                        reservers += req.server.get_member(u).name + "\n"

                    self.res_type = 'text'
                    self.res      = reservers
                else:
                    self.res_type = 'text'
                    self.res      = '誰も予約していないわ。狙い目よ。'


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
                    

            if re.search("^ヘルプ$", req.content):
                self.res_type = 'text'
                self.res      = CLANBATTLE_HELP
                return self.res_type, self.res

        return self.res_type, self.res
                


if __name__ == '__main__':
    pass
#  act = Actions()
#  print (act.have_characters('チャット'))

