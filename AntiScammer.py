#AntiScammer from ABC Discord BitcoinJake09 7/4/2023
import discord
import json
import asyncio
from discord.ext import commands, tasks
from vars import TOKEN, ADMIN_MOD_IDS, LOGS_CHANNEL_ID

# Token and file paths
BANNED_STRINGS_FILE = 'banned_strings.json'  # JSON file path for banned strings
BANNED_NAMES_FILE = 'banned_names.json'  # JSON file path for banned names
ALLOWED_LINKS_FILE = 'allowed_links.json'  # JSON file path for allowed links
MOD_IDS_FILE = 'mod_ids.json'  # JSON file path for MOD_IDs
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
logs_channel = None
changename_channel = None
banned_strings = []
banned_names = []
allowed_links = []

def load_banned_strings():
    with open(BANNED_STRINGS_FILE, 'r') as file:
        data = json.load(file)
        return data['banned_strings']

def load_banned_names():
    with open(BANNED_NAMES_FILE, 'r', encoding='utf-8') as file:  # Specify encoding here
        data = json.load(file)
        return data['banned_names']


def load_allowed_links():
    with open(ALLOWED_LINKS_FILE, 'r') as file:
        data = json.load(file)
        return data['allowed_links']

def load_mod_ids():
    try:
        with open(MOD_IDS_FILE, 'r') as file:
            data = json.load(file)
            return data['mod_ids']
    except FileNotFoundError:
        return []  # Return an empty list if the file does not exist

def update_mod_ids_file(mod_ids):
    with open(MOD_IDS_FILE, 'w') as file:
        json.dump({"mod_ids": mod_ids}, file, indent=4)


def update_json_file(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


@bot.event
async def on_ready():
    print(f'Bot is connected as {bot.user}')
    global logs_channel, banned_strings, changename_channel, banned_names, allowed_links
    logs_channel = bot.get_channel(LOGS_CHANNEL_ID)
    if logs_channel is None:
        print(f'Logs channel with ID {LOGS_CHANNEL_ID} not found. Please check the ID.')
    banned_strings = load_banned_strings()
    banned_names = load_banned_names()
    allowed_links = load_allowed_links()
    await log_action('AntiScammer is Enabled')

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
                await log_action(f'{message.author}(Triggered Bot: {banned_string}): message was deleted because it contained potential scam. (Message deleted: {content})')
                await message.delete()
                break

    # Check for allowed links
    if "http" in content:
        if any(link in content for link in allowed_links):
            await bot.process_commands(message)
        else:
            await log_action(f'only specific links are allowed: {member.display_name} (ID: {member.id}) (Message: {message.content})')
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
    await changename_channel.send(f'{user.mention}, your display name violates our rules. Please change it within 5 minutes or you will be kicked.')
    await asyncio.sleep(5 * 60)  # Wait for 5 minutes
    guild = user.guild
    member = guild.get_member(user.id)
    if member.display_name.lower() in [banned_name.lower() for banned_name in banned_names]:
        await kick_user(member)

async def kick_user(member):
    await member.kick(reason='Banned name detected')

@bot.command()
@commands.has_permissions(administrator=True)
async def add_banned_name(ctx, *, name):
    global banned_names
    if name.lower() not in [n.lower() for n in banned_names]:  # Case-insensitive check
        banned_names.append(name)
        update_json_file(BANNED_NAMES_FILE, {"banned_names": banned_names})
        await ctx.send(f"Banned name added: {name}")
    else:
        await ctx.send("This name is already banned.")

@bot.command()
@commands.has_permissions(administrator=True)
async def remove_banned_name(ctx, *, name):
    global banned_names
    # Perform a case-insensitive removal
    banned_names_lower = [n.lower() for n in banned_names]
    if name.lower() in banned_names_lower:
        # Remove the name based on its case-insensitive match
        name_to_remove = banned_names[banned_names_lower.index(name.lower())]
        banned_names.remove(name_to_remove)
        update_json_file(BANNED_NAMES_FILE, {"banned_names": banned_names})
        await ctx.send(f"Banned name removed: {name}")
    else:
        await ctx.send("This name was not in the banned names.")

@bot.command()
@commands.has_permissions(administrator=True)
async def add_allowed_link(ctx, link):
    global allowed_links
    if link not in allowed_links:
        allowed_links.append(link)
        update_json_file(ALLOWED_LINKS_FILE, {"allowed_links": allowed_links})
        await ctx.send(f"Link added to allowed links: {link}")
    else:
        await ctx.send("This link is already allowed.")

@bot.command()
@commands.has_permissions(administrator=True)
async def remove_allowed_link(ctx, link):
    global allowed_links
    if link in allowed_links:
        allowed_links.remove(link)
        update_json_file(ALLOWED_LINKS_FILE, {"allowed_links": allowed_links})
        await ctx.send(f"Link removed from allowed links: {link}")
    else:
        await ctx.send("This link was not in the allowed links.")

@bot.command()
@commands.has_permissions(administrator=True)
async def add_banned_string(ctx, *, banned_string):
    global banned_strings
    if banned_string not in banned_strings:
        banned_strings.append(banned_string)
        update_json_file(BANNED_STRINGS_FILE, {"banned_strings": banned_strings})
        await ctx.send(f"Banned string added: {banned_string}")
    else:
        await ctx.send("This string is already banned.")

@bot.command()
@commands.has_permissions(administrator=True)
async def remove_banned_string(ctx, *, banned_string):
    global banned_strings
    if banned_string in banned_strings:
        banned_strings.remove(banned_string)
        update_json_file(BANNED_STRINGS_FILE, {"banned_strings": banned_strings})
        await ctx.send(f"Banned string removed: {banned_string}")
    else:
        await ctx.send("This string was not in the banned strings.")


@bot.command()
@commands.has_permissions(administrator=True)
async def check_banned_names(ctx):
    for member in ctx.guild.members:
        await check_member_banned_names(member)
    await log_action('Banned names check complete.')

@bot.command()
@commands.has_permissions(administrator=True)
async def add_mod_id(ctx, mod_id: int):
    global ADMIN_MOD_IDS
    if mod_id not in ADMIN_MOD_IDS:
        ADMIN_MOD_IDS.append(mod_id)
        update_mod_ids_file(ADMIN_MOD_IDS)
        await ctx.send(f"MOD_ID added: {mod_id}")
    else:
        await ctx.send("This MOD_ID is already added.")

@bot.command()
@commands.has_permissions(administrator=True)
async def remove_mod_id(ctx, mod_id: int):
    global ADMIN_MOD_IDS
    if mod_id in ADMIN_MOD_IDS:
        ADMIN_MOD_IDS.remove(mod_id)
        update_mod_ids_file(ADMIN_MOD_IDS)
        await ctx.send(f"MOD_ID removed: {mod_id}")
    else:
        await ctx.send("This MOD_ID was not found.")


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

async def changename_report(message):
    if changename_channel is not None:
        await changename_channel.send(message)
    else:
        print('changename channel not found. Unable to log action:', message)

bot.run(TOKEN)
