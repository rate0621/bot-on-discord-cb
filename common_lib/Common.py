import urllib.request
from urllib.parse import quote
import httplib2
import json
import re
import os, sys
import random

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


if __name__ == "__main__":
  args = sys.argv
  common = Common()
  img_url = common.getImageUrl(args[1], 1)
  print(img_url)
