
from typing import Union
import discord
from discord.ext import commands,tasks
import youtube_dl
from youtube_search import YoutubeSearch
import re
from spotify import TrackNotFound   
import json
import asyncio
import random
from spotify import *

youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'format': 'bestaudio',
    'extractaudio' : True,     
    'audioformat' : "mp3",
    'chachedir': False,
    'quiet':    True
}

ffmpeg_options = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    'options': '-vn'
}


ytdl = youtube_dl.YoutubeDL(ytdl_format_options)



class Music(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
       
    
    @commands.Cog.listener()
    async def on_ready(self):
        if not self.play_loop.is_running():
            self.play_loop.start()
        
        async for guild in self.bot.fetch_guilds():
            with open('loops.json','r') as f:
                loops = json.load(f)
    
            if guild.id not in loops.values():
                loops[str(guild.id)] = '$'

                with open('loops.json','w') as f:
                    json.dump(loops,f,indent = 4)
            
            
            with open('queue.json','r') as f:
                queue = json.load(f)
    
            if guild.id not in queue.values():
                queue[str(guild.id)] = []

                with open('queue.json','w') as f:
                    json.dump(queue,f,indent = 4)
            

            with open('channels.json','r') as f:
                channels = json.load(f)
    
            if guild.id not in channels.values():
                channels[str(guild.id)] = None

                with open('channels.json','w') as f:
                    json.dump(channels,f,indent = 4)
            

            with open('loops.json','r') as f:
                loops = json.load(f)
    
            if guild.id not in loops.values():
                loops[str(guild.id)] = False

                with open('loops.json','w') as f:
                    json.dump(loops,f,indent = 4)

    
    @commands.Cog.listener()
    async def on_voice_state_update(self,member,before,after):
         if before.channel is not None and after.channel is None:
             if member.id == 740290583377215498:
                 self.clear_queue(member.guild)
                 
                 if self.get_loop_state(member.guild):
                     self.change_loop_state(member.guild,False)
                 
    
    @commands.Cog.listener()
    async def on_guild_join(self,guild):
    
        with open('loops.json','r') as f:
                loops = json.load(f)

        loops[str(guild.id)] = False

        with open('loops.json','w') as f:
                json.dump(loops,f,indent = 4)
        
        with open('channels.json','r') as f:
                channels = json.load(f)

        channels[str(guild.id)] = None

        with open('channels.json','w') as f:
                json.dump(channels,f,indent = 4)
        
        with open('queue.json','r') as f:
            queue = json.load(f)
    
        queue[str(guild.id)] = []

        with open('queue.json','w') as f:
            json.dump(queue,f,indent = 4)
    
    @commands.Cog.listener()
    async def on_guild_remove(self,guild):
        with open('loops.json','r') as f:
                loops = json.load(f)

        loops.pop(str(guild.id))

        
        with open('loops.json','w') as f:
                json.dump(loops,f,indent = 4)
        
        with open('channels.json','r') as f:
                channels = json.load(f)

        channels.pop(str(guild.id))

        
        with open('channels.json','w') as f:
                json.dump(channels,f,indent = 4)
        
        
        with open('queue.json','r') as f:
            queue = json.load(f)
    
        
        queue.pop(str(guild.id))

        
        with open('queue.json','w') as f:
            json.dump(queue,f,indent = 4)
        
        if len(self.get_queue(guild)) > 0:
            self.clear_queue(guild)
        
    
        
    def change_current_channel(self,channel:discord.TextChannel):
        with open('channels.json','r') as f:
                channels = json.load(f)

        channels[str(channel.guild.id)] = channel.id

        with open('channels.json','w') as f:
                json.dump(channels,f,indent = 4)
    
    def get_current_channel(self,guild:discord.Guild):
        with open('channels.json','r') as f:
                states = json.load(f)
        return states[str(guild.id)]

    
    
    def change_loop_state(self,guild:discord.Guild,state:bool):
        with open('loops.json','r') as f:
                states = json.load(f)

        states[str(guild.id)] = state

        with open('loops.json','w') as f:
                json.dump(states,f,indent = 4)
    
    def get_loop_state(self,guild:discord.Guild):
        with open('loops.json','r') as f:
                states = json.load(f)
        return states[str(guild.id)]

    

    def queue_current_tarck(self,guild:discord.Guild):
      with open('queue.json','r') as f:
                music = json.load(f)
    
      return music[str(guild.id)][0]
      

    
    
    def get_queue(self,guild:discord.Guild):
        with open('queue.json','r') as f:
            music = json.load(f)
        
        return music[str(guild.id)]
    
    
    
    def insert_in_json(self,guild:discord.Guild):
        with open('queue.json','r') as f:
                music = json.load(f)
        
        if not str(guild.id) in music:
            music[str(guild.id)] = []

            with open('queue.json','w') as f:
                    json.dump(music,f,indent = 4)
        
    
    def queue_remove(self,guild:discord.Guild):
        with open('queue.json','r') as f:
                music = json.load(f)
        
        list = music[str(guild.id)]
        del list[0]
        music[str(guild.id)] = list
        
        with open('queue.json','w') as f:
                json.dump(music,f,indent = 4)
    
    def clear_queue(self,guild:discord.Guild):
        with open('queue.json','r') as f:
                music = json.load(f)

        music[str(guild.id)] = []
        
        with open('queue.json','w') as f:
                json.dump(music,f,indent = 4)
    
    def queue_add(self,guild:discord.Guild,track:Union[str,list]):
        with open('queue.json','r') as f:
            music = json.load(f)
         
        tracks = music[str(guild.id)]
        tracks.append(track) if type(track) == str else tracks.extend(*[track])
        music[str(guild.id)] = tracks
        with open('queue.json','w') as f:
            json.dump(music,f,indent = 4)

    def shuffle_queue(self,guild:discord.Guild):
        with open('queue.json','r') as f:
            music = json.load(f)
        
        if len(music[str(guild.id)]) > 2:
            list = music[str(guild.id)][1:]
            tracks = [self.queue_current_tarck(guild)] + random.sample(list,len(list))
            music[str(guild.id)] = tracks
            with open('queue.json','w') as f:
                json.dump(music,f,indent = 4)
            
        else:
            return False
        
    def track_duration(self,length):
        millis = int(length)
        seconds=(millis/1000)%60
        seconds = int(seconds)
        minutes=(millis/(1000*60))%60
        minutes = int(minutes)
        hours=(millis/(1000*60*60))%24
        return int(hours),int(minutes),int(seconds)

    
    @tasks.loop()
    async def play_loop(self):
        try: 
          for voice in self.bot.voice_clients:
            if voice:
                bef_queue = len(self.get_queue(voice.guild))
                if voice.is_playing() is False and 1 < len(self.get_queue(voice.guild)) and self.get_loop_state(voice.guild) is False and voice.is_connected() and voice.is_paused() is False: 
                    channel = voice.guild.get_channel(self.get_current_channel(voice.guild))
                    print(bef_queue)
                    if bef_queue > 0:
                        self.queue_remove(voice.guild)
                    url = self.queue_current_tarck(voice.guild)
                    await self.load_song(voice.guild,url)
                    await channel.send(embed = self.create_embed(get_track_info(url)[1],url,self.track_duration(get_track_info(url)[0]),get_track_info(url)[4]))
                elif voice.is_playing() is False and self.get_loop_state(voice.guild) and voice.is_paused() is False:
                    await self.load_song(voice.guild,self.queue_current_tarck(voice.guild))
        except NameError as e:
            pass
    
    
    async def load_song(self,guild:discord.Guild,url:str): 
        voice = discord.utils.get(self.bot.voice_clients,guild = guild)
        loop = asyncio.get_event_loop()
        text_to_search = 'Official Music ' +  ", ".join(get_track_info(url)[2]) + '-' + get_track_info(url)[1]
        results_list = YoutubeSearch(text_to_search, max_results=1).to_dict()
        url = "https://www.youtube.com{}".format(results_list[0]['url_suffix'])
        with ytdl:
            data = await loop.run_in_executor(None,lambda: ytdl.extract_info(url,download = False))
            url = data['formats'][0]['url'] 
            player = discord.FFmpegOpusAudio(url,**ffmpeg_options)
            await asyncio.sleep(0.5)
            if voice.is_playing() is False:
               voice.play(player)
        
    
   
    
    def create_embed(self,name,url,duration,image,requester = None,icon = None):
        h,m,s = duration
        h = h if int(h) >= 10 else f'0{h}'
        m = m if int(m) >= 10 else f'0{m}' 
        s = s if int(s) >= 10 else f'0{s}'
     
        time = '00:00:00' if int(h) > 0 else '00:00'
        duration = f'{h}:{m}:{s}' if int(h) else f'{m}:{s}'
    
        text = 'Authors' if len(get_track_info(url)[2]) > 1 else 'Author'
        embed = discord.Embed(title = f'Now playing \"{name}\"',description = f'`{time}\{duration}`',url = url,color = discord.Color.green())
        embed.set_thumbnail(url = image)
        embed.add_field(name = f'{text}',value = ", ".join(get_track_info(url)[2]))
        embed.add_field(name = 'Album',value = f'[{get_track_info(url)[3]}]({get_track_info(url)[5]})')
        embed.add_field(name = 'Release',value = get_track_info(url)[6])
        if requester and icon is not None:
           embed.set_footer(text = f'Requested by {requester}',icon_url = icon)
        return embed
    
    
    @commands.command(aliases = ['p','play'])
    async def play_audio(self,ctx,url:str):
        if ctx.author.voice is None:
            return await ctx.send('**:x:Join to voice channel!**')
        try:
            async with ctx.typing():
                self.insert_in_json(ctx.guild)
                
                self.change_current_channel(ctx.channel)
                voice = discord.utils.get(self.bot.voice_clients,guild = ctx.guild)
                
                list_of_queue_tracks = []
                if not re.findall('album',url) and not re.findall('playlist',url) and not re.findall('artist',url):
                    if len(self.get_queue(ctx.guild)) == 0:
                        self.queue_add(ctx.guild,url)
                    
                    elif voice.is_playing() and len(self.get_queue(ctx.guild)) > 0 :
                        self.queue_add(ctx.guild,url)
                        return await ctx.send(f':white_check_mark: Track **\"{get_track_info(url)[1]}\"** has been added to queue by {ctx.author.mention} :musical_note:')
                
                if re.findall('album',url):
                    list_of_queue_tracks = [track[0] for track in list(get_album_info(url)[0])]    
                    first_album_track = list(get_album_info(url)[0])[0][0]
                    new_url = first_album_track
                   
            
                elif re.findall('playlist',url):
                    list_of_queue_tracks = [track[0][:53] for track in list(get_playlist_info(url)[0])]
                    playlist_first_track = list(get_playlist_info(url)[0])[0][0][:53]
                    new_url = playlist_first_track
              
                elif re.findall('artist',url):
                    region = ctx.guild.region
                    
                    list_of_queue_tracks = [track for track in get_artist_tracks(url,region)]
                    
                    new_url = list_of_queue_tracks[0]
                
                else:
                  if not re.findall('track',url):
                    return await ctx.send('**:x:Invalid link**')
                
                
        except AlbumNotFound:
                await ctx.send('**:x:Album not found**')
        
        except PlayListNotFound:
                await ctx.send('**:x:Playlist not found**')
        
        except TrackNotFound:
                await ctx.send('**:x:Track not found**')
        
        except discord.Forbidden:
                await ctx.send('**:x:I don`t have permissions to connect your channel**')
        
        else:
            self.channel = ctx.channel
            if list_of_queue_tracks:
                await self.load_song(ctx.guild,new_url)
                self.queue_add(ctx.guild,list_of_queue_tracks)
                duration = self.track_duration(get_track_info(new_url)[0])  
                await ctx.send(embed = self.create_embed(get_track_info(new_url)[1],new_url,duration,get_track_info(new_url)[4],requester = ctx.author,icon = ctx.author.avatar_url))
            
	        
            elif re.findall('playlist',url):
                await self.load_song(ctx.guild,url)
                duration = self.track_duration(get_track_info(url)[0])
                await ctx.send(embed = self.create_embed(get_track_info(url)[1],url,duration,get_track_info(url)[4],requester = ctx.author,icon = ctx.author.avatar_url))
                

            
    

    @commands.command(aliases = ['disconnect','leave'])
    async def leave_from_channel(self,ctx):     
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        self.clear_queue(ctx.guild)
        if voice is None:
            await ctx.send("**:x:The bot is not connected to a voice channel.**")
        else:
            await ctx.send(f"**:white_check_mark: I have been disconnected from {voice.channel.mention}.**")
            await voice.disconnect()
        

    
    @commands.command(aliases = ['pause'])
    async def pause_audio(self,ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        
        if voice is None:
            await ctx.send('**:x: Currently i`m not playing anything**')
        else:
            if voice.is_paused():
                await ctx.send('**:x: Music has been already paused**')
            else:
                voice.pause()
                await ctx.send(f"**:arrow_forward: Paused by {ctx.author.mention}**")
        


    @commands.command(aliases = ['res','resume'])
    async def continue_playing_audio(self,ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if voice is None:
            await ctx.send('**:x: Currently i`m not playing anything**')
        
        elif voice.is_paused() is False:
            await ctx.send('**:x:  Music hasn`t been paused**')
        
        else:
            if voice.is_paused():
               voice.resume()
               await ctx.send(f"**:pause_button: Resumed by {ctx.author.mention}**")
        


    @commands.command(aliases = ['s','stop'])
    async def stop_playing_audio(self,ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if voice is None or voice.is_playing() is False:
          await ctx.send('**:x: Currently i`m not playing anything**')
        else:
            self.clear_queue(ctx.guild)
            voice.stop()
            await voice.disconnect()
            if self.get_loop_state(voice.guild):
                self.change_loop_state(ctx.guild,False)
            await ctx.send(f"**:stop_button: Stopped by {ctx.author.mention}**")
  
    @commands.command(aliases = ['q','queue'])
    async def queue_of_tracks(self,ctx,page = 1):
        if len(self.get_queue(ctx.guild)) == 0:
            await ctx.send('**:warning: Queue is empty**')
        else:
          
            queue = len(self.get_queue(ctx.guild)) - 1
            if queue > 5:
                if (page < 1):
                    page = 1
                ELEMENTS_ON_PAGE = 12
                PAGES = queue // ELEMENTS_ON_PAGE
                if queue  % ELEMENTS_ON_PAGE != 0):
                    PAGES += 1
                def calculate_shown_goods(page, ELEMENTS_ON_PAGE = ELEMENTS_ON_PAGE):
                    if (page > 1):
                        START = ELEMENTS_ON_PAGE // (page - 1)
                    elif (page == 1):
                        START = 0
                    STOP = START + ELEMENTS_ON_PAGE
                    return (START, STOP)
                START, STOP = calculate_shown_goods(page)
                async with ctx.typing():
                    embed = discord.Embed(description = '...',color = discord.Color.green())
                    msg = await ctx.send(embed = embed)
                    await msg.add_reaction('◀️')
                    await msg.add_reaction('▶️')
                
                while True:
                    embed = discord.Embed(description = f'In queue: ``{len(queue) - 1}`` {" tracks" if 0 < len(queue) - 1 > 1 else " track"}',color = discord.Color.green())
                    embed.set_author(name = f'Queue | {ctx.guild.name} ',icon_url = ctx.guild.icon_url)
                    embed.add_field(name = 'Now playing:',value = f'[{", ".join(get_track_info(queue[0],False)[1])} - {get_track_info(queue[0],False)[0]}]({queue[0]})')
                    embed.add_field(name = 'Tracks in queue:',value = " \n".join([f'[{", ".join(get_track_info(i,False)[1])} - {get_track_info(i,False)[0]}]({i})' for i in queue[START+1:STOP]]),inline = False)
                    embed.set_footer(text = f'Requested by {ctx.author} | {page}/{PAGES}',icon_url = ctx.author.avatar_url)
                    await msg.edit(embed = embed)
                    
                    
                    try:
                        rea, usr = await self.bot.wait_for('reaction_add', check = lambda r, u: r.message.channel == ctx.channel and u == ctx.author, timeout = 30.0)
                        await rea.remove(usr)
                    except asyncio.TimeoutError:
                        await msg.delete()
                        break
                    else:
                        if (str(rea.emoji) == '▶️' and page < PAGES):
                            page += 1
                            START, STOP = calculate_shown_goods(page)
                        elif (str(rea.emoji) == '◀️' and page > 1):
                            page -= 1
                            START, STOP = calculate_shown_goods(page)
                        
            
            else:
                embed = discord.Embed(description = f'In queue: ``{len(queue) - 1}`` {" tracks" if 0 < len(queue) - 1 > 1 else " track"}',color = discord.Color.green())
                embed.set_author(name = f'Queue | {ctx.guild.name} ',icon_url = ctx.guild.icon_url)
                embed.add_field(name = 'Now playing:',value = f'[{", ".join(get_track_info(queue[0])[2])} - {get_track_info(queue[0])[1]}]({queue[0]})')
                embed.set_footer(text = f'Requested by {ctx.author}',icon_url = ctx.author.avatar_url)
                if len(queue) > 1:
                    embed.add_field(name = 'Tracks in queue:',value = " \n".join([f'[{", ".join(get_track_info(i,False)[1])} - {get_track_info(i,False)[0]}]({i})' for i in queue]),inline = False)
                await ctx.send(embed = embed)
        
    @commands.command(aliases = ['skip','sk'])
    async def skip_song(self,ctx,count_of_skip_tracks:int = None):
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if voice and not voice.is_playing() or voice is None:
            await ctx.send('**:x: Currently i`m not playing anything**')
        else:
            if len(self.get_queue(ctx.guild)) == 1 and not self.get_loop_state(voice.guild):
                self.change_loop_state(ctx.guild,False)
                self.clear_queue(ctx.guild)
        
            if count_of_skip_tracks is None:
                voice.stop()
                await ctx.send(f'**:track_next: Track is skipped by {ctx.author.mention}** ')
            else:
                if count_of_skip_tracks < 2:
                    await ctx.send(f'**:warning: Number must be more then one** ')
                elif count_of_skip_tracks - 1 > len(self.get_queue(ctx.guild)):
                    await ctx.send(f'**:warning: In queue is not so much tracks** ')
                else:
                    for i in range(count_of_skip_tracks - 1):
                        self.queue_remove(ctx.guild)
            
                    await ctx.send(f'**:track_next: Skipped {count_of_skip_tracks} tracks by {ctx.author.mention}** ')
                    voice.stop()

    
    @commands.command(aliases = ['j','join'])
    async def join_to_channel(self,ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        channel = ctx.author.voice.channel
        if voice is None:
            try:
              await channel.connect(timeout = 2)
              await ctx.send(f'**:white_check_mark: I connected to  {channel.mention}**')
            except TimeoutError:
              await ctx.send(f'**:warning: I disconnected from  {channel.mention}**')
        else:
            if voice.channel == ctx.author.voice.channel:
                await ctx.send('**:x: I`m already connected to your channel**')


    @commands.command()
    async def loop(self,ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if voice is None:
           await ctx.send('**:x: Currently i`m not playing anything**')
        else:
            if len(self.get_queue(ctx.guild)) < 1:
                await ctx.send('**:warning: In queue no tracks**')
            else:
                if not self.get_loop_state(ctx.guild):
                    self.change_loop_state(ctx.guild,True)
                    await ctx.send(f'**:repeat: Loop enabled**')
                elif self.get_loop_state(ctx.guild):
                    self.change_loop_state(ctx.guild,False)
                    await ctx.send(f'**:white_check_mark: Loop disabled**')
    
    

    @commands.command(aliases = ['shf','shuffle'])
    async def shuffle_tarcks_in_queue(self,ctx):
        if self.shuffle_queue(ctx.guild) is False:
            await ctx.send('**:warning: In queue no tracks**')
        else:
            await ctx.send('**:white_check_mark: Tracks in queue has been shuffled**')
            self.shuffle_queue(ctx.guild)

    
    @play_audio.before_invoke
    async def check_play(self, ctx: commands.Context):
           voice = discord.utils.get(self.bot.voice_clients,guild = ctx.guild)
           if voice is None:
            if ctx.author.voice is not None:
                await ctx.author.voice.channel.connect()
        
    
    @commands.command(aliases = ['clearq'])
    async def clearqueue(self,ctx):
        if not len(self.get_queue(ctx.guild)) == 0:
            with open('queue.json','r') as f:
                music = json.load(f)

            music[str(ctx.guild.id)] = [self.queue_current_tarck(ctx.guild)]
        
            with open('queue.json','w') as f:
                json.dump(music,f,indent = 4)
            await ctx.send('**:white_check_mark: Queue is cleared**')
    
    
 

        
        
def setup(bot):
  bot.add_cog(Music(bot))
