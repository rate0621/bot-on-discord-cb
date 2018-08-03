import common_lib.priconne_gacha_simulator.GachaSimulation as GachaSimulation
import common_lib.priconne_gacha_simulator.ImageGenerator as ImageGenerator

class Actions():
  def priconne_gacha_roll10(self):
    gs = GachaSimulation.GachaSimulation()
    charactor_list = gs.roll10()

    ig = ImageGenerator.ImageGenerator()
    gacha_result_path = ig.gacha_result_generator(charactor_list)

    return gacha_result_path
