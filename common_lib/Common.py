import urllib.request
from urllib.parse import quote
import httplib2
import json
import re
import os, sys
import random
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# gspreadはpip installで入れられるやつだが、
# 都合上一部魔改造を施しているため同ディレクトリに置いてあるgspreadをimportする
here = os.path.join( os.path.dirname(os.path.abspath(__file__)))
sys.path.append(here)
import gspread_kai as gspread



class Common():
    def getImageUrl(self, search_item, total_num):
        '''
        googleのcustom serachを利用して引数で指定した文字列の画像を取得する
        Line messaging api の仕様上、画像のURLがhttpsでないとAPIが受け付けてくれないため、httpのURLだった場合はスルーして次の画像（URL）を評価する
        一度のリクエストで10件までしか取得できないため、もし10件ともhttpのリンクだった場合はからのリストが返される。
        @param  検索文字列（str）、取得数（int）
        @return 画像のリンクURL（list）
        '''
        GOOGLE_SEACH_API_KEY = os.environ["GOOGLE_SEACH_API_KEY"]
        CUSTOM_SEARCH_ENGINE = os.environ["CUSTOM_SEARCH_ENGINE"]

        img_list = []
        #i = 0
        query_img = "https://www.googleapis.com/customsearch/v1?key=" + GOOGLE_SEACH_API_KEY + "&cx=" + CUSTOM_SEARCH_ENGINE + "&num=10&start=1&q=" + quote(search_item) + "&searchType=image"
        #query_img = "https://www.googleapis.com/customsearch/v1?key=" + GOOGLE_SEACH_API_KEY + "&cx=" + CUSTOM_SEARCH_ENGINE + "&num=" + str(10 if(total_num-i)>10 else (total_num-i)) + "&start=" + str(i+1) + "&q=" + quote(search_item) + "&searchType=image"
        res = urllib.request.urlopen(query_img)
        data = json.loads(res.read().decode('utf-8'))
        for j in range(len(data["items"])):
            if re.search('https', data["items"][j]["link"]):
                img_list.append(data["items"][j]["link"])
                break

        return img_list

    def get_workbook(self):
        '''
        共有設定されたスプレッドシートのクライアントを返す
        '''


        #2つのAPIを記述しないとリフレッシュトークンを3600秒毎に発行し続けなければならない
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

        TYPE           = os.getenv("GS_TYPE", "")
        CLIENT_EMAIL   = os.getenv("GS_CLIENT_EMAIL", "")
        PRIVATE_KEY    = os.getenv("GS_PRIVATE_KEY", "")
        PRIVATE_KEY_ID = os.getenv("GS_PRIVATE_KEY_ID", "")
        CLIENT_ID      = os.getenv("GS_CLIENT_ID", "")

        key_dict = {
          'type'          : TYPE,
          'client_email'  : CLIENT_EMAIL,
          'private_key'   : PRIVATE_KEY,
          'private_key_id': PRIVATE_KEY_ID,
          'client_id'     : CLIENT_ID,
        }

        SPREADSHEET_KEY = os.getenv("SPREADSHEET_KEY", "")
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)

        #OAuth2の資格情報を使用してGoogle APIにログインします。
        gc = gspread.authorize(credentials)

        return gc.open_by_key(SPREADSHEET_KEY)

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


    def create_gsdf(self, ws):
        '''
        渡されたワークシートをDataFrameに変換し、DF型にして返す。
        '''

        # 本来get_all_valuesにvalue_render_optionのオプションは存在しない(gspread==3.0.1)
        df = pd.DataFrame(ws.get_all_values(value_render_option='FORMULA'))
        df.columns =  list(df.iloc[0])
        df = df.drop(0, axis=0)
        df = df.reset_index(drop=True)

        return df




if __name__ == "__main__":
    #args = sys.argv
    common = Common()
    #img_url = common.getImageUrl(args[1], 1)
    #print(img_url)

    ws = common.get_gsfile('boss_reserve')
    df = common.create_gsdf(ws)
    print (df)
    #SPREADSHEET_KEY = os.getenv("SPREADSHEET_KEY", "")
    #worksheet = gc.open_by_key(SPREADSHEET_KEY).sheet1




