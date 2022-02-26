import nextcord
from nextcord.ext import commands, tasks
import os
import json
import pymongo
import datetime
from dateutil.relativedelta import relativedelta
import logging
import music
import chat


logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="bot.txt", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("{asctime}: {levelname}: {name}: {message}", style="{"))
logger.addHandler(handler)



cluster = pymongo.MongoClient("mongodb+srv://tEST:sAHmVYepRa3YoW3J@cluster0.zlpox.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")  
db = cluster["songs"]
premium_users = db["premium_users"]



def get_prefix(bot,message):
    with open('prefix.json','r') as f:
        prefixes = json.load(f)
    
    return prefixes[str(message.guild.id)] 


intents = nextcord.Intents.all()
bot = commands.AutoShardedBot(command_prefix = get_prefix,intents = intents,activity = nextcord.Activity(name = '$play',type = nextcord.ActivityType.listening))
bot.remove_command('help')



for file in os.listdir('./'):
    if file.endswith('.py') and file != 'loader.py' and file != 'spotify.py' and file != 'genius.py' and file != 'slash.py':    
        print(file)
        bot.load_extension(f"{file[:-3]}")


@bot.event
async def on_ready():
    # if not check_premium.is_running():
    #     check_premium.start()
    
    
    print('I`m ready')
    


    

@bot.event
async def on_member_update(before,after):
    if after.guild.id == 868435127527690250:
        patron_role = after.guild.get_role(900097466198810624)
        if patron_role not in before.roles and patron_role in after.roles and premium_users.find_one({"_id": after.id}) is None:
            premium_users.insert_one({"_id": after.id,"end_date": datetime.datetime.today() + relativedelta(months=1)})
            await after.send("**:heart: Thanks for buying Spotichat Premium use ``premium`` command to get more info about it**")
        elif patron_role in before.roles and patron_role not in after.roles and premium_users.find_one({"_id": after.id}) is not None: 
            premium_users.delete_one({"_id": after.id})
            await after.send("**:broken_heart: Your premium subscribe has been ended**")
            
@bot.event
async def on_member_join(member):
    if member.guild.id == 868435127527690250:
        role = member.add_roles(member.guild.get_role(900097606045290507))
        await member.add_roles(role)     


@bot.slash_command(name = 'ping',guild_ids=[520969171467632650])
async def get_bot_ping(ctx,message:str = None):
    await ctx.send(embed = nextcord.Embed(description = f'**My ping: {round(bot.latency,1)} ms**',color = nextcord.Color.green()))



@bot.command()
async def slash_ping(ctx):
    await get_bot_ping.callback(ctx)


@bot.command()  
@commands.is_owner()
async def get_json(ctx):
    await ctx.message.author.send(files = [nextcord.File(fp = './' + file,filename=file) for file in os.listdir('./') if file.endswith('.json')])




# @tasks.loop(seconds=1)
# async def check_premium():
#     users = premium_users.find()
#     for user in users:
#         if len(user.keys()) > 1 and user["end_date"] and user["end_date"] < datetime.datetime.now():
#             guild = bot.get_guild(520969171467632650)
#             member = guild.get_member(user["_id"])
            # role = guild.get_role(520969754463305739)
            # await member.remove_roles(role)




