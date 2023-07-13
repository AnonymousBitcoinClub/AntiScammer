#AntiScammer from ABC Discord BitcoinJake09 7/4/2023
import discord
import json
import asyncio
from discord.ext import commands, tasks
from vars import TOKEN, ADMIN_MOD_IDS, LOGS_CHANNEL_ID, SCAMS_CHANNEL_ID

# Token and file paths
BANNED_STRINGS_FILE = 'banned_strings.json'  # JSON file path for banned strings
BANNED_NAMES_FILE = 'banned_names.json'  # JSON file path for banned names
ALLOWED_LINKS_FILE = 'allowed_links.json'  # JSON file path for allowed links
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
logs_channel = None
scams_channel = None
banned_strings = []
banned_names = []
allowed_links = []

def load_banned_strings():
    with open(BANNED_STRINGS_FILE, 'r') as file:
        data = json.load(file)
        return data['banned_strings']

def load_banned_names():
    with open(BANNED_NAMES_FILE, 'r') as file:
        data = json.load(file)
        return data['banned_names']

def load_allowed_links():
    with open(ALLOWED_LINKS_FILE, 'r') as file:
        data = json.load(file)
        return data['allowed_links']

@bot.event
async def on_ready():
    print(f'Bot is connected as {bot.user}')
    global logs_channel, banned_strings, scams_channel, banned_names, allowed_links
    logs_channel = bot.get_channel(LOGS_CHANNEL_ID)
    scams_channel = bot.get_channel(SCAMS_CHANNEL_ID)
    if logs_channel is None:
        print(f'Logs channel with ID {LOGS_CHANNEL_ID} not found. Please check the ID.')
    if scams_channel is None:
        print(f'Scam channel with ID {SCAMS_CHANNEL_ID} not found. Please check the ID.')
    banned_strings = load_banned_strings()
    banned_names = load_banned_names()
    allowed_links = load_allowed_links()
    await log_action('Hal is Watching')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()
    user = message.author

    if user.id in ADMIN_MOD_IDS:
        return

    if user.bot:
        return

    # Check for banned strings
    if len(content) > 1:
        for banned_string in banned_strings:
            if banned_string in content:
                await log_action(f'{message.author} Triggered Bot: {banned_string}')
                await message.delete()
                await scam_report(f'{message.author.mention}, your message was deleted because it contained potential scam. Message deleted: {content} (Author: {message.author})')
                break

    # Check for allowed links
    if "http" in content:
        if any(link in content for link in allowed_links):
            await bot.process_commands(message)
        else:
            await message.reply(f'{message.author.mention}, only specific links are allowed.')
            await message.delete()

@bot.event
async def on_member_join(member):
    check_banned_names(member)

@bot.event
async def on_member_update(before, after):
    if before.display_name != after.display_name:
        await check_banned_names(after)

async def check_banned_names(member):
    if member.id in ADMIN_MOD_IDS:
        return

    for banned_name in banned_names:
        if banned_name.lower() in member.display_name.lower():
            await log_action(f'Banned name detected: {member.display_name} (ID: {member.id})')
            await warn_user(member)
            break

async def warn_user(user):
    await scams_channel.send(f'{user.mention}, your display name violates our rules. Please change it within 5 minutes or you will be kicked.')
    await asyncio.sleep(5 * 60)  # Wait for 5 minutes
    guild = user.guild
    member = guild.get_member(user.id)
    if member.display_name.lower() in [banned_name.lower() for banned_name in banned_names]:
        await kick_user(member)

async def kick_user(member):
    await member.kick(reason='Banned name detected')

@bot.command()
@commands.has_permissions(administrator=True)
async def check_banned_names(ctx):
    for member in ctx.guild.members:
        await check_member_banned_names(member)
    await log_action('Banned names check complete.')

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
async def check_banned_names_updates():
    global banned_names
    new_banned_names = load_banned_names()
    if banned_names != new_banned_names:
        banned_names = new_banned_names
        await log_action('Banned names updated.')

@check_banned_names_updates.before_loop
async def before_check_banned_names_updates():
    await bot.wait_until_ready()

async def log_action(message):
    if logs_channel is not None:
        await logs_channel.send(message)
    else:
        print('Logs channel not found. Unable to log action:', message)

async def scam_report(message):
    if scams_channel is not None:
        await scams_channel.send(message)
    else:
        print('Scam channel not found. Unable to log action:', message)

bot.run(TOKEN)
