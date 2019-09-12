import os, sys
import sqlite3

import Common

class ClanBattle():
    def __init__(self):
        pass

    def getBosses(self):
        SPREADSHEET_KEY = os.getenv("SPREADSHEET_KEY", "")

        common = Common.Common()
        wb = common.getWorkBook()
        ws = wb.worksheet('boss_master')
        cell_list = ws.get_all_values()
        print (cell_list[0])



if __name__ == '__main__':
    cb = ClanBattle()
    cb.getBosses()


