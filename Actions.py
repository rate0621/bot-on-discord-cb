import os, re
import random
from datetime import datetime, timedelta, timezone
import discord
import gspread

import common_lib.priconne_gacha_simulator.GachaSimulation as GachaSimulation
import common_lib.priconne_gacha_simulator.ImageGenerator  as ImageGenerator
import common_lib.Common as Common
import response.Priconne as Pri


#ServiceAccountCredentials：Googleの各サービスへアクセスできるservice変数を生成します。
from oauth2client.service_account import ServiceAccountCredentials

class Actions:
  def __init__(self):
    self.res      = None
    self.res_type = None

  def check_and_response(self, req):
    here = os.path.join( os.path.dirname(os.path.abspath(__file__)))


    # スタンプを返す系以外のは初めにチェックする
    # おれ騎士、凸報告部屋
    if req.channel.id == '497391628831555584':
      JST = timezone(timedelta(hours=+9), 'JST')
      now = datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S')
      if datetime.now(JST).strftime('%Y/%m/%d 00:00:00') <= now <= datetime.now(JST).strftime('%Y/%m/%d 04:59:59'):
        print (now)

        self.res_type = 'file'
        self.res      = here + "/static/priconne/amesu2/yohuke.png"

        return self.res_type, self.res
        
      else:
        print (now)


    # アメス教徒のチャンネルID
    #if req.channel.id == '504911147280105475': # 開発用
    if req.channel.id == '497625108387594250':
      if re.search('アメス様', req.content):
        files = os.listdir(here + "/static/priconne/amesu/")

        self.res_type = 'file'
        self.res      = here + "/static/priconne/amesu/" + files[random.randrange(len(files))]

        return self.res_type, self.res

    if re.match("^プリコネ\sガチャ", req.content):
      self.res_type = 'file'
      self.res      = self.priconne_gacha_roll10()

      return self.res_type, self.res

    elif re.match("^↑↑↓↓←→←→\sプリコネ\sガチャ", req.content):
      self.res_type = 'file'
      self.res      = self.priconne_gacha_god_roll10()

      return self.res_type, self.res

    elif re.match("^画像\s", req.content):
      self.res_type = 'text'
      self.res      = self.getImage(req.content)

    elif re.match("^プリコネ\s(.+)\sチャレンジ$", req.content):
      self.res_type = 'text'
      self.res      = self.priconne_gacha_challenge(req.content)

      return self.res_type, self.res

    elif re.match("^test", req.content):
      self.res_type = 'text'
      self.res      = self.have_characters('なゆ')

      return self.res_type, self.res


#    elif re.match("^草", req.content):
#      self.res_type = 'file'
#      self.res      = here + "/static/other/kusaa.jpg"
#
#      return self.res_type, self.res

    # スタンプ系はこの下に記述していく

    # 連続でスタンプがでまくるとログが流れてしまったりと鬱陶しいので、
    # スタンプは5分間に1回しかださない
    last_stamp_time_fp = here + '/last_stamp_time.txt'
    with open(last_stamp_time_fp, mode='r') as fh:
        s = fh.read()
        if s == '':
            last_stamp_time = datetime.strptime('2014/01/01 00:00:00', '%Y/%m/%d %H:%M:%S')
        else:
            last_stamp_time = datetime.strptime(s, '%Y/%m/%d %H:%M:%S')

    now = datetime.now()
    if (now - last_stamp_time).total_seconds() >= 500:
      for word_list in Pri.responses:
        for word in word_list.split(','):
          if re.search(word, req.content):
            self.res      = here + "/static/priconne/" + Pri.responses[word_list]
            self.res_type = 'file'

            with open(last_stamp_time_fp, mode='w') as fh:
              fh.write(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))

            return self.res_type, self.res

    ## 絵文字系はこの下に記述
    if re.search('幼女', req.content):
      self.res_type = 'emoji'
      self.res      = ['you:478527842855026698', 'jo:478527811296952330']

      if re.search('セトラン', str(req.author)):
        self.res_type = 'emoji'
        self.res      = ['tuho:478871148134924309']

      return self.res_type, self.res


    return self.res_type, self.res

  def priconne_gacha_roll10(self):
    gs = GachaSimulation.GachaSimulation()
    charactor_list = gs.roll10()

    ig = ImageGenerator.ImageGenerator()
    gacha_result_path = ig.gacha_result_generator(charactor_list)

    return gacha_result_path

  def priconne_gacha_god_roll10(self):
    gs = GachaSimulation.GachaSimulation()
    charactor_list = gs.god_roll10()

    ig = ImageGenerator.ImageGenerator()
    gacha_result_path = ig.gacha_result_generator(charactor_list)

    return gacha_result_path

  def getImage(self, text):
    match = re.search("^画像\s(.+)", text)
    image_name = match.group(1)

    cmn = Common.Common()
    image_url_list = cmn.getImageUrl(image_name, 1)

    return image_url_list[0]

  def priconne_gacha_challenge(self, text):
    match = re.search("^プリコネ\s(.+)\sチャレンジ$", text)
    chara_name = match.group(1)

    gs = GachaSimulation.GachaSimulation()
    challenge_count, message = gs.challenge(chara_name)

    return message

  def have_characters(self, target_user):

    #2つのAPIを記述しないとリフレッシュトークンを3600秒毎に発行し続けなければならない
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

    TYPE = os.getenv("GS_TYPE", "")
    CLIENT_EMAIL = os.getenv("GS_CLIENT_EMAIL", "")
    PRIVATE_KEY = os.getenv("GS_PRIVATE_KEY", "")
    PRIVATE_KEY_ID = os.getenv("GS_PRIVATE_KEY_ID", "")
    CLIENT_ID = os.getenv("GS_CLIENT_ID", "")

    key_dict = {
      'type': TYPE,
      'client_email': CLIENT_EMAIL,
      'private_key': PRIVATE_KEY,
      'private_key_id': PRIVATE_KEY_ID,
      'client_id': CLIENT_ID,
    }

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)

    #OAuth2の資格情報を使用してGoogle APIにログインします。
    gc = gspread.authorize(credentials)

    #共有設定したスプレッドシートキーを変数[SPREADSHEET_KEY]に格納する。
    SPREADSHEET_KEY = '1yPwbavIQC-pJU_cEy7FlJt8P1gQwFOgkOyVrMFPDg1E'

    #共有設定したスプレッドシートのシート1を開く
    worksheet = gc.open_by_key(SPREADSHEET_KEY).sheet1


    # キャラ数取得
    ## 空文字除去
    characters = worksheet.col_values(2)
    characters = [i for i in characters if i]

    chara_count = len(characters)

    # 対象ユーザのカラム取得
    _range = worksheet.range('C3:AE3')

    target_name = 'なゆ'

    for i in _range:
      if i.value == target_name:
        target_col = i.col


    got_characters = worksheet.col_values(target_col)
    got_characters = [i for i in got_characters if i]
    got_characters.pop(0)

    message = '```'
    for (name, level) in zip(characters, got_characters):
      message += name + ':' + str(level) + "\n"
      #print (name + ':' + str(level))

    message += '```'

    return message

