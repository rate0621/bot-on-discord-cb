#!/bin/sh

# ubuntuだとsourceが使えない
. secret/env.sh

## 実行中プロセスの停止
ps aux | grep discord_bot | grep -v grep | awk '{ print "kill -9", $2 }' | sh


git pull origin master
nohup python discord_bot.py > out.log 2> err.log &

