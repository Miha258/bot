from typing import Union
import nextcord
from nextcord.ext import commands,tasks
import datetime
import youtube_dl
from youtube_search import YoutubeSearch
import re
from spotify import TrackNotFound   
import json
import asyncio
import random
from spotify import *
import math
import validators
import pymongo




youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
                'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
                'format': 'bestaudio/best',
                'extractaudio' : True,     
                'audioformat' : "mp3",
                'cachedir': False,
                'quiet': True,
                'noplaylist': True

}



ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class Music(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.cluster = pymongo.MongoClient("mongodb+srv://tEST:sAHmVYepRa3YoW3J@cluster0.zlpox.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")  
        self.db = self.cluster["songs"]
        self.premium_users = self.db["premium_users"]
        self.guilds = self.db["guilds"]
        self.queues = self.db["queues"]
        
    
    
    @tasks.loop(seconds=3)
    async def check_playing(self):
        guilds = self.guilds.find() 
        guilds = [guild for guild in guilds if guild["disconnect_time"]]
        for guild in guilds:
            if not guild["premium"] and guild["disconnect_time"]:
                guild_obj = nextcord.utils.get(self.bot.guilds,id = guild["_id"])
                voice = guild_obj.voice_client
                if voice and guild["disconnect_time"] > datetime.datetime.now() and not voice.is_playing():
                    await asyncio.sleep(2)
                    if self.guilds.find_one({"_id": guild_obj.id})["last_playing"] is None and len(self.get_queue(guild_obj)) == 0:
                        self.guilds.update_one({"_id": guild_obj.id},{'$set': {"last_playing": datetime.datetime.now() + datetime.timedelta(seconds= 360)}})
                    disc_time = self.guilds.find_one({"_id": guild_obj.id})["last_playing"]
                    if disc_time:
                        if disc_time < datetime.datetime.now():
                            await voice.disconnect()
                            channel = guild_obj.get_channel(self.get_current_channel(guild_obj))
                            self.guilds.update_one({"_id": guild_obj.id},{"$set": {"premium" : False,"disconnect_time" : None,"last_playing": None}})
                            await channel.send('**:warning: I was disconnected because I did do nothing**')

    @tasks.loop(seconds=3)
    async def check_prem_connection(self):
        guilds = self.guilds.find() 
        guilds = [guild for guild in guilds if guild["disconnect_time"]]
        for guild in guilds:
            if not guild["premium"] and guild["disconnect_time"]:
                if guild["disconnect_time"] < datetime.datetime.now():
                    guild = nextcord.utils.get(self.bot.guilds,id = guild["_id"])
                    voice = guild.voice_client
                    if voice:
                        if not voice.is_playing():
                            await voice.disconnect() 
                            channel = guild.get_channel(self.get_current_channel(guild))
                            self.guilds.update_one({"_id": guild.id},{"$set": {"premium" : False,"disconnect_time" : None,"last_playing": None}})
                            await channel.send('**:warning: To use me in voice 24/7 you need to subscribe on Spotichat Premium**')
  
    
    @commands.Cog.listener()
    async def on_command(self,ctx):
        command_name = ctx.command.name
        if command_name == 'join_to_channel' or command_name == 'play_audio':
            voice = ctx.guild.voice_client
            if voice and not self.guilds.find_one({"_id": ctx.guild.id})["disconnect_time"]:
                premium = self.premium_users.find_one({"_id": ctx.author.id})
                if not premium:
                    self.guilds.update_one({"_id": ctx.guild.id},{"$set": {"premium" : False,"disconnect_time" : datetime.datetime.now() + datetime.timedelta(minutes = 30)}})
                elif premium:
                    self.guilds.update_one({"_id": ctx.guild.id},{"$set": {"premium" : True,"disconnect_time" : None,"last_playing": None}})

        

    @commands.Cog.listener()
    async def on_ready(self):
    
        if not self.play_loop.is_running():
            self.play_loop.start()
        
        if not self.check_prem_connection.is_running():
            self.check_prem_connection.start()
        
        if not self.check_playing.is_running():
            self.check_playing.start()
        
        
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
                
            
            await asyncio.sleep(5)
            if self.guilds.count_documents({"_id": guild.id}) == 0:
                self.guilds.insert_one({"_id": guild.id,"premium": False,"disconnect_time": None})
            elif self.guilds.count_documents({"_id": guild.id}) == 1 and self.guilds.find_one({"_id": guild.id})["disconnect_time"]:
                self.guilds.update_one({"_id": guild.id},{"$set": {"premium" : False,"disconnect_time" : None,"last_playing": None}})
    

            
    
    @commands.Cog.listener()
    async def on_voice_state_update(self,member,before,after):
         if before.channel is not None and after.channel is None:
             if member.id == 792310226938101779:
                 self.clear_queue(member.guild)
                 if self.get_loop_state(member.guild):
                     self.change_loop_state(member.guild,False)
                 if self.get_effect(member.guild):
                     self.clear_effect(member.guild)
                 if self.guilds.count_documents({"_id": member.guild.id}) == 1 and self.guilds.find_one({"_id": member.guild.id})["disconnect_time"]:
                    self.guilds.update_one({"_id": member.guild.id},{"$set": {"premium" : False,"disconnect_time" : None,"last_playing": None}})
         

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

        if self.guilds.count_documents({"_id": guild.id}) == 0:
            self.guilds.insert_one({"_id": guild.id,"premium": False,"disconnect_time": None})
    
    @commands.Cog.listener()
    async def on_guild_remove(self,guild):
        if guild.name:
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
            
            if self.guilds.count_documents({"_id": guild.id}) == 1:
                self.guilds.delete_one({"_id": guild.id})
    
    def get_blacklist(self,guild:nextcord.Guild):
        with open('settings.json','r') as f:
            settings = json.load(f)
        
        setting = settings[str(guild.id)]
        return setting["blacklist"] 


    def clear_effect(self,guild:nextcord.Guild):
        with open('settings.json','r') as f:
            settings = json.load(f)
        
        setting = settings[str(guild.id)]
        setting["effect"] = None

        with open('settings.json','w') as f:
            json.dump(settings,f,indent = 4)

    def get_effect(self,guild:nextcord.Guild):
        with open('settings.json','r') as f:
            settings = json.load(f)
        
        setting = settings[str(guild.id)]
        return setting["effect"] 
        
    def change_current_channel(self,channel:nextcord.TextChannel):
        with open('channels.json','r') as f:
                channels = json.load(f)

        channels[str(channel.guild.id)] = channel.id

        with open('channels.json','w') as f:
            json.dump(channels,f,indent = 4)
    
    
    def get_current_channel(self,guild:nextcord.Guild):
        with open('channels.json','r') as f:
                channels = json.load(f)
        return channels[str(guild.id)]

    
    
    def change_loop_state(self,guild:nextcord.Guild,state:bool):
        with open('loops.json','r') as f:
                loops = json.load(f)

        loops[str(guild.id)] = state

        with open('loops.json','w') as f:
                json.dump(loops,f,indent = 4)
    
    def get_loop_state(self,guild:nextcord.Guild):
        with open('loops.json','r') as f:
                states = json.load(f)
        return states[str(guild.id)]


    def queue_current_track(self,guild:nextcord.Guild):
      with open('queue.json','r') as f:
                music = json.load(f)
    
      return music[str(guild.id)][0]
      

  
    
    def get_queue(self,guild:nextcord.Guild):
        with open('queue.json','r') as f:
            music = json.load(f)
        
        return music[str(guild.id)]
    
    
    
    def insert_in_json(self,guild:nextcord.Guild):
        with open('queue.json','r') as f:
                music = json.load(f)
        
        if not str(guild.id) in music:
            music[str(guild.id)] = []

            with open('queue.json','w') as f:
                json.dump(music,f,indent = 4)
        
    
    def queue_remove(self,guild:nextcord.Guild):
        with open('queue.json','r') as f:
                music = json.load(f)
        
        list = music[str(guild.id)]
        del list[0]
        music[str(guild.id)] = list
        
        with open('queue.json','w') as f:
                json.dump(music,f,indent = 4)
    
    def clear_queue(self,guild:nextcord.Guild):
        with open('queue.json','r') as f:
                music = json.load(f)

        music[str(guild.id)] = []
        
        with open('queue.json','w') as f:
                json.dump(music,f,indent = 4)
    
    def queue_add(self,guild:nextcord.Guild,track:Union[str,list],first:bool = None):
        with open('queue.json','r') as f:
            music = json.load(f)
         
        tracks = music[str(guild.id)]
        tracks.append(track) if isinstance(track,str) else tracks.extend(*[track])
        if first and not isinstance(track,list):
            tracks.insert(0,track)
        music[str(guild.id)] = tracks
        with open('queue.json','w') as f:
            json.dump(music,f,indent = 4)

    
    def shuffle_queue(self,guild:nextcord.Guild):
        with open('queue.json','r') as f:
            music = json.load(f)
        
        if len(music[str(guild.id)]) > 2:
            list = music[str(guild.id)][1:]
            tracks = [self.queue_current_track(guild)] + random.sample(list,len(list))
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

    
    @tasks.loop(seconds = 1)
    async def play_loop(self):
        try: 
          for voice in self.bot.voice_clients:
            if voice:
                if voice.is_playing() is False and 1 < len(self.get_queue(voice.guild)) and self.get_loop_state(voice.guild) is False and voice.is_connected() and voice.is_paused() is False:
                    channel = voice.guild.get_channel(self.get_current_channel(voice.guild))
                    self.queue_remove(voice.guild)
                    url = self.queue_current_track(voice.guild)
                    await self.load_song(voice.guild,url)
                    embed,view = self.create_embed(get_track_info(url)[1],url,self.track_duration(get_track_info(url)[0]),get_track_info(url)[4])
                    await channel.send(embed = embed,view = view) 
                elif voice.is_playing() is False and self.get_loop_state(voice.guild) and voice.is_paused() is False:
                    await self.load_song(voice.guild,self.queue_current_track(voice.guild))
        except NameError as e:
            
            pass
    
    
    async def load_song(self,guild:nextcord.Guild,url:str):
        voice = guild.voice_client
        loop = asyncio.get_event_loop()
        authors = await loop.run_in_executor(None,lambda:get_track_info(url)[2])
        track_name = await loop.run_in_executor(None,lambda:get_track_info(url)[1])
        text_to_search = 'Official Music ' +  ", ".join(authors) + '-' + track_name
        results_list = YoutubeSearch(text_to_search, max_results=1).to_dict()
        url = "https://www.youtube.com{}".format(results_list[0]['url_suffix'])
        key = self.get_effect(guild)
        if key:
            keys = {
                'bass_boost': "-af bass=g=7:f=110:w=0.6",
                'vaporwave': "-af aresample=48000,asetrate=48000*0.8",
                "tremolo": "-filter_complex tremolo",
                "vibrato": "-af vibrato=f=6.5",
                "flanger": "-filter_complex flanger",
                "gate": "-filter_complex agate",
                "mcompand": "-filter_complex mcompand",
                'reverse_audio': "-filter_complex areverse", 
                'night_core': '-af \"aresample=48000,asetrate=48000*1.25\"',
                '8D': '-af apulsator=hz=0.08',
                'clear': '-af dynaudnorm=f=200',
                'cristalizte': '-af crystalizer=i=4',
                'karaoke': '-af pan=\"stereo|c0=c0|c1=-1*c1\"'
                
            }

            ffmpeg_options = {
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                'options': '-threads 1 ' + keys[key]
            }
        else:
            ffmpeg_options = {
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                'options': '-vn -threads 1'
            }
        
        with ytdl:
            data = await self.bot.loop.run_in_executor(None,lambda:ytdl.extract_info(url,download = False))
        url = data['formats'][0]['url']
        player = nextcord.FFmpegPCMAudio(url,**ffmpeg_options)
        await asyncio.sleep(1)
        
        if voice.is_playing() is False:
            voice.play(player)
            voice.source = nextcord.PCMVolumeTransformer(voice.source)
            voice.source.volume = 0.5
            
            
            
    
    
    def create_embed(self,name,url,duration,image,requester = None,icon = None):
        h,m,s = duration
        h = h if int(h) >= 10 else f'0{h}'
        m = m if int(m) >= 10 else f'0{m}' 
        s = s if int(s) >= 10 else f'0{s}'
        
        time = '00:00:00' if int(h) > 0 else '00:00'
        duration = f'{h}:{m}:{s}' if int(h) else f'{m}:{s}'
   
        text = 'Authors' if len(get_track_info(url)[2]) > 1 else 'Author'
        embed = nextcord.Embed(title = f'Now playing \"{name}\"',description = f'`{time}\{duration}`',url = url,color = nextcord.Color.green())
        embed.set_thumbnail(url = image)
        embed.add_field(name = f'{text}',value = ", ".join(get_track_info(url)[2]))
        embed.add_field(name = 'Album',value = f'[{get_track_info(url)[3]}]({get_track_info(url)[5]})')
        embed.add_field(name = 'Release',value = get_track_info(url)[6])
        
        
        view = nextcord.ui.View()

        back_btn = nextcord.ui.Button(label='⏮')
        pause_btn = nextcord.ui.Button(label='⏸')
        next_btn = nextcord.ui.Button(label='⏭')
        resume_btn = nextcord.ui.Button(label='▶️')
        stop_btn = nextcord.ui.Button(label='⏹')
        queue_btn = nextcord.ui.Button(label='🎶')
        loop_btn = nextcord.ui.Button(label='🔁')


        async def back_btn_callback(interaction):
            self.queue_add(interaction.guild,self.queue_current_track(interaction.guild),True)
            await self.skip_song(ctx = interaction,replay = True)
            view.stop()

        async def stop_btn_callback(interaction):
            await self.stop_playing_audio(interaction)
            view.stop()
     
        async def next_btn_callback(interaction):
            await self.skip_song(interaction)
            view.stop()

        
        back_btn.callback = back_btn_callback
        pause_btn.callback = lambda ctx: self.pause_audio(ctx)
        resume_btn.callback = lambda ctx: self.continue_playing_audio(ctx)
        next_btn.callback = next_btn_callback
        stop_btn.callback = stop_btn_callback
        queue_btn.callback = lambda ctx: self.queue_of_tracks(ctx)
        loop_btn.callback = lambda ctx: self.loop(ctx)

        buttons = [back_btn,pause_btn,resume_btn,next_btn,stop_btn,queue_btn,loop_btn]
        for button in buttons:
            view.add_item(button)
        
        if requester and icon is not None:
           embed.set_footer(text = f'Requested by {requester}',icon_url = icon)
        return embed,view
    

    
    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command(aliases = ['p','play'])
    async def play_audio(self,ctx,*,query:str):  
        inter = None
        if isinstance(ctx,nextcord.Interaction):   
            inter = ctx
            author = ctx.user
            await self.check_play(ctx)
        else:
            author = ctx.author

        
        if author.voice is None:
            return await ctx.send('**:x:Join to voice channel!**')
        elif author.voice.channel.id in self.get_blacklist(ctx.guild):
            return await ctx.send('**:x:This channel in blacklist**')
        try:
            self.insert_in_json(ctx.guild)
            self.change_current_channel(ctx.channel)
            voice = nextcord.utils.get(self.bot.voice_clients,guild = ctx.guild)
            list_of_queue_tracks = []
            if not validators.url(query):
                if not search(query):
                    raise TrackNotFound
                else:
                    query = search(query)
            
            await ctx.send(f'**:mag_right: Searching for `{query}`...**')
            if not re.findall('album',query) and not re.findall('playlist',query) and not re.findall('artist',query):
                if len(self.get_queue(ctx.guild)) == 0:
                    self.queue_add(ctx.guild,query)
                elif voice.is_playing() and len(self.get_queue(ctx.guild)) > 0:
                    self.queue_add(ctx.guild,query)
                    return await ctx.send(f':white_check_mark: Track **\"{get_track_info(query)[1]}\"** has been added to queue by {author.mention} :musical_note:')
        
            if re.findall('album',query):
                list_of_queue_tracks = [track[0] for track in list(get_album_info(query)[0])]    
                first_album_track = list(get_album_info(query)[0])[0][0]
                new_url = first_album_track
                
        
            elif re.findall('playlist',query):
                list_of_queue_tracks = [track[0][:53] for track in list(get_playlist_info(query)[0])]
                playlist_first_track = list(get_playlist_info(query)[0])[0][0][:53]
                new_url = playlist_first_track
            
            elif re.findall('artist',query):
                region = ctx.guild.region
                list_of_queue_tracks = [track for track in get_artist_tracks(query,region)]
                new_url = list_of_queue_tracks[0]
            
            else:
                if not re.findall('track',query):
                    return await ctx.send('**:x:Invalid link**')
                
                
        except AlbumNotFound:
                await ctx.send('**:x: Album not found**')
        
        except PlayListNotFound:
                await ctx.send('**:x: Playlist not found**')
        
        except TrackNotFound:
                await ctx.send('**:x: Track not found**')
        
        except nextcord.Forbidden:
                await ctx.send('**:x: I don`t have permissions to connect your channel**')
        
        else:
            self.channel = ctx.channel
            if list_of_queue_tracks:
                duration = self.track_duration(get_track_info(new_url)[0])  
                if not voice.is_playing():
                    embed,view = self.create_embed(get_track_info(new_url)[1],new_url,duration,get_track_info(new_url)[4],requester = author,icon = author.avatar.url)
                    await ctx.send(embed = embed,view = view)
                await self.load_song(ctx.guild,new_url)
                self.queue_add(ctx.guild,list_of_queue_tracks)
                
            
            elif re.findall('track',query):
                await self.load_song(ctx.guild,query)
                duration = self.track_duration(get_track_info(query)[0])
                embed,view = self.create_embed(get_track_info(query)[1],query,duration,get_track_info(query)[4],requester = author,icon = author.avatar.url)
                await ctx.send(embed = embed,view = view)

        if inter:
            await inter.edit_original_message(content = '**:white_check_mark: Found**')
            await self.remove_ef(ctx)   
        

    
    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command(aliases = ['disconnect','leave'])
    async def leave_from_channel(self,ctx):     
        voice = nextcord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        self.clear_queue(ctx.guild)
        if voice is None:
            await ctx.send("**:x:The bot is not connected to a voice channel.**")
        else:
            await ctx.send(f"**:white_check_mark: I have been disconnected from {voice.channel.mention}.**")
            await voice.disconnect()
        

    
    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command(aliases = ['pause'])
    async def pause_audio(self,ctx):
        inter = None
        if isinstance(ctx,nextcord.Interaction):
            inter = ctx
            await ctx.send('**Setting on pause...**')
            author = ctx.user
        else:
            author = ctx.author

        
        voice = nextcord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if voice is None:
            await ctx.send('**:x: Currently i`m not playing anything**')
        else:
            if voice.is_paused():
                await ctx.send('**:x: Music has been already paused**')
            else:
                voice.pause()
                await ctx.send(f"**:arrow_forward: Paused by {author.mention}**")
        
        if inter:
            await inter.delete_original_message()

    
    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command(aliases = ['res','resume'])
    async def continue_playing_audio(self,ctx):
        inter = None
        if isinstance(ctx,nextcord.Interaction):
            inter = ctx
            await ctx.send('**Resuming...**')
            author = ctx.user
        else:
            author = ctx.author
    
    
        voice = nextcord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if voice is None:
            await ctx.send('**:x: Currently i`m not playing anything**')
        elif voice.is_paused() is False:
            await ctx.send('**:x:  Music hasn`t been paused**')
        else:
            if voice.is_paused():
               voice.resume()
               await ctx.send(f"**:pause_button: Resumed by {author.mention}**")
        
        if inter:
            await inter.delete_original_message()


    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command(aliases = ['s','stop'])
    async def stop_playing_audio(self,ctx):
        inter = None
        if isinstance(ctx,nextcord.Interaction):
            inter = ctx
            await ctx.send('**Stopping...**')
            author = ctx.user
        else:
            author = ctx.author
            
        
        voice = nextcord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if voice is None or voice.is_playing() is False:
          await ctx.send('**:x: Currently i`m not playing anything**')
        else:
            self.clear_queue(ctx.guild)
            voice.stop()
            await voice.disconnect()
            if self.get_loop_state(voice.guild):
                self.change_loop_state(ctx.guild,False)
            await ctx.send(f"**:stop_button: Stopped by {author.mention}**")
        
        if inter:
            await inter.delete_original_message()

    
    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command(aliases = ['q','queue'])
    async def queue_of_tracks(self,ctx):
        inter = None
        if isinstance(ctx,nextcord.Interaction):
            inter = ctx
            await ctx.send('**Getting queue...**')
             
        if len(self.get_queue(ctx.guild)) == 0:
            await ctx.send('**:warning: Queue is empty**')
        else:
            if inter:
                queue = Queue(inter,self.bot)
            else:
                queue = Queue(ctx,self.bot)
            await queue.send_queue()
        
        if inter:
            await inter.delete_original_message()

    
    @commands.cooldown(1,2, commands.BucketType.user)
    @commands.command(aliases = ['skip','sk'])
    async def skip_song(self,ctx,count_of_skip_tracks:int = None,replay:bool = False):
        inter = None
        if isinstance(ctx,nextcord.Interaction):
            inter = ctx
            await ctx.send('**Skipping...**')
            author = ctx.user
        else:
            author = ctx.author
            

        voice = nextcord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if voice and not voice.is_playing() or voice is None:
            await ctx.send('**:x: Currently i`m not playing anything**')
        else:
            if len(self.get_queue(ctx.guild)) == 1 and not self.get_loop_state(voice.guild):
                self.change_loop_state(ctx.guild,False)
                self.clear_queue(ctx.guild)
        
            if count_of_skip_tracks is None:
                voice.stop()
                if not replay:
                    await ctx.send(f'**:track_next: Track is skipped by {author.mention}** ')
                else:
                    await ctx.send(f'**:arrow_backward: Replayed by {author.mention}**')
            else:
                if count_of_skip_tracks < 2:
                    await ctx.send(f'**:warning: Number must be more then one** ')
                elif count_of_skip_tracks - 1 > len(self.get_queue(ctx.guild)):
                    await ctx.send(f'**:warning: In queue is not so much tracks** ')
                else:
                    for i in range(count_of_skip_tracks - 1):
                        self.queue_remove(ctx.guild)
                    await ctx.send(f'**:track_next: Skipped {count_of_skip_tracks} tracks by {author.mention}** ')
                    voice.stop()
        if inter:
            await inter.delete_original_message()

    
    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command(aliases = ['j','join'])
    async def join_to_channel(self,ctx,_from_queues = False):
        if isinstance(ctx,nextcord.Interaction):
            author = ctx.user
        else:
            author = ctx.author
        
        voice_state = author.voice
        if voice_state is None:
            await ctx.send('**:x: Connect to channel!**')
        elif author.voice.channel.id in self.get_blacklist(ctx.guild):
            await ctx.send('**:x: This channel in blacklist**')
        else:
            voice = ctx.guild.voice_client
            channel = voice_state.channel
            if voice is None:
                self.change_current_channel(ctx.channel)
                await channel.connect()
                await ctx.send(f'**:white_check_mark: I connected to  {channel.mention}**')
            else:
                if voice.channel == channel and not _from_queues:
                    await ctx.send('**:x: I`m already connected to your channel**')

    
    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command()
    async def loop(self,ctx):
        voice = ctx.guild.voice_client
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
    
    

    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command(aliases = ['shf','shuffle'])
    async def shuffle_tarcks_in_queue(self,ctx):
        inter = None
        if isinstance(ctx,nextcord.Interaction):
            inter = ctx
           
        if self.shuffle_queue(ctx.guild) is False:
            await ctx.send('**:warning: In queue no tracks**')
        else:
            await ctx.send('**:white_check_mark: Tracks in queue has been shuffled**')
            self.shuffle_queue(ctx.guild)
        
        if inter:
            await inter.delete_original_message()


    @play_audio.before_invoke
    async def check_play(self, ctx: commands.Context):
        if isinstance(ctx,nextcord.Interaction):
            author = ctx.user
        else:
            author = ctx.author

        voice = nextcord.utils.get(self.bot.voice_clients,guild = ctx.guild)
        if voice is None:
            if author.voice is not None:
                channel = author.voice.channel
                await channel.connect()
    
   
    @play_audio.after_invoke
    async def remove_ef(self,ctx: commands.Context):
        if self.get_effect(ctx.guild):
            self.clear_effect(ctx.guild)

    
    @commands.cooldown(1,3,commands.BucketType.user)
    @commands.has_permissions(manage_messages = True)
    @commands.command(name = 'clearq')
    async def clearqueue(self,ctx):
        if not len(self.get_queue(ctx.guild)) == 0:
            with open('queue.json','r') as f:
                music = json.load(f)

            music[str(ctx.guild.id)] = [self.queue_current_tarck(ctx.guild)]
        
            with open('queue.json','w') as f:
                json.dump(music,f,indent = 4)
            await ctx.send('**:white_check_mark: Queue is cleared**')
    

    @commands.cooldown(1,3,commands.BucketType.user)
    @commands.command(aliases = ['download','d'])
    async def get_mp3_file(self,ctx,url:str):
        premium_user = self.premium_users.find_one({"_id": ctx.author.id})
        try:
            async with ctx.typing():
                text_to_search = 'Official Music ' +  ", ".join(get_track_info(url)[2]) + '-' + get_track_info(url)[1]
                results_list = YoutubeSearch(text_to_search, max_results=1).to_dict()
                url = "https://www.youtube.com{}".format(results_list[0]['url_suffix'])
                result = await self.bot.loop.run_in_executor(None,lambda:ytdl.extract_info(url,download=False))
                data = list(filter(lambda format:format['ext'] == 'm4a',result['formats']))[0]
                url = data['url']
                file_size = data["filesize"] / 1024 / 1000
                if file_size > 3 and not premium_user:
                   await ctx.send('**:x: To download files in size more then 3M you need to subscribe on Spotichat Premium**')
                else:
                    await ctx.reply (embed = nextcord.Embed(title = 'Click to download',url = url,color = nextcord.Color.green()))

    
        except TrackNotFound:
            await ctx.send('**:x: Track not found**')
    

    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command(aliases = ['v','volume'])
    async def change_volume(self,ctx,percent:int):
        premium_user = self.premium_users.find_one({"_id": ctx.author.id})
        if not premium_user:
            await ctx.send(f'**:x: This is premium command**')
        else:
            voice = ctx.guild.voice_client
            
            if not voice:
                ctx.send(f'**:x: I don`t play nothing**')
            elif percent > 150 or percent < 10:
                await ctx.send(f'**:x: Give me precent between 10 and 150**')
            else:
                volume = percent*0.01
                voice.source.volume = volume
                await ctx.send(f'**:white_check_mark: volume set on {percent}%**')
    

    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command(aliases = ['svq','saveq'])
    async def save_queue(self,ctx,queue_name):
        queue = self.get_queue(ctx.guild)
        if len(queue) < 2:
            await ctx.send('**:x: Queue to small to save it**')
        elif len(queue) > 8 and self.premium_users.count_documents({"_id": ctx.author.id}) == 0:
            await ctx.send('**:x: Queue to large to save it without Spotichat Premium**')
        elif len(self.queues.find_one({"_id": ctx.author.id})["queues"]) == 6 and self.premium_users.count_documents({"_id": ctx.author.id}) == 0:
            await ctx.send('**:x: You can`t save more then six queues without Spotichat Premium**')
        elif len(queue) > 100:
            await ctx.send('**:x: Queue to large to save it (max 100 songs for one queue)**')
        elif len(queue_name) > 12:
            await ctx.send('**:x: Name of this queue to long**')
        else:
            if self.queues.count_documents({"_id": ctx.author.id}) == 0:
                self.queues.insert_one({"_id": ctx.author.id,"queues": [{"_id": 0,"name":queue_name ,"items": queue}]})
            else:
                queues = self.queues.find_one({"_id": ctx.author.id})["queues"]
                self.queues.update_one({"_id": ctx.author.id},{"$push":{"queues": {"_id": len(queues),"name":queue_name ,"items": queue}}})
            await ctx.send('**:white_check_mark: Queue saved**') 
  

    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command(aliases = ['queues','svqueues'])
    async def list_of_saved_queues(self,ctx):
        inter = None
        if isinstance(ctx,nextcord.Interaction):
            inter = ctx
            await ctx.send('**Getting saved queues...**')
        
        if self.queues.count_documents({"_id": ctx.author.id}) == 0:
            await ctx.send('**:x: You haven`t any saved queues**')
        else:
            sq = SavedQueue(ctx,self.bot,ctx.author)
            await sq.send_queue()
            
        
        if inter:
            await inter.delete_original_message()


class Queue(Music):      
    def __init__(self,ctx,bot):
        super().__init__(bot)
        self.ctx = ctx
        self.author = self.ctx.user if isinstance(self.ctx,nextcord.Interaction) else self.ctx.author
        self.page = 1
        self.view = nextcord.ui.View()
        self.__queue_lenth = len(self.get_queue(ctx.guild)) - 1
        self.__queue = self.get_queue(ctx.guild)
        self._ELEMENTS_ON_PAGE = 8
        self._PAGES = math.ceil(self.__queue_lenth / self._ELEMENTS_ON_PAGE)

    @property
    def queue(self):
        return self.__queue

    @queue.setter
    def queue(self,new_queue):
        q = self.__queue = new_queue
        self.__queue_lenth = len(q) - 1
        self._PAGES = math.floor(self.__queue_lenth / self._ELEMENTS_ON_PAGE)

    @queue.getter
    def queue(self):
        return self.__queue_lenth - 1


    def _get_embed(self,START,STOP):
        embed = nextcord.Embed(color = nextcord.Color.green())
        embed.set_author(name = f'Queue | {self.ctx.guild.name} ',icon_url = self.ctx.guild.icon.url if self.ctx.guild.icon else "https://camo.githubusercontent.com/10a3f498d105f35e3547b033f0a7bcbc06fa8c837792b50954234b37e1a039bc/68747470733a2f2f6170692e616c6578666c69706e6f74652e6465762f636f6c6f722f696d6167652f333633393346")
        if self.__queue_lenth > 1:
            embed.description = f'In queue: ``{self.__queue_lenth}`` {" tracks" if 0 < self.__queue_lenth > 1 else " track"}'
        
        
        if self.__queue_lenth > self._ELEMENTS_ON_PAGE:
            embed.add_field(name = 'Now playing:',value = f'[{", ".join(get_track_info(self.__queue[0],False)[1])} - {get_track_info(self.__queue[0],False)[0]}]({self.__queue[0]})')
            embed.add_field(name = 'Tracks in queue:',value = " \n".join([f'[{", ".join(get_track_info(i,False)[1])} - {get_track_info(i,False)[0]}]({i})' for i in self.__queue[START+1:STOP]]),inline = False)
            embed.set_footer(text = f'Requested by {self.author} | {self.page}/{self._PAGES}',icon_url = self.author.avatar.url)
        else:
            embed.add_field(name = 'Now playing:',value = f'[{", ".join(get_track_info(self.__queue[0])[2])} - {get_track_info(self.__queue[0])[1]}]({self.__queue[0]})')
            embed.set_footer(text = f'Requested by {self.author}',icon_url = self.author.avatar.url)
            if self.__queue_lenth > 1: 
                embed.add_field(name = 'Tracks in queue:',value = " \n".join([f'[{", ".join(get_track_info(i,False)[1])} - {get_track_info(i,False)[0]}]({i})' for i in self.__queue[1:]]),inline = False)
       
        return embed
    
    
    def _calculate_shown_goods(self,page):
        START = 0
        if (page > 1):
            START = self._ELEMENTS_ON_PAGE // (page - 1)
        
       
        STOP = START + self._ELEMENTS_ON_PAGE
        return (START, STOP)
    
    
    async def _left_callback(self,interaction):
        self.page -= 1
        if (self.page < 1):
            self.page = 1
        
        START, STOP = self._calculate_shown_goods(self.page)
        return await interaction.message.edit(embed = self._get_embed(START, STOP),view = self.view)
    
    
    async def _right_callback(self,interaction):
        self.page += 1
        if (self.page < 1):
            self.page = 1
        elif (self.page + 1) > self._PAGES:
            self.page = self._PAGES
        
        
        START, STOP = self._calculate_shown_goods(self.page)
        return await interaction.message.edit(embed = self._get_embed(START, STOP))
    
    
    async def send_queue(self):
        view = self.view
        left = nextcord.ui.Button(label='◀️')
        right = nextcord.ui.Button(label='▶️')
        left.callback = self._left_callback
        right.callback = self._right_callback
        
        if self.__queue_lenth > self._ELEMENTS_ON_PAGE:
            START,STOP = self._calculate_shown_goods(self.page)
            view.add_item(left)
            view.add_item(right)
            await self.ctx.send(embed = self._get_embed(START,STOP),view = view)
    
        else:
            await self.ctx.send(embed = self._get_embed(0,self._ELEMENTS_ON_PAGE))

        



class SavedQueue(Queue):
    def __init__(self,ctx:commands.Context,bot,member:nextcord.Member):
        super().__init__(ctx,bot)
        self.__member = member
        self.__saved_queues = self.queues.find_one({"_id": self.__member.id})["queues"]
        self.__queues_lenth = len(self.__saved_queues)
        self._ELEMENTS_ON_PAGE = 6
        self._PAGES = math.ceil(self.__queues_lenth / self._ELEMENTS_ON_PAGE)
       
      


    def _get_embed(self,START,STOP):
        embed = nextcord.Embed(color = nextcord.Color.green())
        embed.set_author(name = f'List of saved queues {self.__member} ',icon_url = self.__member.avatar.url if self.ctx.guild.icon else "https://camo.githubusercontent.com/10a3f498d105f35e3547b033f0a7bcbc06fa8c837792b50954234b37e1a039bc/68747470733a2f2f6170692e616c6578666c69706e6f74652e6465762f636f6c6f722f696d6167652f333633393346")
        self.__saved_queues = self.queues.find_one({"_id": self.__member.id})["queues"]
        self.__queues_lenth = len(self.__saved_queues)
        self._PAGES = math.ceil(self.__queues_lenth / self._ELEMENTS_ON_PAGE)
        queues_list = self.__saved_queues
        if self.__queues_lenth > self._ELEMENTS_ON_PAGE:
            queues_list = self.__saved_queues[START:STOP]
        
        
        emojis = {
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣"
        }

        self.view.clear_items()
        left = nextcord.ui.Button(label='◀️',row = 2)
        right = nextcord.ui.Button(label='▶️',row = 2)
        left.callback = self._left_callback
        right.callback = self._right_callback
        self.view.add_item(left)
        self.view.add_item(right)


        for i,queue in enumerate(queues_list,1):
            row = 0 if i < 4 else 1
            name = queue["name"]
            queue_lenth = len(queue["items"])
            btn = nextcord.ui.Button(label=emojis[i],custom_id=str(i+(self._ELEMENTS_ON_PAGE * (self.page - 1))),row = row)
            btn.callback = self._select_btn_callback 
            self.view.add_item(btn)
            embed.add_field(name = f"#{i} Queue \'{name}\'",value = f'**Length: {queue_lenth}**')
            
    
        embed.set_footer(text = f'Requested by {self.__member} | {self.page}/{self._PAGES}',icon_url = self.ctx.author.avatar.url)
        return embed    
    
    
    async def _select_btn_callback(self,interaction):
        self.view.clear_items()
        self.page = 1
        item_id = interaction.data["custom_id"]
        queue = Queue(self.ctx,self.bot)
        index = int(item_id)-1
        queue.queue = self.__saved_queues[index]["items"]
        
        queue_lenth = queue.queue
        if queue_lenth > queue._ELEMENTS_ON_PAGE:
            START,STOP = queue._calculate_shown_goods(queue.page)
            embed = queue._get_embed(START,STOP)
        else:
            embed = queue._get_embed(0,queue._ELEMENTS_ON_PAGE)
        
        
        
        queue_name = self.__saved_queues[int(item_id)-1]["name"]
        embed.set_author(name = f"#{item_id} Queue \'{queue_name}\'",icon_url = self.__member.avatar.url if self.ctx.guild.icon else "https://camo.githubusercontent.com/10a3f498d105f35e3547b033f0a7bcbc06fa8c837792b50954234b37e1a039bc/68747470733a2f2f6170692e616c6578666c69706e6f74652e6465762f636f6c6f722f696d6167652f333633393346")
        view = self.view
        
        
        back = nextcord.ui.Button(emoji='🚪')
        del_queue = nextcord.ui.Button(emoji='❌')
        play_queue = nextcord.ui.Button(emoji='▶️')
        left = nextcord.ui.Button(label='◀️',row=2)
        right = nextcord.ui.Button(label='▶️',row=2)
        
        
        async def del_queue_callback(interaction):
            indexes = {x["name"]: i for i,x in enumerate(self.__saved_queues)}
            self.queues.update_one({"_id": self.__member.id},{"$pull": {"queues": {"_id": indexes[queue_name]}}})
            
            if (self.__queues_lenth - 1) == 0:
                await interaction.message.edit(content = '**:x: You haven`t any saved queues**')    
            else:
                self.page = 1
                await interaction.message.edit(embed = self._get_embed(0,self._ELEMENTS_ON_PAGE),view = self.view)
        

        async def load_queue(interaction):
            await self.join_to_channel(self,interaction,_from_queues = True)
            if self.ctx.guild.voice_client:
                self.queue_add(self.ctx.guild,self.__saved_queues[index]["items"])
                await interaction.message.edit('**:white_check_mark: Queue loaded**')
            else:
                self.page = 1
                await interaction.message.edit(embed = self._get_embed(0,self._ELEMENTS_ON_PAGE),view = self.view)


        async def back_callback(interaction):
            self.page = 1
            await interaction.message.edit(embed = self._get_embed(0,self._ELEMENTS_ON_PAGE),view = self.view)
                
         
        left.callback = queue._left_callback
        right.callback = queue._right_callback
        back.callback = back_callback
        del_queue.callback = del_queue_callback
        play_queue.callback = load_queue
        
        view.add_item(play_queue)
        view.add_item(back)
        view.add_item(del_queue)
        if queue_lenth > queue._ELEMENTS_ON_PAGE:
            START,STOP = self._calculate_shown_goods(queue.page)
            view.add_item(left)
            view.add_item(right)
            
        
        await interaction.message.edit(embed = embed,view = view)
        

    def _calculate_shown_goods(self,page):
        START = 0
        if (page > 1):
            START = self._ELEMENTS_ON_PAGE // (page - 1)
    
        STOP = START + self._ELEMENTS_ON_PAGE
        return (START, STOP)
    
    
    async def _left_callback(self,interaction):
        self.page -= 1
        if (self.page < 1):
            self.page = 1
        
        START, STOP = self._calculate_shown_goods(self.page)
        return await interaction.message.edit(embed = self._get_embed(START, STOP),view = self.view)
    
    
    async def _right_callback(self,interaction):
        self.page += 1
        if (self.page < 1):
            self.page = 1
        elif (self.page + 1) > self._PAGES:
            self.page = self._PAGES
        

        START, STOP = self._calculate_shown_goods(self.page)
        return await interaction.message.edit(embed = self._get_embed(START, STOP),view = self.view)
    

    async def send_queue(self):
        view = self.view
        if self.__queues_lenth > self._ELEMENTS_ON_PAGE: 
            START,STOP = self._calculate_shown_goods(self.page)
            await self.ctx.send(embed = self._get_embed(START,STOP),view = view)
        else:
            await self.ctx.send(embed = self._get_embed(0,self._ELEMENTS_ON_PAGE),view = view)

def setup(bot):
  bot.add_cog(Music(bot))