#AntiScammer from ABC Discord BitcoinJake09 7/4/2023
import discord
import json
from discord.ext import commands, tasks
from vars import TOKEN, ADMIN_MOD_IDS, LOGS_CHANNEL_ID, YOUR_GUILD_ID

#TOKEN = 'your_bot_token'
BANNED_STRINGS_FILE = 'banned_strings.json'  # JSON file path
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
logs_channel = None
banned_strings = []

def load_banned_strings():
    with open(BANNED_STRINGS_FILE, 'r') as file:
        data = json.load(file)
        return data['banned_strings']

@bot.event
async def on_ready():
    print(f'Bot is connected as {bot.user}')
    global logs_channel, banned_strings
    logs_channel = bot.get_channel(LOGS_CHANNEL_ID)
    if logs_channel is None:
        print(f'Logs channel with ID {LOGS_CHANNEL_ID} not found. Please check the ID.')
    banned_strings = load_banned_strings()
    await log_action(f'Hal is Watching')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()
    if len(content) > 1:
        await log_action(f'Checking: {content}')
    for banned_string in banned_strings:
        if banned_string in content:
            await log_action(f'Bot Triggered: {banned_string}')
            await message.delete()
            await message.channel.send(f'{message.author.mention}, your message was deleted because it contained potential scam.')
            await log_action(f'Message deleted: {message.content} (Author: {message.author})')
            break

    await bot.process_commands(message)

@tasks.loop(minutes=10)
async def check_banned_strings_updates():
    global banned_strings
    new_banned_strings = load_banned_strings()
    if banned_strings != new_banned_strings:
        banned_strings = new_banned_strings
        await log_action('Banned strings updated.')

@check_banned_strings_updates.before_loop
async def before_check_banned_strings_updates():
    await bot.wait_until_ready()

@tasks.loop(minutes=10)
async def check_username_changes():
    guild = bot.get_guild(YOUR_GUILD_ID)
    for member in guild.members:
        if member.id in ADMIN_MOD_IDS:
            # Check if the member's name matches any admin or mod name
            if member.display_name.lower() not in [name.lower() for name in ADMIN_MOD_NAMES]:
                # Handle the case where the member's name has been changed
                # You can implement the desired actions here, such as sending a warning or removing permissions
                await log_action(f'Username change detected: {member.display_name} (ID: {member.id})')

@check_username_changes.before_loop
async def before_check_username_changes():
    await bot.wait_until_ready()

async def log_action(message):
    if logs_channel is not None:
        await logs_channel.send(message)
    else:
        print('Logs channel not found. Unable to log action:', message)

bot.run(TOKEN)
