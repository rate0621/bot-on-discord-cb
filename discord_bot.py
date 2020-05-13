import discord
import re,os
import setproctitle
import emoji

import Actions
import ManageActions

import common_lib.PriDb as PriDb


client = discord.Client()

BOT_TOKEN  = os.getenv("DISCORD_BOT_TOKEN", "")

def remove_emoji(src_str):
    return ''.join(c for c in src_str if c not in emoji.UNICODE_EMOJI)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
async def on_message(message):

    # botへのメンションのときの動作(主に管理者用)
    if str(client.user.id) in message.content:
        mact = ManageActions.ManageActions()
        mact.check_and_action(message)

    else:
        # 送り主がBotだった場合はスルー
        if client.user != message.author:

#            # 発言の内容をDBに格納
#            
#            text = remove_emoji(message.content)
#
#            if text != '':
#                pridb = PriDb.PriDb()
#                pridb.insert_talk(
#                    message.server.id,
#                    message.author.id,
#                    text,
#                    message.timestamp.strftime("%Y/%m/%d %H:%M:%S")
#                )
#
#
            act = Actions.Actions()
            res_type, res = act.check_and_response(message)

    #    for i in client.get_all_emojis():
    #      print (i)

            if res_type == 'file':
                await client.send_file(message.channel, res)
            if res_type == 'text':
                await message.channel.send(res)
            if res_type == 'emoji':
                for e in res:
                    await client.add_reaction(message, e)


# プロセス名設定
name, ext = os.path.splitext(os.path.basename(__file__))
setproctitle.setproctitle(os.path.basename(name))

client.run(BOT_TOKEN)
