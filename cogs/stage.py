import discord
import asyncio
from discord.ext import commands
import sqlite3
import validators
import os.path
import os
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "sqlite.db")

USER_ROLE_ID = os.getenv("USER_ROLE_ID", "")
STAFF_ROLE_ID = os.getenv("STAFF_ROLE_ID", "")
OWNER_ID = os.getenv("OWNER_ID", "")

if not USER_ROLE_ID:
    print("USER_ROLE_ID not found in .env file")
    exit()

if not STAFF_ROLE_ID:
    print("STAFF_ROLE_ID not found in .env file")
    exit()

if not OWNER_ID:
    print("OWNER_ID not found in .env file")
    exit()
class stage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
         
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel is not None:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            guildID = member.guild.id
            c.execute("SELECT voiceChannelID FROM guild WHERE guildID = ?", (guildID,))
            voice=c.fetchone()
            if voice is None:
                pass
            else:
                voiceID = voice[0]
                try:
                    if after.channel.id == voiceID:
                        c.execute("SELECT * FROM voiceChannel WHERE userID = ?", (member.id,))
                        cooldown=c.fetchone()
                        if cooldown is None:
                            pass
                        else:
                            await member.send("Creating channels too quickly you've been put on a 15 second cooldown!")
                            await asyncio.sleep(15)

                        c.execute("SELECT voiceCategoryID FROM guild WHERE guildID = ?", (guildID,))
                        voice=c.fetchone()
                        c.execute("SELECT channelName, channelLimit FROM userSettings WHERE userID = ?", (member.id,))
                        setting=c.fetchone()
                        c.execute("SELECT channelLimit FROM guildSettings WHERE guildID = ?", (guildID,))
                        guildSetting=c.fetchone()
                        if setting is None:
                            name = f"{member.name}'s stage"
                            if guildSetting is None:
                                limit = 0
                            else:
                                limit = guildSetting[0]
                        else:
                            if guildSetting is None:
                                name = setting[0]
                                limit = setting[1]
                            elif guildSetting is not None and setting[1] == 0:
                                name = setting[0]
                                limit = guildSetting[0]
                            else:
                                name = setting[0]
                                limit = setting[1]
                        categoryID = voice[0]
                        id = member.id
                        category = self.bot.get_channel(categoryID)
                        
                        server_id = member.guild.id
                        
                        c.execute("SELECT * FROM serverSettings WHERE serverID = ?", (server_id,))

                        serverSettings=c.fetchone()

                        serverID = serverSettings[0]

                        maxChannels = serverSettings[1]
                        roleID = serverSettings[2]

                        print(serverID, maxChannels, roleID)
                        
                        c.execute("select (select count() from roomCreated) as count, * from roomCreated")

                        rooms=c.fetchone()
                        
                        if rooms == None:
                            c.execute("INSERT INTO roomCreated VALUES (0)")
                        total_rooms = rooms[0]

                        if(total_rooms <= maxChannels or discord.utils.find(lambda r: r.id == roleID, member.roles)):

                            channel2 = await member.guild.create_stage_channel(name,category=category,position=10)

                            channelID = channel2.id

                            utenti = discord.utils.get(member.guild.roles, id=USER_ROLE_ID)
                            staff = discord.utils.get(member.guild.roles, id=STAFF_ROLE_ID)
                            role = discord.utils.get(member.guild.roles, name='@everyone')

                            await member.move_to(channel2)
                            await channel2.set_permissions(self.bot.user, connect=True,read_messages=True)
                            await channel2.set_permissions(member, manage_channels=True, mute_members=True, connect=True, move_members=True)
                            await channel2.set_permissions(utenti, connect=False,read_messages=True)
                            await channel2.set_permissions(staff, connect=True,read_messages=True)
                            await channel2.set_permissions(role, read_messages=False)
                            c.execute("INSERT INTO roomCreated VALUES (?)", (channelID,))
                            conn.commit()
                            
                            c.execute("INSERT INTO voiceChannel VALUES (?, ?)", (id,channelID))
                            conn.commit()

                            
                            print('(' + member.guild.name + ') ' + member.name + ' (id: ' + str(member.id) + ") 's room has been created.")
                            print("Channels: "+str(total_rooms)+"/"+str(maxChannels))
                            
                            def check(a,b,c):
                                return len(channel2.members) == 0
                            await self.bot.wait_for('voice_state_update', check=check)
                            await channel2.delete()
                            
                            c.execute('DELETE FROM voiceChannel WHERE userID=?', (id,))
                            
                            c.execute('DELETE FROM roomCreated WHERE stageID=?', (channelID,))

                            c.execute("select (select count() from roomCreated) as count, * from roomCreated")

                            rooms=c.fetchone()
                            
                            total_rooms = rooms[0]
                            
                            print('(' + member.guild.name + ') ' + member.name + ' (id: ' + str(member.id) + ") 's room has been deleted.")
                            print("Channels: "+str(total_rooms-1)+"/"+str(maxChannels))
                        else:
                            await member.send("Unable to create a stage channel. Max channels limit reached!")
                except:
                    pass
            conn.commit()
            conn.close()

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(title="", description="",color=0x7289da)
        embed.set_author(name=f"{ctx.guild.me.display_name}",url="https://discordbotc.org/bot/472911936951156740", icon_url=f"{ctx.guild.me.avatar_url}")
        embed.add_field(name=f'**Commands:**', value=f'**Lock your channel by using the following command:**\n`.stage lock`\n------------\n\n'
                        f'**Unlock your channel by using the following command:**\n`.stage unlock`\n------------\n\n'
                        f'**Change your channel name by using the following command:**\n`.stage name <name>`\n**Example:** `.stage name EU 5kd+`\n------------\n\n'
                        f'**Change your channel limit by using the following command:**\n`.stage limit number`\n**Example:** `.stage limit 2`\n------------\n\n'
                        f'**Give users permission to join by using the following command:**\n`.stage permit @person`\n**Example:** `.stage permit @Matt05#6501`\n------------\n\n'
                        f'**Claim ownership of channel once the owner has left:**\n`.stage claim`\n**Example:** `.stage claim`\n------------\n\n'
                        f'**Remove permission and the user from your channel using the following command:**\n`.stage reject @person`\n**Example:** `.stage reject @Matt05#6501`\n', inline='false')
        embed.set_footer(text='Bot powered by Matt05#6501')
        await ctx.channel.send(embed=embed)

    @commands.group()
    async def stage(self, ctx):
        pass

    @stage.command()
    async def setup(self, ctx):
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            guildID = ctx.guild.id
            id = ctx.author.id
            if ctx.author.id == ctx.guild.owner.id or ctx.author.id == OWNER_ID:
                def check(m):
                    return m.author.id == ctx.author.id
                print('\n[SETUP] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has started the setup.")
                await ctx.channel.send("**You have 60 seconds to answer each question!**")
                await ctx.channel.send(f"Enter the __name of the category__ you wish to create the channels in: (e.g `Stage Channels`)")
                try:
                    category = await self.bot.wait_for('message', check=check, timeout = 60.0)
                except asyncio.TimeoutError:
                    await ctx.channel.send('Took too long to answer!')
                    print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") took too long to answer (setup failed).")
                else:
                    new_cat = await ctx.guild.create_category_channel(category.content)
                    print('[SETUP] (' + ctx.author.guild.name + ") Category's name: " + category.content)
                    await ctx.channel.send('Enter the __name of the stage channel hub__: (e.g `Join To Create`)')
                    try:
                        channel = await self.bot.wait_for('message', check=check, timeout = 60.0)
                    except asyncio.TimeoutError:
                        await ctx.channel.send('Took too long to answer!')
                        print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") took too long to answer (setup failed).")
                    else:
                        print('[SETUP] (' + ctx.author.guild.name + ") stage channel hub's name: " + channel.content)
                        await ctx.channel.send('Max channels __number__:')
                        try:
                            maxChannels = await self.bot.wait_for('message', check=check, timeout = 60.0)
                        except asyncio.TimeoutError:
                            await ctx.channel.send('Took too long to answer!')
                            print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") took too long to answer (setup failed).")
                        else:
                            print('[SETUP] (' + ctx.author.guild.name + ") Max channels: " + maxChannels.content)
                            await ctx.channel.send("Admin __role's ID__:")
                            try:
                                adminRole = await self.bot.wait_for('message', check=check, timeout = 60.0)
                                print('[SETUP] (' + ctx.author.guild.name + ") Admin role's ID: " + adminRole.content)
                                c.execute("SELECT * FROM serverSettings WHERE serverID = ?", (guildID,))
                                stage=c.fetchone()
                                if stage is None:
                                    c.execute ("INSERT INTO serverSettings VALUES (?, ?, ?)",(guildID,maxChannels.content,adminRole.content))
                                    print('[SETUP] (' + ctx.author.guild.name + ") Created server settings!")
                                else:
                                    c.execute ("UPDATE serverSettings SET serverID = ?, maxChannels = ?, roleID = ?",(guildID,maxChannels.content,adminRole.content))
                                    print('[SETUP] (' + ctx.author.guild.name + ") Updated server settings!")
                                
                            except asyncio.TimeoutError:
                                await ctx.channel.send('Took too long to answer!')
                                print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") took too long to answer (setup failed).")
                            else:
                                try:
                                    channel = await ctx.guild.create_voice_channel(channel.content, category=new_cat)
                                    c.execute("SELECT * FROM guild WHERE guildID = ? AND ownerID=?", (guildID, id))
                                    stage=c.fetchone()
                                    if stage is None:
                                        c.execute ("INSERT INTO guild VALUES (?, ?, ?, ?)",(guildID,id,channel.id,new_cat.id))
                                    else:
                                        c.execute ("UPDATE guild SET guildID = ?, ownerID = ?, stageChannelID = ?, stageCategoryID = ? WHERE guildID = ?",(guildID,id,channel.id,new_cat.id, guildID))
                                    await ctx.channel.send("**You are all setup and ready to go!**")
                                    print('\n[SETUP] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has completed the setup!\n")
                                except:
                                    await ctx.channel.send("You didn't enter the information properly. Use `.stage setup` again!")
                                    print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") didn't enter the information properly (setup failed).")
            else:
                await ctx.channel.send(f"{ctx.author.mention} only the owner of the server can setup the bot!")
                print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") is not the owner of the server (setup failed).")
            conn.commit()
            conn.close()
        except Exception as e:
            print("Error:", e)
            # Send error message to the user
            await ctx.channel.send("An error occurred while setting up the bot. Please try again later.")

    @commands.command()
    async def setlimit(self, ctx, num):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        if ctx.author.id == ctx.guild.owner.id or ctx.author.id == OWNER_ID:
            c.execute("SELECT * FROM guildSettings WHERE guildID = ?", (ctx.guild.id,))
            stage=c.fetchone()
            if stage is None:
                c.execute("INSERT INTO guildSettings VALUES (?, ?, ?)", (ctx.guild.id,f"{ctx.author.name}'s channel",num))
            else:
                c.execute("UPDATE guildSettings SET channelLimit = ? WHERE guildID = ?", (num, ctx.guild.id))
            await ctx.send("You have changed the default channel limit for your server!")
            print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has changed the server's limit.")
        else:
            await ctx.channel.send(f"{ctx.author.mention} only the owner of the server can setup the bot!")
            print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") is not the owner of the server (change default limit failed).")
        conn.commit()
        conn.close()

    @setup.error
    async def info_error(self, ctx, error):
        print('\n[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ') has generated an error:\n' + error + '\n------\n')

    @stage.command()
    async def reset(self, ctx):
        id = ctx.author.id
        if ctx.author.id == ctx.guild.owner.id or ctx.author.id == OWNER_ID:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT * FROM roomCreated")
            print('\n[RESET] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ') has started the reset:')
            channel_to_delete = c.fetchall()
            for channel in channel_to_delete:
                for id in channel:
                    if id != 0:
                        try:
                            channel = self.bot.get_channel(id)
                            print('[RESET] (' + ctx.author.guild.name + ') ' + 'Deleting channel: ' + channel.name)
                            await channel.delete()
                        except Exception as error:
                            print(error)

            c.execute("DELETE FROM roomCreated")
            c.execute("INSERT INTO roomCreated VALUES (0)")
            
            print('[RESET] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ') has completed the reset.\n')
            await ctx.send("Reset completato!")
            
            conn.commit()
            conn.close()
        else:
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") is not the server owner (reset configs failed).")
            await ctx.channel.send(f"{ctx.author.mention} only the owner of the server can reset the bot!")

    @stage.command()
    async def lock(self, ctx):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT stageID FROM stageChannel WHERE userID = ?", (id,))
        stage=c.fetchone()
        if stage is None:
            await ctx.channel.send(f"❌ {ctx.author.mention} you don't own a channel.")
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has not a channel (lock channel failed).")
        else:
            channelID = stage[0]
            role = discord.utils.get(ctx.guild.roles, id=USER_ROLE_ID)
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(role, connect=False,read_messages=True)
            await ctx.channel.send(f'🔒 {ctx.author.mention} stage chat locked!')
            print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has locked his channel.")
        conn.commit()
        conn.close()

    @stage.command()
    async def unlock(self, ctx):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT stageID FROM stageChannel WHERE userID = ?", (id,))
        stage=c.fetchone()
        if stage is None:
            await ctx.channel.send(f"❌ {ctx.author.mention} you don't own a channel.")
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has not a channel (unlock channel failed).")
        else:
            channelID = stage[0]
            role = discord.utils.get(ctx.guild.roles, id=USER_ROLE_ID)
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(role, connect=True,read_messages=True)
            await ctx.channel.send(f'🔓 {ctx.author.mention} stage chat unlocked!')
            print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has unlocked his channel.")
        conn.commit()
        conn.close()

    @stage.command(aliases=["allow"])
    async def permit(self, ctx, member : discord.Member):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT stageID FROM stageChannel WHERE userID = ?", (id,))
        stage=c.fetchone()
        if stage is None:
            await ctx.channel.send(f"❌ {ctx.author.mention} you don't own a channel.")
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has not a channel (permited user failed).")
        else:
            channelID = stage[0]
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(member, connect=True)
            await ctx.channel.send(f'✅ {ctx.author.mention} You have permited {member.name} to have access to the channel.')
            print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ') permited ' + member.name + '(id: ' + member.id + ') to have access to the channel.')
        conn.commit()
        conn.close()

    @stage.command(aliases=["deny"])
    async def reject(self, ctx, member : discord.Member):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        id = ctx.author.id
        guildID = ctx.guild.id
        c.execute("SELECT stageID FROM stageChannel WHERE userID = ?", (id,))
        stage=c.fetchone()
        if stage is None:
            await ctx.channel.send(f"❌ {ctx.author.mention} you don't own a channel.")
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has not a channel (reject user failed).")
        else:
            channelID = stage[0]
            channel = self.bot.get_channel(channelID)
            for members in channel.members:
                if members.id == member.id:
                    c.execute("SELECT stageChannelID FROM guild WHERE guildID = ?", (guildID,))
                    stage=c.fetchone()
                    channel2 = self.bot.get_channel(stage[0])
                    await member.move_to(channel2)
            await channel.set_permissions(member, connect=False,read_messages=True)
            await ctx.channel.send(f':no_entry_sign: {ctx.author.mention} you have rejected {member.name} from accessing the channel.')
            print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ') reject ' + member.name + '(id: ' + member.id + ') to have access to the channel.')
        conn.commit()
        conn.close()

    @stage.command()
    async def limit(self, ctx, limit):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT stageID FROM stageChannel WHERE userID = ?", (id,))
        stage=c.fetchone()
        if stage is None:
            await ctx.channel.send(f"❌ {ctx.author.mention} you don't own a channel.")
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has not a channel (channel limit failed).")
        else:
            channelID = stage[0]
            channel = self.bot.get_channel(channelID)
            await channel.edit(user_limit = limit)
            await ctx.channel.send(f'{ctx.author.mention} You have set the channel limit to be '+ '{}!'.format(limit))
            print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has changed the limit of his channel.")
            c.execute("SELECT channelName FROM userSettings WHERE userID = ?", (id,))
            stage=c.fetchone()
            if stage is None:
                c.execute("INSERT INTO userSettings VALUES (?, ?, ?)", (id,f'{ctx.author.name}',limit))
            else:
                c.execute("UPDATE userSettings SET channelLimit = ? WHERE userID = ?", (limit, id))
        conn.commit()
        conn.close()

    @stage.command(aliases=["rename"])
    async def name(self, ctx,*, name):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT stageID FROM stageChannel WHERE userID = ?", (id,))
        stage=c.fetchone()
        if stage is None:
            await ctx.channel.send(f"❌ {ctx.author.mention} you don't own a channel.")
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has not a channel (rename channel failed).")
        else:
            channelID = stage[0]
            channel = self.bot.get_channel(channelID)
            await channel.edit(name = name)
            await ctx.channel.send(f'{ctx.author.mention} you have changed the channel name to '+ '{}!'.format(name))
            print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") has changed the name of his channel.")
            c.execute("SELECT channelName FROM userSettings WHERE userID = ?", (id,))
            stage=c.fetchone()
            if stage is None:
                c.execute("INSERT INTO userSettings VALUES (?, ?, ?)", (id,name,0))
            else:
                c.execute("UPDATE userSettings SET channelName = ? WHERE userID = ?", (name, id))
        conn.commit()

    @stage.command()
    async def claim(self, ctx):
        x = False
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        channel = ctx.author.stage.channel
        if channel == None:
            await ctx.channel.send(f"❌ {ctx.author.mention} you're not in a stage channel.")
            print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") was not in a stage channel (claim channel failed).")
        else:
            id = ctx.author.id
            c.execute("SELECT userID FROM stageChannel WHERE stageID = ?", (channel.id,))
            stage=c.fetchone()
            if stage is None:
                await ctx.channel.send(f"❌ {ctx.author.mention} you can't own that channel!")
                print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") can not claim this channel (claim channel failed).")
            else:
                for data in channel.members:
                    if data.id == stage[0]:
                        owner = ctx.guild.get_member(stage [0])
                        await ctx.channel.send(f"{ctx.author.mention} this channel is already owned by {owner.mention}!")
                        print('[ERROR] (' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") was already the owner of the channel (claim channel failed).")
                        x = True
                if x == False:
                    await ctx.channel.send(f"{ctx.author.mention} you are now the owner of the channel!")
                    print('(' + ctx.author.guild.name + ') ' + ctx.author.name + ' (id: ' + str(ctx.author.id) + ") claims a channel.")
                    c.execute("UPDATE stageChannel SET userID = ? WHERE stageID = ?", (id, channel.id))
            conn.commit()
            conn.close()

def setup(bot):
    bot.add_cog(stage(bot))