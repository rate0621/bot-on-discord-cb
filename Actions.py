import os, re
from datetime import datetime

import common_lib.priconne_gacha_simulator.GachaSimulation as GachaSimulation
import common_lib.priconne_gacha_simulator.ImageGenerator  as ImageGenerator
import common_lib.Common as Common
import response.Priconne as Pri

class Actions:
  def __init__(self):
    self.res      = None
    self.res_type = None

  def check_and_response(self, req):
    here = os.path.join( os.path.dirname(os.path.abspath(__file__)))

    # スタンプを返す系以外のは初めにチェックする
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

