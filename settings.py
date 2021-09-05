
import discord
from discord.ext import commands
import json






class Settings(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
   

    @commands.Cog.listener()
    async def on_command_error(self,ctx,error):
        if isinstance(error,discord.ext.commands.MissingPermissions):  
            await ctx.send('**:warning: You don`t have enough permisions**')
    

    @commands.Cog.listener()
    async def on_ready(self):
        async for guild in self.bot.fetch_guilds():
            with open('prefix.json','r') as f:
                prefix = json.load(f)
        
            if guild.id not in prefix.values():
                prefix[str(guild.id)] = '$'
                
                with open('prefix.json','w') as f:
                        json.dump(prefix,f,indent = 4)
            
            with open('embeds_channel.json','r') as f:
                channels = json.load(f)
        
            if guild.id not in channels.values():
                channels[str(guild.id)] = None
                
                with open('embeds_channel.json','w') as f:
                        json.dump(channels,f,indent = 4)

            
            with open('settings.json','r') as f:
                settings = json.load(f)
        
            if guild.id not in settings.values():
                
                settings[str(guild.id)] = {
                    "delete_msg": False,
                    "send_embeds": False
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
                "send_embeds": False
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
        with open ('prefix.json','r') as f:
            prefixes = json.load(f)
        
        prefixes.pop(str(guild.id))
        
        with open ('prefix.json','w') as f:
            json.dump(prefixes,f,indent = 4)
        
        with open ('settings.json','r') as f:
            prefixes = json.load(f)
        
        prefixes.pop(str(guild.id))
        
        with open ('settings.json','w') as f:
            json.dump(prefixes,f,indent = 4)
        
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
    
    @commands.has_permissions(manage_messages = True)
    @commands.command()
    async def send_embeds(self,ctx,channel:discord.TextChannel = None):
        
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



def setup(bot):
  bot.add_cog(Settings(bot))