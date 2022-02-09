import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound
import traceback
import sys

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

bot.remove_command("help")

DISCORD_TOKEN = 'INSERT DISCORD TOKEN HERE!'

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
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await ctx.send("Command Not Found!", delete_after=2)
        return
    raise error
bot.run(DISCORD_TOKEN)
