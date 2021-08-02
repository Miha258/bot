import discord
from discord.ext import commands
import os
import json




def get_prefix(bot,message):
    with open('prefix.json','r') as f:
        prefixes = json.load(f)
    
    return prefixes[str(message.guild.id)] 

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = get_prefix,intents = intents,activity = discord.Activity(name = '$play',type = discord.ActivityType.listening))
bot.remove_command('help')

for file in os.listdir('./'):
    if file.endswith('.py') and file != 'loader.py' and file != 'spotify.py':    
        bot.load_extension(f"{file[:-3]}")

@bot.event
async def on_ready():
    print('Im ready')

@bot.command()
async def ping(ctx):
    await ctx.send(embed = discord.Embed(description = f'**My ping: {round(bot.latency,1)} ms**',color = discord.Color.green()))

@bot.command(aliases = ['h','help'])
async def help_command(ctx):
    embed = discord.Embed(title = 'Help ℹ️',description = 'This commands will be useful',color = discord.Color.green())
    embed.add_field(name = '```Chat commands```',value =
        '`toptracks` - The most popular tracks among guild members\n\n'
        '`searchtracks` - Search tracks by name\n\n'
        '`searchplaylist` - Search playlist by name\n\n'
        '`searchartist` - Search artist by name\n\n'
        '`searchalbums` - Search albums by name\n\n'
        '`lyric` - Get lyric form spotify url\n'
        '`Usage: $lyric <url>`\n'
        '`Alias: l`\n'
    )
    
    
    embed.add_field(name = '```Music commands```',value =
        '`play` - Play audio from spotify url\n'
        '`Usage: $play <url>`\n'
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
    )

    embed.add_field(name = '```Settings commands```',value = 
    '`delete_commands` - Enable or disable deleting message with command\n\n'
    '`send_embeds` - Enable or disable sending embeds(if it enabled then in specific channel will be sent embed with current track info that member listens to)\n'
    '`Usage: $send_embeds <@channel>`\n\n'
    '`setprefix` - Set custom prefix in guild\n'
    '`Usage: $setprefix <prefix>`\n'
    )
    
    await ctx.send(embed = embed)
    
bot.run(os.environ['BOT_TOKEN'])
