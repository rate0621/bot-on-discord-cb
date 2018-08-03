import discord
import re

import Actions

client = discord.Client()

BOT_TOKEN  = os.getenv("DISCORD_BOT_TOKEN", "")

@client.event
async def on_ready():
  print('Logged in as')
  print(client.user.name)
  print(client.user.id)
  print('------')

@client.event
async def on_message(message):
  # 送り主がBotだった場合はスルー
  if client.user != message.author:
    # 発言された内容をチェック
    if re.match("^プリコネ\sガチャ", message.content):
      act = Actions.Actions()
      filepath = act.priconne_gacha_roll10()
      await client.send_file(message.channel, filepath)
    elif re.match("^プリコネはカス", message.content):
      m = 'そり'
      await client.send_message(message.channel, m)


client.run(BOT_TOKEN)
