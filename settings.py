import discord
from discord.ext import commands
import json

class Settings(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_guild_join(guild):
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
    async def on_guild_remove(guild):
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
            await ctx.send(':white_check_mark:Message delete enabled')
        elif not setting['delete_msg']:
            setting['delete_msg'] = True
            await ctx.send(':white_check_mark:Message delete disabled')
        settings[str(ctx.guild.id)] = setting
        with open('settings.json','w') as f:
            json.dump(settings,f,indent = 4)
    
    @commands.command()
    async def send_embeds(self,ctx,channel:discord.TextChannel = None):
        with open('embeds_channel.json','r') as f:
            guilds = json.load(f)
            
        guilds[str(ctx.guild.id)] = channel.id
            
        with open('embeds_channel.json','w') as f:
            json.dump(guilds,f,indent = 4)
    
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