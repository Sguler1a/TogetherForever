import os
import logging
from datetime import datetime, time
import discord
from discord.ext import commands, tasks
import pytz
from dotenv import load_dotenv

from src.google_sheets_api import GoogleSheetsFetcher
from src.generator import MessageGenerator

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load Environment Variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

TIMEZONE_STR = os.getenv("TIMEZONE", "America/Toronto")
SCHEDULER_TIME = os.getenv("SCHEDULER_TIME", "08:00")

# Parse scheduler time
try:
    hourStr, minuteStr = SCHEDULER_TIME.split(":")
    tz = pytz.timezone(TIMEZONE_STR)
    # Using python timezone object for tasks.loop
    daily_time = time(hour=int(hourStr), minute=int(minuteStr), tzinfo=tz)
except Exception as e:
    logger.error(f"Failed to parse time {SCHEDULER_TIME}: {e}")
    # Default fallback
    daily_time = time(hour=8, minute=0, tzinfo=pytz.timezone("America/Toronto"))

# Initialize clients
data_fetcher = GoogleSheetsFetcher(
    credentials_path=GOOGLE_CREDENTIALS_PATH, 
    sheet_id=GOOGLE_SHEET_ID, 
    timezone_str=TIMEZONE_STR
)
message_generator = MessageGenerator(api_key=GEMINI_API_KEY)

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def run_daily_workflow():
    """Fetches data from Google Sheets, runs it through Gemini, and returns the string message."""
    logger.info("Starting daily workflow extraction...")
    try:
        data = data_fetcher.fetch_all_data()
        msg = message_generator.generate_daily_message(data)
        return msg
    except Exception as e:
        logger.error(f"Workflow error: {e}")
        return "Good morning! ☀️ Something went slightly wrong fetching your data today, but I hope you both have a fantastic day! ❤️"

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    if not daily_checkin_loop.is_running():
        daily_checkin_loop.start()

@bot.command(name="today")
async def today_manual_trigger(ctx):
    """Manual trigger to force a send in the channel"""
    logger.info(f"Manual !today trigger invoked by {ctx.author}")
    await ctx.send("Fetching today's cutesy check-in! Give me a second... ✨")
    
    msg = await run_daily_workflow()
    await ctx.send(msg)

@tasks.loop(time=daily_time)
async def daily_checkin_loop():
    logger.info("Executing scheduled daily check-in loop.")
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        msg = await run_daily_workflow()
        await channel.send(msg)
    else:
        logger.error(f"Could not find Discord channel with ID: {DISCORD_CHANNEL_ID}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("No DISCORD_TOKEN provided. Cannot start.")
    else:
        bot.run(DISCORD_TOKEN)
