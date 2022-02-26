import pymongo
import nextcord
from nextcord.ext import commands
import json






class Settings(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.cluster = pymongo.MongoClient("mongodb+srv://tEST:sAHmVYepRa3YoW3J@cluster0.zlpox.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        self.db = self.cluster["songs"]
        self.premium_users = self.db["premium_users"]
      


    # @commands.Cog.listener()
    # async def on_command_error(self,ctx,error):
    #     print(error)
    #     if isinstance(error,nextcord.ext.commands.MissingPermissions):  
    #         await ctx.send('**:warning: You don`t have enough permisions**')
    #     elif isinstance(error,nextcord.ext.commands.errors.ChannelNotFound): 
    #         await ctx.send('**:x: It must be voice channel**')
        
    

    @commands.Cog.listener()
    async def on_ready(self):
        async for guild in self.bot.fetch_guilds():
            with open('prefix.json','r') as f:
                prefix = json.load(f)

            if str(guild.id) not in prefix:
                print(guild.id)
                prefix[str(guild.id)] = '$'
                
                with open('prefix.json','w') as f:
                        json.dump(prefix,f,indent = 4)
            
            with open('embeds_channel.json','r') as f:
                channels = json.load(f)

            if str(guild.id) not in channels:
                channels[str(guild.id)] = None
                
                with open('embeds_channel.json','w') as f:
                    json.dump(channels,f,indent = 4)

            
            with open('settings.json','r') as f:
                settings = json.load(f)

        
            if str(guild.id) not in settings: 
                settings[str(guild.id)] = {
                    "delete_msg": False,
                    "send_embeds": False,
                    "effect": None,
                    "blacklist": []
                }
                
                with open('settings.json','w') as f:
                    json.dump(settings,f,indent = 4)


    @commands.Cog.listener()
    async def on_guild_join(self,guild):
        with open ('prefix.json','r') as f:
            prefixes = json.load(f)
        
        prefixes[str(guild.id)] = '$'
        
        
        with open('prefix.json','w') as f:
            json.dump(prefixes,f,indent = 4)
        
        
        with open ('settings.json','r') as f:
            settings = json.load(f)
        
        
        settings[str(guild.id)] = {
                "delete_msg": False,
                "send_embeds": False,
                "effect": None,
                "blacklist": []
        }
        
        with open('settings.json','w') as f:
            json.dump(settings,f,indent = 4)
        
        
        with open('embeds_channel.json','r') as f:
            guilds = json.load(f)
            
        guilds[str(guild.id)] = None
            
        
        with open('embeds_channel.json','w') as f:
            json.dump(guilds,f,indent = 4)

    @commands.Cog.listener()
    async def on_guild_remove(self,guild):
        if guild.name:
            with open ('prefix.json','r') as f:
                prefixes = json.load(f)
            
            prefixes.pop(str(guild.id))
            
            with open ('prefix.json','w') as f:
                json.dump(prefixes,f,indent = 4)
            
            with open ('settings.json','r') as f:
                settings = json.load(f)
            
            settings.pop(str(guild.id))
            
            with open ('settings.json','w') as f:
                json.dump(settings,f,indent = 4)
            
            with open('embeds_channel.json','r') as f:
                guilds = json.load(f)
            
            guilds.pop(str(guild.id))
            
            with open('embeds_channel.json','w') as f:
                json.dump(guilds,f,indent = 4)
    

    @commands.Cog.listener()
    async def on_command_completion(self,ctx):
        with open ('settings.json','r') as f:
            settings = json.load(f)
        setting = settings[str(ctx.guild.id)]
        if setting['delete_msg']:
            await ctx.message.delete()
        
    
    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.has_permissions(manage_messages = True)
    @commands.command()
    async def delete_commands(self,ctx):
        with open ('settings.json','r') as f:
            settings = json.load(f)
        
        setting = settings[str(ctx.guild.id)]
        if setting['delete_msg']:
            setting['delete_msg'] = False
            await ctx.send('**:white_check_mark: Message delete disabled**')
        elif not setting['delete_msg']:
            setting['delete_msg'] = True
            await ctx.send('**:white_check_mark: Message delete enabled**')
          
        settings[str(ctx.guild.id)] = setting
        with open('settings.json','w') as f: 
            json.dump(settings,f,indent = 4)
    
    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.has_permissions(manage_channels = True)
    @commands.command()
    async def send_embeds(self,ctx,channel:nextcord.TextChannel = None):
        with open('embeds_channel.json','r') as f:
            guilds = json.load(f)
        
        with open('settings.json','r') as f:
            settings = json.load(f)
        
        setting = settings[str(ctx.guild.id)]
        
        if setting['send_embeds'] and channel:
            await ctx.send(f'**:warning: Embed messages already enabled and will be sent in {ctx.guild.get_channel(guilds[str(ctx.guild.id)]).mention}**')
        
        if setting['send_embeds'] and channel is None:
            setting['send_embeds'] = False
            guilds[str(ctx.guild.id)] = None
            await ctx.send(f'**:white_check_mark: Embed messages dissabled**')
        elif not setting['send_embeds'] and channel:
            setting['send_embeds'] = True
            guilds[str(ctx.guild.id)] = channel.id
            await ctx.send(f'**:white_check_mark: Embed messages will be sent in {channel.mention}**')
        
        settings[str(ctx.guild.id)] = setting
        
        with open('embeds_channel.json','w') as f:
            json.dump(guilds,f,indent = 4)
        with open('settings.json','w') as f:
            json.dump(settings,f,indent = 4)

    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.has_permissions(administrator = True)
    @commands.command()
    async def setprefix(self,ctx,prefix):
        with open('prefix.json','r') as f:
            prefixes = json.load(f)
             
        prefixes[str(ctx.guild.id)] = prefix
        
        with open('prefix.json','w') as f:
            json.dump(prefixes,f,indent = 4)
        message = await ctx.send(f'Prefix changed to ``{prefix}``')
        await message.add_reaction('❌')
        await self.bot.wait_for('reaction_add',check = lambda r,u : r != '❌'and u.id != ctx.guild.me.id)
        await message.delete()

    
    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command(aliases = ['addeffect','addeff'])
    async def apply_effect(self,ctx,effect:str):
        if not self.premium_users.find_one({"_id": ctx.author.id}):
            await ctx.send('**:x: This is premium command**')
        else:
            effect_list = ['reverse_audio','bass_boost','night_core','8D','clear','cristalizte','tremolo','mcompand','gate','flanger','vibrato','vaporwave','karaoke']
            if effect in effect_list:
                with open('settings.json','r') as f:
                    settings = json.load(f) 
                
                setting = settings[str(ctx.guild.id)]
                setting["effect"] = effect
                settings[str(ctx.guild.id)] = setting
                    
                with open('settings.json','w') as f:
                    json.dump(settings,f,indent = 4)
            
                await ctx.send(f'**:white_check_mark: Effect `{effect}` has been applyed**')
            else:
                await ctx.send(f'**:x: Invalid effect name use `efhelp` command to get list of effect names**')
    
    
    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command(aliases = ['removeeffect','remeff'])
    async def remove_effect(self,ctx):
        premium_user = self.premium_users.find_one({"_id": ctx.author.id})
        if not premium_user:
            await ctx.send('**:x: This is premium command**')
        else:
            with open('settings.json','r') as f:
                settings = json.load(f)
                
            setting = settings[str(ctx.guild.id)]
            current_effect = setting["effect"]
            if current_effect is None:
                return await ctx.send(f'**:warning: No effect to remove**') 
            else:
                setting["effect"] = None
                settings[str(ctx.guild.id)] = setting
                
            with open('settings.json','w') as f:
                json.dump(settings,f,indent = 4)
            
            await ctx.send(f'**:white_check_mark: Effect `{current_effect}` has been removed**')
        
    @commands.cooldown(1,2, commands.BucketType.user)
    @commands.command(name = 'addblacklist')
    @commands.has_permissions(manage_channels = True)
    async def add_channel_to_blacklist(self,ctx,channel: nextcord.VoiceChannel):
        with open('settings.json','r') as f:
            settings = json.load(f)
    
        setting = settings[str(ctx.guild.id)]
        
        if channel.type != nextcord.ChannelType.voice or channel.type != nextcord.ChannelType.stage_voice:
            await ctx.send(f'**:x: Channel must be voice or stage voice type**')
        elif channel.id not in setting["blacklist"]:
            setting["blacklist"].append(channel.id)
            settings[str(ctx.guild.id)] = setting
        else:
            return await ctx.send(f'**:warning:  Channel {channel.mention} already in blacklist**')
        with open('settings.json','w') as f:
            json.dump(settings,f,indent = 4)

        await ctx.send(f'**:white_check_mark: Channel {channel.mention} in blacklist**')
    
    
    
            
       
    @commands.cooldown(1,2, commands.BucketType.user)
    @commands.command(name = 'remblacklist')
    @commands.has_permissions(manage_channels = True)
    async def remove_channel_from_blacklist(self,ctx,channel: nextcord.VoiceChannel):
        with open('settings.json','r') as f:
            settings = json.load(f)
    
        setting = settings[str(ctx.guild.id)]
        if channel.id in setting["blacklist"]:
            setting["blacklist"].remove(channel.id)
        else:
            return await ctx.send(f'**:x: Channel {channel.mention} isn`t in blacklist**')
        settings[str(ctx.guild.id)] = setting

        with open('settings.json','w') as f:
            json.dump(settings,f,indent = 4)
    
        await ctx.send(f'**:white_check_mark: Channel {channel.mention} removed from blacklist**')


def setup(bot):
  bot.add_cog(Settings(bot))