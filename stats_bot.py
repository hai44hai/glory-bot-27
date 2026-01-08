import discord
from discord.ext import commands
import json, os

# =======================
# Config
# =======================
import csetup_stats as csetup  # TOKEN, GLORY_CHANNEL_ID, STATS_CHANNEL_ID
STATS_CHANNEL_ID = getattr(csetup, "STATS_CHANNEL_ID", csetup.GLORY_CHANNEL_ID)

# =======================
# Bot setup
# =======================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"
MSG_FILE = "stats_message.json"

data = {}
stats_message_id = None

# =======================
# Load/save functions
# =======================
def load_data():
    global data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_message_id():
    global stats_message_id
    if os.path.exists(MSG_FILE):
        with open(MSG_FILE, "r", encoding="utf-8") as f:
            stats_message_id = json.load(f).get("stats_message_id")
    else:
        stats_message_id = None

def save_message_id():
    global stats_message_id
    if stats_message_id:
        with open(MSG_FILE, "w", encoding="utf-8") as f:
            json.dump({"stats_message_id": stats_message_id}, f)

# =======================
# Keep names exactly as in server
# =======================
def clean_name(member):
    return member.display_name.strip()  # שמות בעברית, עם אימוג'ים, כפי שהם

def clean_all_names():
    for uid in data:
        # אין ניקוי – שמות נשארים כמו שהם
        pass

# =======================
# Update stats message
# =======================
async def update_stats_message():
    global stats_message_id
    await bot.wait_until_ready()
    channel = bot.get_channel(STATS_CHANNEL_ID)
    if not channel:
        print(f"[ERROR] Can't find channel with ID {STATS_CHANNEL_ID}")
        return

    # Top 10 users
    sorted_users = sorted(data.items(), key=lambda x: x[1]["count"], reverse=True)[:10]

    embed = discord.Embed(
        title="📊 Glory Stats – Live",
        description="Top collectors of Glory",
        color=discord.Color.blue()
    )

    if not sorted_users:
        embed.add_field(name="No data yet", value="Start sending '1' messages!", inline=False)
    else:
        for i, (uid, info) in enumerate(sorted_users, start=1):
            embed.add_field(name=f"{i}. {info['name']}", value=f"Glory: {info['count']}", inline=False)

    # Update existing message
    if stats_message_id:
        try:
            msg = await channel.fetch_message(stats_message_id)
            await msg.edit(embed=embed)
            return
        except discord.NotFound:
            stats_message_id = None
        except discord.Forbidden:
            print(f"[ERROR] Missing permissions to edit message in {channel.name}")
            return

    # Send new message if none exists
    try:
        msg = await channel.send(embed=embed)
        stats_message_id = msg.id
        save_message_id()
    except discord.Forbidden:
        print(f"[ERROR] Missing permissions to send messages in {channel.name}")

# =======================
# Events
# =======================
@bot.event
async def on_ready():
    load_data()
    load_message_id()
    clean_all_names()
    print(f"[INFO] Stats Bot connected as {bot.user}")
    await update_stats_message()

@bot.event
async def on_message(message):
    if message.author.bot:
        await bot.process_commands(message)
        return

    await bot.process_commands(message)

    if message.channel.id != csetup.GLORY_CHANNEL_ID:
        return
    if message.content.strip() != "1":
        return

    uid = str(message.author.id)
    if uid not in data:
        data[uid] = {"name": clean_name(message.author), "count": 0}
    else:
        data[uid]["name"] = clean_name(message.author)

    data[uid]["count"] += 1
    save_data()
    await update_stats_message()

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    if message.channel.id != csetup.GLORY_CHANNEL_ID:
        return
    if message.content.strip() != "1":
        return

    uid = str(message.author.id)
    if uid in data and data[uid]["count"] > 0:
        data[uid]["count"] -= 1
        save_data()
        await update_stats_message()

# =======================
# Admin commands
# =======================
@bot.command()
@commands.has_permissions(moderate_members=True)
async def reset(ctx, member: discord.Member):
    uid = str(member.id)
    if uid not in data:
        await ctx.send("❌ No data for this user")
        return
    data[uid]["count"] = 0
    save_data()
    await ctx.send(f"🔄 {member.mention}'s data has been reset")
    await update_stats_message()

@bot.command()
@commands.has_permissions(administrator=True)
async def resetall(ctx):
    data.clear()
    save_data()
    await ctx.send("🔥 All data has been reset")
    await update_stats_message()

# =======================
# Run bot
# =======================
bot.run(csetup.TOKEN)
