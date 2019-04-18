#!/bin/sh

if [ ps aux | grep discord_bot | grep -v grep ] ; then
    echo 'aaa'
else
    echo 'bbb'
fi

