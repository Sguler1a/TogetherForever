from google import genai
import logging
import json
import random

logger = logging.getLogger(__name__)

class MessageGenerator:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        # Using 2.5 flash as previous versions are deprecated or unsupported
        self.model_name = 'gemini-2.5-flash'

    def generate_daily_message(self, notion_data: dict) -> str:
        # Check for empty state
        is_empty = all(len(items) == 0 for items in notion_data.values())
        
        system_instructions = (
            "You are a cutesy, bubbly, and positive bot for a private couple's Discord server. "
            "Your job is to send a simple, sweet morning briefing. "
            "Keep the message around 200 words. Use emojis. Be positive and loving, but not overly complex. "
            "Do not be sassy, just be simple and positive. "
            "You do not need to greet the users by name, just a general 'Good morning loves!' or similar is fine. "
            "Format the output for Discord Markdown."
        )

        if is_empty:
            prompt = (
                f"{system_instructions}\n\n"
                "There are no upcoming events, reminders, or specific check-in questions for today! "
                "Just wish them a wonderful day and give them a short, sweet relationship encouragement."
            )
        else:
            # Randomly select single items to prevent LLM primacy bias and ensure variety
            affirmations = notion_data.get('affirmations', [])
            selected_affirmation = random.choice(affirmations) if affirmations else None

            health_quests = notion_data.get('health', [])
            selected_health = random.choice(health_quests) if health_quests else None

            all_activities = notion_data.get('online_activities', [])
            short_activities = [a for a in all_activities if str(a.get('length', '')).lower() == 'short']
            long_activities = [a for a in all_activities if str(a.get('length', '')).lower() == 'long']

            selected_short = random.choice(short_activities) if short_activities else None
            selected_long = random.choice(long_activities) if long_activities else None

            selected_activities = []
            if selected_short:
                selected_activities.append(selected_short)
            if selected_long:
                selected_activities.append(selected_long)

            prompt = (
                f"{system_instructions}\n\n"
                "Here is the data for today. Use the affirmation and relationship health question as a guideline "
                "or inspiration so the message feels slightly different each day. "
                "For activities, suggest both the short and long options if provided.\n\n"
                f"Upcoming Events: {json.dumps(notion_data.get('events', []))}\n"
                f"Today's Reminders: {json.dumps(notion_data.get('reminders', []))}\n"
                f"Inspiration/Affirmation: {json.dumps(selected_affirmation) if selected_affirmation else 'None'}\n"
                f"Relationship Check-in Question: {json.dumps(selected_health) if selected_health else 'None'}\n"
                f"Online Activities Ideas: {json.dumps(selected_activities) if selected_activities else 'None'}\n\n"
                "Please synthesize this into a cohesive daily message."
            )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Failed to generate message from Gemini: {e}")
            return "Good morning! ☀️ I tried to write something super cute today, but my brain glitched. I love you both though, have a great day! ❤️"