@bot.command(aliases = ['h','help'])
async def help_command(ctx): 
    embed = nextcord.Embed(title = 'Help ℹ️',description = 'This commands will be useful.Use command``support`` to get support\nUse ``premium`` to get more info about Spotichat Premium',color = nextcord.Color.green())
    embed.add_field(name = '```Chat commands```',value =
        '`toptracks` - The most popular tracks among guild members\n\n'
        '`searchtracks` - Search tracks by name\n\n'
        '`searchplaylist` - Search playlist by name\n\n'
        '`searchartist` - Search artist by name\n\n'
        '`searchalbums` - Search albums by name\n\n'
        '`lyric` - Get lyric form spotify url\n'
        '`Usage: $lyric <url>`\n'
        '`Alias: l`\n\n'
    )
    
    
    embed.add_field(name = '```Music commands```',value =
        '`play` - Play audio from spotify url\n'
        '`Usage: $play <url>`\n'
        '`Other Usage: $play <name of song>`\n'
        '`Alias: p`\n\n'
        '`stop` - Stop playing audio\n\n'
        '`pause` - Pause playing audio\n\n'
        '`resume` - Resume playing audio\n\n'
        '`skip` - Skip playing audio\n'
        '`Usage: $skip`\n'
        '`Other Usage: $skip <number>`\n'
        '`Alias: sk`\n\n'
        '`loop` - Loop playing current audio\n\n'
        '`queue` - Shows queue of tracks\n'
        '`Alias: q`\n\n'
        '`shuffle` - Shuffle the queue\n'
        '`Alias: shf`\n\n'
        '`clearqueue` - Clear the queue\n'
        '`Alias: clearq`\n\n'
        '`download` - Download tracks from spotify by url\n'
        '`Usage: $download <url>`\n'
        '`Alias: d`\n\n'
        '`saveq`- Save queue\n'
        '`Usage: $saveq <queue_name>`\n'
        '`Alias: svq`\n\n'
        '`svqueues`- Check saved queues\n'
        '`Usage: $svqueues <queue_name>`\n'
        '`Alias: queues`\n\n'
    )

    embed.add_field(name = '```Settings commands```',value = 
    '`delete_commands` - Enable or disable deleting message with command\n\n'
    '`send_embeds` - Enable or disable sending embeds(if it enabled then in specific channel will be sent embed with current track info that member listens to)\n'
    '`Usage: $send_embeds <@channel>`\n\n'
    '`setprefix` - Set custom prefix in guild\n'
    '`Usage: $setprefix <prefix>`\n\n'
    '`addblacklist` - Add channel to blacklist(bot won\'t be able to connect thist channel)\n'
    '`Usage: $addblacklist <voice_channel>`\n\n'
    '`remblacklist` - Remove channel from blacklist\n'
    '`Usage: $remblacklist <voice_channel>`\n\n'
    '`volume` - Change music volume\n'
    '`Usage: $volume <precent(between 10 and 150)>`\n'
    '`Alias: v`\n\n'
    '`addeffect` - Add music effect\n'
    '`Usage: $addeffect <effect name>`'
    '`Alias: addeff`\n\n'
    '`removeeffect` - Remove music effect\n'
    '`Alias: remeff`\n\n'
    )
    
    await ctx.send(embed = embed)


@bot.slash_command(name = 'help',guild_ids=[520969171467632650])
async def help_slash(ctx):
    await help_command.callback(ctx)


@bot.command(name = 'efhelp')
async def ef_help(ctx):
    embed = nextcord.Embed(title = 'Effects Help ℹ️',description = 'A list of available effects',color = nextcord.Color.green())
    embed.add_field(name = '** **',value =
        '`reverse_audio` - reverse the audio\n'
        '`bass_boost` - boost bass in audio\n'
        '`night_core` - a version of a track that increases the pitch and speeds up the pace of its source material by 10–35%.\n'
        '`8D audio` - an effect applied to a stereo track where songs have been edited with \nspacial reverb and mixing to make it seem like the audio moving in a circle around your head.\n'
        '`cristalizte` - makes the song clearly heard, sometimes reduces the bass effect to make song clear\n'
        '`clear` - makes sound more clearly\n'
        '`vaporwave` - slowed-down, chopped and screwed samples of tracks\n'
        '`karaoke` - gets melody melody from track\n'
        '`tremolo` - changes amplitude of the sound\n'
        '`vibrato` - adds expression to vocal and instrumental music\n'
        '`flanger` - is an audio effect produced by mixing two identical signals together\n' 
        '`gate` - makes small gaps in the track\n'
        '`mcompand` - makes the track more muffled'
    )
    await ctx.send(embed = embed)



@bot.command(name = 'premium')
async def send_patreon_url(ctx): 
    embed = nextcord.Embed(title = ':information_source: Info about Spotichat Premium benefits',description = 'Patreon - https://www.patreon.com/spotichat',color = nextcord.Color.green())
    embed.add_field(name = 'Download songs in more size',value='Without premium you can download files in size 3M')
    embed.add_field(name = 'Play music with effects',value = 'To get more info about effects you need to use ``efhelp`` command')
    embed.add_field(name = 'Volume command',value = 'You can change music volume')
    embed.add_field(name = 'Being in voice 24/7',value = 'I will be endlessly in the voice channel')
    embed.add_field(name = 'Save more queues',value = 'You can save more then 6 queues and queue can include more than 8 tracks') 
    await ctx.send(embed = embed) 


