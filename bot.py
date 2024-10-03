import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound
import traceback
import sys
import os
from dotenv import load_dotenv
load_dotenv()


bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

bot.remove_command("help")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")

if not DISCORD_TOKEN:
    print("Token not found in .env file")
    exit()

initial_extensions = ['cogs.stage']

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load extension '+extension, file=sys.stderr)
            traceback.print_exc()

@bot.event
async def on_ready():
    print('\nBOOT INFORMATION:')
    print('Bot: ' + str(bot.user.name) + ' | ' + str(bot.user.id))
    print('------\n')
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await ctx.send("Error: Command Not Found!")
        return
    raise error
bot.run(DISCORD_TOKEN)
