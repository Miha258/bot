
import io
from os import name
import discord
import pymongo
import requests
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from spotify import *
import json
from lyrics_extractor import SongLyrics


class Chat(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.cluster = pymongo.MongoClient("mongodb+srv://tEST:sAHmVYepRa3YoW3J@cluster0.zlpox.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        self.db = self.cluster["songs"]
        self.collection = self.db["songs"]
        self.users = self.db["users"]
    
    @commands.Cog.listener()
    async def on_ready(self):
      async for guild in self.bot.fetch_guilds():
        async for member in guild.fetch_members():
          if self.users.count_documents({"_id": member.id}) == 0 and not member.bot:
            self.users.insert_one({"_id": member.id,"bef_track_id" : None})

    @commands.Cog.listener()
    async def on_member_join(self,member):
        if self.users.count_documents({"_id": member.id}) == 0 and not member.bot:
          self.collection.insert_one({"_id": member.id,"bef_track_id" : None})
    
   
    @commands.Cog.listener()
    async def on_member_remove(self,member):
        if self.users.count_documents({"_id": member.id}) == 0 and not member.bot:
          self.users.delete_one({"_id": member.id})
      
    
    @commands.Cog.listener()
    async def on_member_ban(self,member):
        if self.users.count_documents({"_id": member.id}) == 1: self.users.delete_one({"_id": member.id})
          
    
    @commands.Cog.listener()
    async def on_guild_join(self,guild):
        async for member in guild.fetch_members():
          if self.users.count_documents({"_id": member.id}) == 0: self.collection.insert_one({"_id": member.id,"bef_track_id" : None})
    
          
        
    @commands.Cog.listener()
    async def on_member_update(self,before,after):
        if discord.activity.Spotify in list(map(type,after.activities)):
          af_activ = after.activity if len(after.activities) < 2 or len(after.activities) < 3 else list(filter(lambda act:type(act) == discord.activity.Spotify,after.activities))[0]
          if self.users.find_one({"_id": after.id})["bef_track_id"] != af_activ.track_id or self.users.find_one({"_id": after.id})["bef_track_id"] is None:
            self.users.update_one({"_id": after.id},{"$set":{"bef_track_id" : str(af_activ.track_id)}})
            spot = af_activ
            avatar = Image.open(requests.get(spot.album_cover_url, stream=True).raw).convert('RGBA')
            spotify = Image.open(requests.get('https://cdn.discordapp.com/attachments/815640791652499486/821070476909477928/Spotify.PNG', stream=True).raw).convert('RGBA')
            avatar = avatar.resize((450,450))
            mask = Image.new('L',(1500,1500),0)
            draw = ImageDraw.Draw(mask)
            idraw = ImageDraw.Draw(spotify)
            headline = ImageFont.truetype("font.ttf", size=70)
            headline2 = ImageFont.truetype('font.ttf', size=40)
            idraw.text((570, 50), f'Track', font=headline2, fill='#FFFFFF')
            idraw.text((570, 110), f'{spot.title if len(spot.title) < 27 else spot.title[:27] + "..."}', font=headline, fill='#FFFFFF')
            idraw.text((570, 210), f'Album', font=headline2, fill='#FFFFFF')
            idraw.text((570, 270), f'{spot.album if len(spot.album) < 27 else spot.album[:27] + "..."}', font=headline, fill='#FFFFFF')
            idraw.text((570, 370), f'Author:{spot.artist}' if len(spot.artists) == 1 else f'Authors: {", ".join(spot.artists)[:35] if len(", ".join(spot.artists)) < 35 else ", ".join(spot.artists)[:35] + "..."}',font=headline2,fill='#A7A7A7')
            idraw.text((570, 470), f"{spot.created_at}" [:-15], font=headline2, fill='#FFFFFF')
            idraw.text((570, 570), f"Listener: {after}",font=headline2, fill='#FFFFFF')
            draw.ellipse((0,0) + (1500,1500),fill = 255)
            spotify = spotify.resize((1920,640))
            spotify.paste(avatar,(50,50),avatar)
           
          
            
            
            with open('embeds_channel.json','r') as f:
              guilds = [guild for guild in self.bot.guilds if after in guild.members]
              guilds_channels = json.load(f)
            
            
            for guild in guilds:
              _buffer = io.BytesIO()
              spotify.save(_buffer,"png")
              _buffer.seek(0)
              channel_id = guilds_channels[str(guild.id)]
              if channel_id is not None:
                channel = discord.utils.get(guild.channels,id = channel_id)
                await channel.send(file = discord.File(fp = _buffer,filename = f'spotify-{guild.id}.png'))
                self.collection.insert_one({"_id": af_activ.track_id,"song_auditions" : 1,"title" : af_activ.title,"guild_id" : after.guild.id,"authors" : af_activ.artists}) if self.collection.count_documents({"_id": af_activ.track_id}) == 0 else self.collection.update_one({"_id": af_activ.track_id},{"$inc":{"song_auditions" : 1}})


      
              
                            
                  
    @commands.command()
    async def toptracks(self,ctx):
        embed = discord.Embed(color = discord.Color.green())
        songs = list(self.collection.find({"guild_id" : ctx.guild.id},limit = 10).sort("song_auditions",-1))
        i = 0
        
        for song in songs:
          i += 1
          embed.add_field(name = f'#{i} {", ".join(song["authors"])} - {song["title"]}',value = f'Auditions: **{song["song_auditions"]}**',inline = False)
        embed.set_author(name = f'The most popular tracks in {ctx.guild.name} guild',icon_url = ctx.guild.icon_url)
        embed.set_footer(text=f'Requested by: {ctx.author}', icon_url=ctx.author.avatar_url)
        await ctx.send(embed = embed) 


    @commands.command()
    async def searchtracks(self,ctx,*,name:str):
      try:
        embed = discord.Embed(title = f'On query \'{name}\' was found:',color = discord.Color.green())
        i = 0
        
        for name,url,autors in tracks(name):
            i += 1
            text = 'Author:' if len(autors) < 2 else 'Authors:'
            embed.add_field(name = f'**#{i}** {text} {", ".join(autors)}',value= f'**[{name}]({url})**',inline = False)
        embed.set_footer(text=f'Requested by: {ctx.author}', icon_url=ctx.author.avatar_url)
        await ctx.send(embed = embed)
      except TrackNotFound:
        await ctx.send('**:x:Tracks not found**')


    @commands.command()
    async def searchartist(self,ctx,*,name:str):
      try:
        embed = discord.Embed(title = f'Artist: {artist(name)[5]}',url = artist(name)[4],color = discord.Color.green())
        data = ''
        for track,url in artist(name)[0]:
          data += f'**[{track}]({url})**\n'
        
        embed.add_field(name = 'Followers:' ,value = f'**{artist(name)[1]}**')
        embed.add_field(name = 'Monthly listeners:' ,value = f'**{artist(name)[6]}**')
        if data:
          embed.add_field(name = 'Albums:',value = data)
        if artist(name)[3]:
          embed.add_field(name = 'Genres:' ,value = ', '.join(artist(name)[3]))
        
        embed.set_thumbnail(url = artist(name)[2])
        embed.set_footer(text=f'Requested by: {ctx.author}', icon_url=ctx.author.avatar_url)
        await ctx.send(embed = embed)
      
      except ArtistNotFound:
        await ctx.send('**:x:Artist not found**')

     
    @commands.command()
    async def searchplaylist(self,ctx,*,name:str):
      try:
        embed = discord.Embed(title = f'On query \'{name}\' was found:',color = discord.Color.green())
        i = 0

        for name,url,autors in get_user_playlists(name):
            i += 1
            embed.add_field(name = f'**#{i}** Author: {autors}',value= f'**[{name}]({url})**',inline = False)
        embed.set_footer(text=f'Requested by: {ctx.author}', icon_url=ctx.author.avatar_url)
        await ctx.send(embed = embed)
      except PlayListNotFound:
        await ctx.send('**:x:Playlist not found**')
    
    @commands.command()
    async def searchalbums(self,ctx,*,name:str):
      try:
        embed = discord.Embed(title = f'On query \'{name}\' was found:',color = discord.Color.green())
        i = 0
        for name,url,autors in get_user_playlists(name):
            i += 1
            embed.add_field(name = f'**#{i}** Author: {autors}',value= f'**[{name}]({url})**',inline = False)
        embed.set_footer(text=f'Requested by: {ctx.author}', icon_url=ctx.author.avatar_url)
        await ctx.send(embed = embed)
      except PlayListNotFound:
        await ctx.send('**:x:Playlist not found**')
    
    
    @commands.command(aliases = ['l','lyric'])
    async def get_lyric(self,ctx,url:str = None):
        try:
            track_name = ", ".join(get_track_info(url)[2]) + ' - ' + get_track_info(url)[1]
            print(track_name)
            track_image = get_track_info(url)[4]
            extract_lyrics = await self.bot.loop.run_in_executor(None,lambda:SongLyrics('AIzaSyCyY2Kzm14tJ5o8ZaeojB8jZI8spOoumYw','11ad9a21977f60462'))
        except TrackNotFound:
            await ctx.send('**:x: Track not found**')
        
        else:
            lyric = extract_lyrics.get_lyrics(track_name)
            embed = discord.Embed(title = f'{lyric["title"]}',description = lyric["lyrics"])
            embed.set_thumbnail(url = track_image)
            await ctx.send(embed = embed)



def setup(bot):
  bot.add_cog(Chat(bot))
    

