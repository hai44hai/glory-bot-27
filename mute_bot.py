import discord
from discord.ext import commands
from datetime import datetime, timedelta
import csetup_mute as csetup  # מייבא את הקובץ הנכון

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
last_message_time = {}

@bot.event
async def on_ready():
    print(f"[INFO] Bot connected as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        await bot.process_commands(message)
        return

    await bot.process_commands(message)

    if message.channel.id != csetup.GLORY_CHANNEL_ID:
        return

    user_id = message.author.id
    now = datetime.utcnow()

    if message.content.strip() != "1":
        try:
            await message.delete()
        except:
            pass
        return

    if user_id in last_message_time:
        delta = (now - last_message_time[user_id]).total_seconds()
        if delta < csetup.COOLDOWN_SECONDS:
            try:
                await message.delete()
            except:
                pass
            until = discord.utils.utcnow() + timedelta(seconds=csetup.MUTE_SECONDS)
            try:
                await message.author.timeout(until, reason="Sent 1 too many times")
            except:
                pass
            if csetup.LOG_CHANNEL_ID:
                log_channel = bot.get_channel(csetup.LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(f"🔇 {message.author.mention} muted for spamming 1")
            return

    last_message_time[user_id] = now

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    try:
        await member.timeout(None, reason="Unmuted by command")
        await ctx.send(f"✅ {member.mention} unmuted successfully!")
    except:
        await ctx.send(f"❌ Cannot unmute {member.mention}, missing permissions.")
@bot.event
async def on_ready():
    print("Bot connected to Discord!")

bot.run(csetup.TOKEN)
