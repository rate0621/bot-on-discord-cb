import os, re

import common_lib.priconne_gacha_simulator.GachaSimulation as GachaSimulation
import common_lib.priconne_gacha_simulator.ImageGenerator  as ImageGenerator

class Actions:
  def __init__(self):
    self.res      = None
    self.res_type = None

  def check_and_response(self, req):
    if re.match("^プリコネ\sガチャ", req.content):
      self.res_type = 'file'
      self.res      = self.priconne_gacha_roll10()
    elif re.search("やばい", req.content):
      self.res_type = 'file'
      self.res      = self.priconne_yabaidesune()
    elif re.search("ありがとう", req.content):
      self.res_type = 'file'
      self.res      = self.priconne_arigatou()
    elif re.search("さすが", req.content):
      self.res_type = 'file'
      self.res      = self.priconne_sasuga()
    elif re.search("おやすみ", req.content):
      self.res_type = 'file'
      self.res      = self.priconne_oyasumi()

    return self.res_type, self.res

  def priconne_gacha_roll10(self):
    gs = GachaSimulation.GachaSimulation()
    charactor_list = gs.roll10()

    ig = ImageGenerator.ImageGenerator()
    gacha_result_path = ig.gacha_result_generator(charactor_list)

    return gacha_result_path

  def priconne_yabaidesune(self):
    here       = os.path.join( os.path.dirname(os.path.abspath(__file__)))
    send_image_path = here + "/static/priconne/0.png"

    return send_image_path

  def priconne_arigatou(self):
    here       = os.path.join( os.path.dirname(os.path.abspath(__file__)))
    send_image_path = here + "/static/priconne/9.png"

    return send_image_path

  def priconne_sasuga(self):
    here       = os.path.join( os.path.dirname(os.path.abspath(__file__)))
    send_image_path = here + "/static/priconne/10.png"

    return send_image_path

  def priconne_oyasumi(self):
    here       = os.path.join( os.path.dirname(os.path.abspath(__file__)))
    send_image_path = here + "/static/priconne/12.png"

    return send_image_path

