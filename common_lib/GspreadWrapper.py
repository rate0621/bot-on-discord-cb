import re
import os, sys
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# gspreadはpip installで入れられるやつだが、
# 都合上一部魔改造を施しているため同ディレクトリに置いてあるgspreadをimportする
here = os.path.join( os.path.dirname(os.path.abspath(__file__)))
sys.path.append(here)
import gspread_kai as gspread


class GspreadWrapper:
    def __init__(self, key_dict):

        #2つのAPIを記述しないとリフレッシュトークンを3600秒毎に発行し続けなければならない
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

        credentials = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)

        #OAuth2の資格情報を使用してGoogle APIにログインします。
        self.gc = gspread.authorize(credentials)


    def get_workbook(self):
        '''
        共有設定されたスプレッドシートのクライアントを返す
        '''

        SPREADSHEET_KEY = os.getenv("SPREADSHEET_KEY", "")

        return self.gc.open_by_key(SPREADSHEET_KEY)

    def toAlpha(self, num):
        if num<=26:
            return chr(64+num)
        elif num%26==0:
            return toAlpha(num//26-1)+chr(90)
        else:
            return toAlpha(num//26)+chr(64+num%26)


    def get_gsfile(self, sheet_name):
        '''
        渡された名前のワークシートのインスタンスを返す
        '''

        wb = self.get_workbook()
        ws = wb.worksheet(sheet_name)

        return ws


    def create_gsdf(self, ws, value_render_option='FORMULA'):
        '''
        渡されたワークシートをDataFrameに変換し、DF型にして返す。
        '''

        # 本来get_all_valuesにvalue_render_optionのオプションは存在しない(gspread==3.0.1)
        df = pd.DataFrame(ws.get_all_values(value_render_option=value_render_option))
        df.columns =  list(df.iloc[0])
        df = df.drop(0, axis=0)
        df = df.reset_index(drop=True)

        return df

    def check_sheet_exists_and_create(self, check_sheet_title):
        wb = self.get_workbook()
        worksheets = wb.worksheets()
        is_exists = False

        for sheet in worksheets:
            if check_sheet_title == sheet.title:
                is_exists = True
                break

        if not is_exists:
            wb.add_worksheet(title=check_sheet_title, rows=5000, cols=26)

    def excel_date(self, num):
        from datetime import datetime, timedelta
        return(datetime(1899, 12, 30) + timedelta(days=num))




if __name__ == "__main__":
    common = Common()
    #img_url = common.getImageUrl(args[1], 1)
    #print(img_url)

    ws = common.get_gsfile('boss_reserve')
    df = common.create_gsdf(ws, value_render_option='FORMATTED_VALUE')
    print (df)
    #SPREADSHEET_KEY = os.getenv("SPREADSHEET_KEY", "")
    #worksheet = gc.open_by_key(SPREADSHEET_KEY).sheet1




