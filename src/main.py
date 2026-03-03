import os
import logging
from datetime import datetime, time
import discord
from discord.ext import commands, tasks
from discord import app_commands
import pytz
from dotenv import load_dotenv
from dateutil import parser as date_parser

from src.google_sheets_api import GoogleSheetsFetcher
from src.generator import MessageGenerator

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load Environment Variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))
DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
ADMIN_DISCORD_ID = os.getenv("ADMIN_DISCORD_ID")
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
message_generator = MessageGenerator(
    api_key=GEMINI_API_KEY,
    admin_discord_id=ADMIN_DISCORD_ID
)

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        if DISCORD_GUILD_ID:
            guild = discord.Object(id=DISCORD_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Slash commands synced to guild {DISCORD_GUILD_ID}")
        else:
            await self.tree.sync()
            logger.info("Slash commands synced globally.")

bot = MyBot(command_prefix="!", intents=intents)

async def run_daily_workflow():
    """Fetches data from Google Sheets, runs it through Gemini, and returns the string message."""
    logger.info("Starting daily workflow extraction...")
    try:
        data = data_fetcher.fetch_all_data()
        msg = message_generator.generate_daily_message(data)
        return msg
    except Exception as e:
        logger.error(f"Workflow error: {e}")
        admin_ping = f"<@{ADMIN_DISCORD_ID}>" if ADMIN_DISCORD_ID else "@doberkai"
        return f"Good morning! ☀️ Something went slightly wrong fetching your data today, but I hope you both have a fantastic day! ❤️ ({admin_ping} pls fix me!)"

def parse_date_to_string(date_input: str) -> str | None:
    try:
        parsed_date = date_parser.parse(date_input)
        return parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        return None

@bot.tree.command(name="addevent", description="Add an event to the shared Google Sheets database")
@app_commands.describe(name="The name of the event", date="The date of the event (e.g., YYYY-MM-DD or Month Day)", location="Optional location")
async def add_event_cmd(interaction: discord.Interaction, name: str, date: str, location: str = ""):
    parsed_date = parse_date_to_string(date)
    if not parsed_date:
        await interaction.response.send_message(f"Meow? >_< I couldn't quite understand the date format for '{date}'. Could you try giving it to me like YYYY-MM-DD or Month Day (e.g., March 1st)? :3", ephemeral=True)
        return
        
    success = data_fetcher.add_event(name, parsed_date, location)
    if success:
        await interaction.response.send_message(f"✨ Purr-fect! =^._.^= Successfully added event: **{name}** on {parsed_date}! :3", ephemeral=False)
    else:
        await interaction.response.send_message("❌ Oh no! >_< My paws slipped and I failed to add the event. Please check the logs!", ephemeral=True)

@bot.tree.command(name="addreminder", description="Add a reminder to the shared Google Sheets database")
@app_commands.describe(task="The task description", start_date="Start date", end_date="Optional end date")
async def add_reminder_cmd(interaction: discord.Interaction, task: str, start_date: str, end_date: str = ""):
    parsed_start = parse_date_to_string(start_date)
    if not parsed_start:
         await interaction.response.send_message(f"Meow? >_< I couldn't quite understand the start date format for '{start_date}'. Could you try giving it to me like YYYY-MM-DD or Month Day (e.g., March 1st)? :3", ephemeral=True)
         return
         
    parsed_end = ""
    if end_date:
        parsed_end = parse_date_to_string(end_date)
        if not parsed_end:
            await interaction.response.send_message(f"Meow? >_< I couldn't quite understand the end date format for '{end_date}'. Could you try giving it to me like YYYY-MM-DD or Month Day (e.g., March 1st)? :3", ephemeral=True)
            return

    success = data_fetcher.add_reminder(task, parsed_start, parsed_end)
    if success:
        await interaction.response.send_message(f"📝 Pawsome! Successfully added reminder: **{task}**! :3", ephemeral=False)
    else:
        await interaction.response.send_message("❌ Hiss! >_< I couldn't add that reminder. Check my logs!", ephemeral=True)

@bot.tree.command(name="addaffirmation", description="Add an affirmation to the shared Google Sheets database")
@app_commands.describe(quote="The affirmation quote")
async def add_affirmation_cmd(interaction: discord.Interaction, quote: str):
    success = data_fetcher.add_affirmation(quote)
    if success:
        await interaction.response.send_message(f"💖 Meow! Successfully added affirmation: \"{quote}\" =^._.^=", ephemeral=False)
    else:
        await interaction.response.send_message("❌ Oh nyooo >_< I failed to add the affirmation. Check the logs please!", ephemeral=True)

@bot.tree.command(name="addhealth", description="Add a relationship health question")
@app_commands.describe(question="The question to ask")
async def add_health_cmd(interaction: discord.Interaction, question: str):
    success = data_fetcher.add_health_question(question)
    if success:
        await interaction.response.send_message(f"🩺 Purr-fect! Successfully added relationshiphealth question: \"{question}\" :3", ephemeral=False)
    else:
        await interaction.response.send_message("❌ *Sad meow* >_< I failed to add the health question. Check the logs!", ephemeral=True)

@bot.tree.command(name="addactivity", description="Add an online activity")
@app_commands.describe(name="Activity name", length="Expected length of the activity")
@app_commands.choices(length=[
    app_commands.Choice(name="Short", value="Short"),
    app_commands.Choice(name="Long", value="Long")
])
async def add_activity_cmd(interaction: discord.Interaction, name: str, length: app_commands.Choice[str]):
    success = data_fetcher.add_online_activity(name, length.value)
    if success:
        await interaction.response.send_message(f"🎮 Pawsome job! Successfully added {length.value.lower()} activity: **{name}** =^._.^=", ephemeral=False)
    else:
        await interaction.response.send_message("❌ Oh whiskers! >_< I couldn't add the activity. Check my logs!", ephemeral=True)

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

@bot.command(name="upcoming")
async def upcoming_cmd(ctx):
    """Shows all future events and reminders."""
    logger.info(f"Manual !upcoming trigger invoked by {ctx.author}")
    await ctx.send("Fetching upcoming events and reminders... ✨")
    
    try:
        events = data_fetcher.get_events()
        reminders = data_fetcher.get_upcoming_reminders()
    except Exception as e:
        logger.error(f"Error fetching upcoming data: {e}")
        await ctx.send("Oh no! >_< I couldn't fetch the upcoming events and reminders. Please check the logs!")
        return

    if not events and not reminders:
        await ctx.send("There are no upcoming events or reminders! 🐾")
        return
        
    response = "🗓️ **Upcoming Events & Reminders** 🗓️\n\n"
    
    if events:
        response += "**Events:**\n"
        for idx, ev in enumerate(events, 1):
            date_str = ev.get('date', 'Unknown Date')
            response += f"{idx}. **{ev['title']}** - {date_str}\n"
        response += "\n"
        
    if reminders:
        response += "**Reminders:**\n"
        for idx, rm in enumerate(reminders, 1):
            date_start = rm.get('date_start', 'Unknown Date')
            date_end = rm.get('date_end', '')
            date_str = date_start
            if date_end and date_start != date_end:
                date_str += f" to {date_end}"
            response += f"{idx}. **{rm['title']}** - {date_str}\n"

    # Send in chunks to avoid discord limits
    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
    for chunk in chunks:
        await ctx.send(chunk)


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
