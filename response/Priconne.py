import os, re

### アメス様セリフ
#SENGEN_ZUMI                        = 'すでに凸宣言済みのようね。'
#TOTU_SURUWA                        = 'に凸するわ。'
#JIKAN_YO                           = 'の時間よー！'
#NOKORI_YO                          = 'よ'    ## 「残り〇〇よ」の「よ」の部分
#TOTSUSUU_YO                        = 'よ'  ## 「かかった凸数は〇〇よ」の「よ」の部分
#OTSUKARE_SAMA                      = 'お疲れさま！'
#SENGEN_SITENAI                     = '凸宣言していないようね。'
#YOYAKU_KANRYOU                     = '予約完了。ボスが回ってきたら教えてあげるわ。すぐに凸れるように模擬はしておくのよ。'
#YOYAKU_CANCEL                      = '予約キャンセルしておいたわよ'
#YOYAKU_SITENAI                     = 'あなた予約していないわよ。寝ぼけてるの？'
#YOYAKU_JOUKYOU                     = '予約状況はこんな感じね。'
#TOTU_CANCEL                        = '凸宣言キャンセルしておいたわよ'
#TOTU_SENGEN_NASHI                  = '・・・そもそもあなた凸宣言してないわよ'
#TOTSUSU_KAKUNIN_NOW                = '今日は今のところ、'
#TOTSUSU_KAKUNIN_TOTSUNE            = '凸ね（持ち越しはカウントしてないからね）'
#MOCHIKOSHI_HAAKU                   = '持ち越し時間把握したわ。吐く場所はしっかり考えておくのよ。'
#ALL_MITOTSU                        = '今日はまだ誰も３凸終えてないわね。・・・大丈夫・・・？'
#KANTOTSU_MEMBERS                   = '今日完凸してるメンバーは以下よ'
#MITOTSU_MEMBERS                    = '今日まだ未完凸のメンバーは以下よ'
#ZENJITSU_MIKANTOTSU                = "昨日３凸出来なかったメンバーは以下よ。\nただ、持ち越しで処理した場合は凸としてカウントされないからね。"
#SHUKAI_KAKUNIN                     = '各周にかかった凸数はこちら。'
#TOUBATSU_HUKA                      = 'そもそも討伐すらできなさそうよ。もうちょい頑張って、応援してるわ。'
#MOCHIKOSHI_TIME_NOW_HP             = '今のボスのHPが'
#MOCHIKOSHI_TIME_SONOJUNBAN         = 'その順番で通すとだいたい'
#MOCHIKOSHI_TIME_BYO_NO_MOCHIKOSHI  = '秒の持ち越しになりそうね。'
###

### アキノさんセリフ
SENGEN_ZUMI                        = 'すでに凸宣言済みのようですわ。'
TOTU_SURUWA                        = 'に凸しますわ。'
JIKAN_YO                           = 'の時間ですわよ！'
NOKORI_YO                          = 'ですわ'    ## 「残り〇〇よ」の「よ」の部分
TOTSUSUU_YO                        = 'ですわ'  ## 「かかった凸数は〇〇よ」の「よ」の部分
OTSUKARE_SAMA                      = 'お疲れさま！'
SENGEN_SITENAI                     = '凸宣言していないようですわね。'
YOYAKU_KANRYOU                     = '予約完了。ボスが回ってきたら教えてあげますわ。すぐに凸れるように模擬はしておいてくださいまし。'
YOYAKU_CANCEL                      = '予約キャンセルしておきましたわ'
YOYAKU_SITENAI                     = 'あなた予約していませんわね。'
YOYAKU_JOUKYOU                     = '予約状況はこんな感じですわ。'
TOTU_CANCEL                        = '凸宣言キャンセルしておきましたわ'
TOTU_SENGEN_NASHI                  = '・・・そもそも凸宣言していなくってよ？'
TOTSUSU_KAKUNIN_NOW                = '今日は今のところ、'
TOTSUSU_KAKUNIN_TOTSUNE            = '凸ですわ（持ち越しはカウントしていませんわ）'
MOCHIKOSHI_HAAKU                   = '持ち越し時間把握しましたわ。吐く場所はしっかり考えておいてくださいまし。'
ALL_MITOTSU                        = '今日はまだ誰も３凸終えてませんわね。・・・大丈夫かしら・・・？'
KANTOTSU_MEMBERS                   = '今日完凸してるメンバーは以下ですわ'
MITOTSU_MEMBERS                    = '今日まだ未完凸のメンバーは以下ですわ'
ZENJITSU_MIKANTOTSU                = "昨日３凸出来なかったメンバーは以下ですわ。\nただ、持ち越しで処理した場合は凸としてカウントされないからね。"
SHUKAI_KAKUNIN                     = '各周にかかった凸数はこちらですわ。'
TOUBATSU_HUKA                      = 'そもそも討伐すらできなさそうですわ。お金なら差し上げるのでどうか頑張ってくださいまし。'
MOCHIKOSHI_TIME_NOW_HP             = '今のボスのHPが'
MOCHIKOSHI_TIME_SONOJUNBAN         = 'その順番で通すとだいたい'
MOCHIKOSHI_TIME_BYO_NO_MOCHIKOSHI  = '秒の持ち越しになりそうですわ。'
###

responses = {
  'やばい': '0.png',
  'ヒュー': '1.png',
  '恋してもいいですか': '2.png',
  'あはは,wwww': '3.png',
  'おいっすー,こんにちわ,こんにちは,こんばんわ,こんばんは,よろしくおねがいします,よろしくお願いします,よろしくお頼み申し上げ奉るが候': '4.png',
  'しょんぼり': '5.png',
  'へとへと,疲れた': '6.png',
  'お腹空いた': '7.png',
  '主さま': '8.png',
  'ありがと': '9.png',
  'さすが': '10.png',
  'ふむ': '11.png',
  'おやすみ': '12.png',
  'だめ': '13.png',
  '了解です': '14.png',
  'ご覧ください': '15.png',
  '頼んだ': '16.png',
  '嫌いじゃない': '17.png',
  'いい感じ': '18.png',
  '馬鹿じゃないの': '19.png',
  'ばいばい,またね': '20.png',
  'できる子': '21.png',
  'どうでもいい': '22.png',
#  'にゃん,にゃーん': '23.png',
}

amesu_res = [
'あはは',
'ドンマイ',
'あはははっ！せっかく頑張ったのにねー',
'ごめんなさい！！',
'・・・見てることしかできないと、こういうとき歯がゆいわね。',
'何か良からぬ事態になるかもしれないから、一応覚悟だけはしておいて',
'慎重に、よく考えながら行動しなさい',
'おっと。ごめん、ちょっと興奮しちゃった。',
'草アアアアアア',
'あ、なんだ、あんたまだいたの？もう帰っていいわよ。はいはい、お疲れ様〜',
'どうか負けないで。あたしはいつでも、あんたの味方よ',
'・・・',
'はーい、お疲れ様',
'あたし、すっごい応援してる！！',
'事後処理の仕方を間違えると、詰むわよ',
'実際、今回はかなりやばかったのよ',
'もう寝なさい',
'二度と話しかけてこないで',
'コッコロたんみたいに可愛くなってから出直してきなさい',
]
