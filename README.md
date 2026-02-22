# Cutesy Couple's Daily Digest Bot

An automated Discord bot designed to keep couples connected by synthesizing daily updates from a shared Notion dashboard into a sweet, positive morning briefing using Google Gemini AI.

## Features

- 📅 **Smart Event Tracking:** Automatically pulls upcoming events and daily reminders from Notion databases.
- 💖 **Relationship Building:** Integrates daily affirmations, relationship check-in questions, and online activity ideas to keep things fresh.
- 🤖 **AI Synthesized Delivery:** Uses Google Gemini (1.5 Flash) to format data into a natural, cutesy, and positive morning message.
- ⏰ **Automated Scheduling:** Runs automatically at 08:00 AM (America/Toronto time) via `discord.ext.tasks`.
- 🐳 **Dockerized:** Fully containerized for easy deployment on free-tier cloud platforms (like Oracle Cloud).

## Tech Stack

- **Language:** Python 3.11
- **Discord Integration:** `discord.py`
- **Knowledge Base:** Notion API (v1)
- **AI engine:** Google Generative AI (`gemini-1.5-flash`)
- **Testing:** `pytest`
- **Deployment:** Docker & Docker Compose

## Notion Database Setup

The bot expects a single parent Notion page containing 5 specific inline databases. They must contain the following properties:

1. **"Events"** (Title: `Name`, Date: `Date`, Text: `Location`)
2. **"Reminders"** (Title: `Task`, Date: `Date`)
3. **"Affirmations"** (Title: `Quote`)
4. **"Relationship Health"** (Title: `Question`)
5. **"Online Activities"** (Title: `Name`, Select: `Length`)

_Note: You use as many extra columns as you want for your own organization (e.g. a "Notes" column)! The bot will only pull what it needs and ignore the rest._

## Installation & Local Development

1. Clone the repository:

```bash
git clone https://github.com/your-username/TogetherForever.git
cd TogetherForever
```

2. Duplicate `.env.example` to `.env` and fill in your API credentials:

```bash
cp .env.example .env
```

_(You will need a Discord Bot Token, a Notion Internal Integration Secret, and a Google AI Studio API Key)._

3. Run locally using Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

## Running Tests

To verify the Notion date filtering and Gemini generation logic without hitting the live APIs:

```bash
pytest tests/
```

## Need Help?

Want this bot set up for your own Discord server but don't want to deal with the coding and cloud hosting?

**Contact `doberkai` on Discord** and they can help set it up for you!
