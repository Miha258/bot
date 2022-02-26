
import nextcord
from nextcord import guild
from genius import *
import pymongo
import requests
from nextcord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from spotify import *
import json
import io
import asyncio


class Chat(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.cluster = pymongo.MongoClient("mongodb+srv://tEST:sAHmVYepRa3YoW3J@cluster0.zlpox.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        self.db = self.cluster["songs"]
        self.collection = self.db["songs"]
        self.users = self.db["users"]
       
    
    @commands.Cog.listener()
    async def on_ready(self):
        all_users = [int(user) for user in self.users.find().distinct('_id')]
        user_not_in_db = [{"_id": member.id + member.guild.id,"bef_track_id" : None,"guild_id": member.guild.id} for member in self.bot.get_all_members() if not member.id + member.guild.id in all_users]
        if user_not_in_db:
            self.users.insert_many(user_not_in_db)
        
        
    @commands.Cog.listener()
    async def on_member_join(self,member):
        if self.users.count_documents({"_id": member.id + member.guild.id}) == 0 and not member.bot:
          self.users.insert_one({"_id": member.id + member.guild.id,"bef_track_id" : None,'guild_id': member.guild.id})
    
   
    @commands.Cog.listener()
    async def on_member_remove(self,member):
        if self.users.count_documents({"_id": member.id + member.guild.id}) == 0 and not member.bot:
          self.users.delete_one({"_id": member.id + member.guild.id,'guild_id': member.guild.id})
      

    @commands.Cog.listener()
    async def on_member_ban(self,guild, member):
        if self.users.count_documents({"_id": member.id + member.guild.id}) == 1:
          self.users.delete_one({"_id": member.id + member.guild.id,'guild_id': member.guild.id})
    

    @commands.Cog.listener()
    async def on_member_unban(self,guild,member):
        if self.users.count_documents({"_id": member.id + guild.id}) == 0:
          self.users.insert_one({"_id": member.id + guild.id,"bef_track_id" : None,'guild_id': guild.id})
    
    
    @commands.Cog.listener()
    async def on_guild_join(self,guild):
        all_users = [int(user) for user in self.users.find({'guild_id': guild.id}).distinct('_id')]
        users = [{"_id": member.id + guild.id,"bef_track_id" : None,'guild_id': guild.id} for member in guild.members if not member.id + member.guild.id in all_users]
        self.users.insert_many(users)


    @commands.Cog.listener()
    async def on_guild_remove(self,guild):
        if guild.name:
          self.users.delete_many({'guild_id': guild.id})
   

    @commands.Cog.listener()
    async def on_presence_update(self,before,after):
        if nextcord.activity.Spotify in list(map(type,after.activities)):
            af_activ = list(filter(lambda act:type(act) == nextcord.activity.Spotify,after.activities))[0]
            bef_activ = list(filter(lambda act:type(act) == nextcord.activity.Spotify,before.activities))
            bef_id =  bef_activ[0].track_id if len(bef_activ) > 0 else self.users.find_one({"_id": after.id + after.guild.id})["bef_track_id"]
            if bef_id != af_activ.track_id:
              await asyncio.sleep(1)
              self.users.update_one({"_id": after.id + after.guild.id},{"$set":{"bef_track_id" : af_activ.track_id}})
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
                guilds_channels = json.load(f)
              
              channel_id = guilds_channels[str(after.guild.id)]
              channel = nextcord.utils.get(after.guild.channels,id = channel_id)
              if channel:
                _buffer = io.BytesIO()
                spotify.save(_buffer,"png")
                _buffer.seek(0)
              
                await channel.send(file = nextcord.File(fp = _buffer,filename = f'spotify-{after.guild.id}.png'))
          
              self.collection.insert_one({"_id": af_activ.track_id+str(after.guild.id),"song_auditions" : 1,"title" : af_activ.title,"guild_id" : after.guild.id,"authors" : af_activ.artists}) if self.collection.count_documents({"_id": af_activ.track_id+str(after.guild.id),"guild_id": after.guild.id}) == 0 else self.collection.update_one({"_id": af_activ.track_id+str(after.guild.id),"guild_id": after.guild.id},{"$inc":{"song_auditions" : 1}})

    
    
    @commands.cooldown(1,1, commands.BucketType.user)                 
    @commands.command()
    async def toptracks(self,ctx):
        embed = nextcord.Embed(color = nextcord.Color.green())
        songs = list(self.collection.find({"guild_id" : ctx.guild.id},limit = 10).sort("song_auditions",-1))
        i = 0
        for song in songs:
          i += 1
          embed.add_field(name = f'#{i} {", ".join(song["authors"])} - {song["title"]}',value = f'Auditions: **{song["song_auditions"]}**',inline = False)
        embed.set_author(name = f'The most popular tracks in {ctx.guild.name} guild',icon_url = ctx.guild.icon.url if ctx.guild.icon else "https://camo.githubusercontent.com/10a3f498d105f35e3547b033f0a7bcbc06fa8c837792b50954234b37e1a039bc/68747470733a2f2f6170692e616c6578666c69706e6f74652e6465762f636f6c6f722f696d6167652f333633393346")
        await ctx.send(embed = embed) 

    @commands.cooldown(1,1, commands.BucketType.user)   
    @commands.command()
    async def searchtracks(self,ctx,*,name:str):
      try:
        embed = nextcord.Embed(title = f'On query \'{name}\' was found:',color = nextcord.Color.green())
        i = 0
        
        for name,url,autors in tracks(name):
            i += 1
            embed.add_field(name = f'**#{i}** {"Authors" if len(autors) > 1 else "Author"}: {", ".join(autors)}',value= f'**[{name}]({url})**',inline = False)
       
        await ctx.send(embed = embed)
      except TrackNotFound:
        await ctx.send('**:x: Tracks not found**')

    @commands.cooldown(1,1, commands.BucketType.user)   
    @commands.command()
    async def searchartist(self,ctx,*,name:str):
      try:
        embed = nextcord.Embed(title = f'Artist: {artist(name)[5]}',url = artist(name)[4],color = nextcord.Color.green())
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
        
        await ctx.send(embed = embed)
      
      except ArtistNotFound:
        await ctx.send('**:x: Artist not found**')

    @commands.cooldown(1,1, commands.BucketType.user)   
    @commands.command()
    async def searchplaylist(self,ctx,*,name:str):
      try:
        embed = nextcord.Embed(title = f'On query \'{name}\' was found:',color = nextcord.Color.green())
        i = 0

        for name,url,autors in get_user_playlists(name):
            i += 1
            embed.add_field(name = f'**#{i}** {"Authors" if len(autors) > 1 else "Author"}: {", ".join(autors)}',value= f'**[{name}]({url})**',inline = False)
        
        await ctx.send(embed = embed)
      except PlayListNotFound:
        await ctx.send('**:x: Playlist not found**')
    
    @commands.cooldown(1,1, commands.BucketType.user)   
    @commands.command()
    async def searchalbums(self,ctx,*,name:str):
      try:
        embed = nextcord.Embed(title = f'On query \'{name}\' was found:',color = nextcord.Color.green())
        i = 0
        for url,name,autors in albums(name):
            i += 1
            embed.add_field(name = f'**#{i}** {"Authors" if len(autors) > 1 else "Author"}: {", ".join(autors)}',value= f'**[{name}]({url})**',inline = False)
        await ctx.send(embed = embed)
      except PlayListNotFound:
        await ctx.send('**:x:Playlist not found**')
    
    @commands.cooldown(1,1, commands.BucketType.user)   
    @commands.command(aliases = ['l','lyric'])
    async def get_lyric(self,ctx,url:str = None):
        try:
            track_name = ", ".join(get_track_info(url,False)[1]) + ' - ' + get_track_info(url,False)[0]
            track_image = get_track_info(url,False)[2]
            url = await GeniusLyric().get_lyric(track_name)
            
        except TrackNotFound:
            await ctx.send('**:x: Track not found**')

        except LyricNotFound:
            await ctx.send('**:x: Lyrics not found**')
        else:
            embed = nextcord.Embed(title = f'Lyrics of \'{track_name}\'',url = url,color = nextcord.Color.green())
            embed.set_thumbnail(url = track_image)
            embed.set_footer(text = 'From Genius',icon_url='https://img.utdstc.com/icon/05d/36d/05d36d070ead729534565c1813a84aeb5299707c959a96be1687585aed1a4748')
            await ctx.send(embed = embed)
        


 
def setup(bot):
  bot.add_cog(Chat(bot))
    