@bot.slash_command(name = 'premium',guild_ids=[520969171467632650])
async def send_patreon_url_slash(ctx):
    await send_patreon_url.callback(ctx)


@bot.command(name = 'support')
async def get_support(ctx):
    support_channel = bot.get_channel(900095433634881536)
    invite = await support_channel.create_invite()
    await ctx.send(f"**:information_source: You can get support here** {invite.url}")


@bot.slash_command(name = 'support',guild_ids=[520969171467632650])
async def support_slash(ctx):
    await get_support.callback(ctx)
    


@commands.is_owner()
@bot.command(name = 'send_message')
async def send_message(ctx):
    for guild in bot.guilds:
        if guild.system_channel:
            try:
                channel = guild.system_channel
                with open("message.json") as f:
                    params = json.load(f)
                embed = nextcord.Embed.from_dict(params)
                await channel.send(embed = embed)
            except Exception:
                print('I can`t send message here')



m = music.Music(bot)

@bot.slash_command(name = 'play',guild_ids=[520969171467632650],description='Play music in voice')
async def play_slash(ctx,*,query):
    await m.play_audio(m,ctx = ctx,query = query)

@bot.slash_command(name = 'shuffle',guild_ids=[520969171467632650],description='Mix tracks in queue in random order')
async def shuffle_slash(ctx):
    await m.shuffle_tarcks_in_queue(m,ctx)


@bot.slash_command(name = 'stop',guild_ids=[520969171467632650],description='End playing music')
async def stop_slash(ctx):
    await m.stop_playing_audio(m,ctx)

@bot.slash_command(name = 'pause',guild_ids=[520969171467632650],description='Stop playing music')
async def pause_slash(ctx):
    await m.pause_audio(m,ctx)

@bot.slash_command(name = 'resume',guild_ids=[520969171467632650],description='Resume playing music')
async def resume_slash(ctx):
    await m.continue_playing_audio(m,ctx)

@bot.slash_command(name = 'queue',guild_ids=[520969171467632650],description='Get queue of tracks')
async def queue_slash(ctx):
    await m.queue_of_tracks(m,ctx)

@bot.slash_command(name = 'skip',guild_ids=[520969171467632650],description='Skip current track')
async def skip_slash(ctx):
    await m.skip_song(m,ctx = ctx)

@bot.slash_command(name = 'join',guild_ids=[520969171467632650],description='Join to your channel')
async def join_slash(ctx):
    await m.join_to_channel(m,ctx = ctx)

@bot.slash_command(name = 'loop',guild_ids=[520969171467632650],description='Loop the playing audio')
async def loop_slash(ctx):
    await m.loop(m,ctx = ctx)

@bot.slash_command(name = 'download',guild_ids=[520969171467632650],description='Download track from Spotify')
async def download_slash(ctx,url):
    await m.get_mp3_file(m,ctx = ctx,url = url)       

#=================================================================

c = chat.Chat(bot)

@bot.slash_command(name = 'lyric',guild_ids=[520969171467632650],description='Get track lyric')
async def lyric_slash(ctx,url:str):
    await c.get_lyric(c,ctx,url)

@bot.slash_command(name = 'searchtracks',guild_ids=[520969171467632650],description='Search tracks in Spotify')
async def searchtracks_slash(ctx,*,name:str):
    await c.searchtracks(c,ctx = ctx,name = name)

@bot.slash_command(name = 'searchalbums',guild_ids=[520969171467632650],description='Search albums in Spotify')
async def searchalbums_slash(ctx,*,name:str):
    await c.searchalbums(c,ctx = ctx,name = name)

@bot.slash_command(name = 'searchplaylists',guild_ids=[520969171467632650],description='Search playlists in Spotify')
async def searchplaylists_slash(ctx,*,name:str):
    await c.searchplaylist(c,ctx = ctx,name = name)

@bot.slash_command(name = 'searchartists',guild_ids=[520969171467632650],description='Search artists in Spotify')
async def searchartists_slash(ctx,*,name:str):
    await c.searchartist(c,ctx = ctx,name = name)

    
bot.run('NzkyMzEwMjI2OTM4MTAxNzc5.X-b2Zg.G3nvxdPFGdCzBkBqyw3uFJaHy1c')




  
