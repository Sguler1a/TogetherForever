from google import genai
import logging
import json

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
            prompt = (
                f"{system_instructions}\n\n"
                "Here is the data for today. Use the affirmation and relationship health question as a guideline "
                "or inspiration so the message feels slightly different each day.\n\n"
                f"Upcoming Events: {json.dumps(notion_data.get('events', []))}\n"
                f"Today's Reminders: {json.dumps(notion_data.get('reminders', []))}\n"
                f"Inspiration/Affirmation: {json.dumps(notion_data.get('affirmations', []))}\n"
                f"Relationship Check-in Question: {json.dumps(notion_data.get('health', []))}\n"
                f"Online Activities Ideas: {json.dumps(notion_data.get('online_activities', []))}\n\n"
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
