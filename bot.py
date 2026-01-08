import discord
from discord.ext import commands

TOKEN = "MTA2OTU5NjI1MTY4MDY2OTcwNg.GRTwuX.keLOkjvL6XkncBJv31MHGQhqLg1okA066CC4eU"
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"[INFO] Bot connected as {bot.user}")

bot.run(TOKEN)
