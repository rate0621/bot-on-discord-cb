import discord
import re,os
import setproctitle
import emoji
import aiohttp
import requests

import Actions
import ManageActions

import common_lib.PriDb as PriDb
import common_lib.ClanBattle as ClanBattle

intents = discord.Intents(messages=True, guilds=True, members=True, reactions=True)
client = discord.Client(intents=intents)

BOT_TOKEN  = os.getenv("DISCORD_BOT_TOKEN", "")
CLANBATTLE_DAMAGELOG_CHANNEL  = os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL", "")

def remove_emoji(src_str):
    return ''.join(c for c in src_str if c not in emoji.UNICODE_EMOJI)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_raw_reaction_add(payload):
    CLANBATTLE_DAMAGELOG_CHANNEL = []
    CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL1", ""))
    CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL2", ""))
    CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL3", ""))
    CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL4", ""))
    CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL5", ""))
    if not client.user.id == payload.user_id and str(payload.channel_id) in CLANBATTLE_DAMAGELOG_CHANNEL:
        cb = ClanBattle.ClanBattle()
        m_id = cb.get_damage_memo_message_id(payload.channel_id)
        if payload.message_id == int(m_id) and payload.emoji.name == emoji.emojize(':bikini:'):
            target_message_id = await client.get_channel(int(payload.channel_id)).fetch_message(payload.message_id)
            await target_message_id.edit(content='お疲れ様！ダメージメモを閉じますわ。', suppress=True)
            print (payload.channel_id)
            cb.delete_damage_memo(payload.channel_id)
        
#        guild_id = payload.guild_id
#        guild = discord.utils.find(lambda g: g.id == guild_id, client.guilds)
#        if checked_emoji == OREKISHI_ROLE_EMOJI:
#            role = guild.get_role(OREKISHI_ROLE_ID)
#            await payload.member.add_roles(role)
#        elif checked_emoji == TOWA_ROLE_EMOJI:
#            role = guild.get_role(TOWA_ROLE_ID)
#            await payload.member.add_roles(role)



@client.event
async def on_message(message):
    CLANBATTLE_DAMAGELOG_CHANNEL = []
    CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL1", ""))
    CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL2", ""))
    CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL3", ""))
    CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL4", ""))
    CLANBATTLE_DAMAGELOG_CHANNEL.append(os.getenv("CLANBATTLE_DAMAGELOG_CHANNEL5", ""))

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
            if res_type == 'damage_memo':
                m = await message.channel.send(res)
                await m.add_reaction(emoji.emojize(':bikini:'))
                act.insert_damage_memo(m)
            if res_type == 'edit':
                cb = ClanBattle.ClanBattle()
                m_id = cb.get_damage_memo_message_id(message.channel.id)
                await message.delete()
                current_boss_num = CLANBATTLE_DAMAGELOG_CHANNEL.index(str(message.channel.id))
                edit_message = await client.get_channel(int(CLANBATTLE_DAMAGELOG_CHANNEL[current_boss_num])).fetch_message(m_id)
                await edit_message.edit(content=res, suppress=True)
            if res_type == 'emoji':
                for e in res:
                    await client.add_reaction(message, e)


# プロセス名設定
name, ext = os.path.splitext(os.path.basename(__file__))
setproctitle.setproctitle(os.path.basename(name))

client.run(BOT_TOKEN)
