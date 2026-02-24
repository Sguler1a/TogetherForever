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
            "You do not need to greet the users by name, just a general 'Good morning loves!' or similar is fine. "
            "You are a kitten, sprinkle in cat puns and cat-related content like 'meow' and 'purr'. "
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
            
            # Since there is no 'Length' property, just randomly select 2 activities to suggest
            selected_activities = []
            if all_activities:
                # Shuffle and pick up to 2
                shuffled = list(all_activities)
                random.shuffle(shuffled)
                selected_activities = shuffled[:2]

            prompt = (
                f"{system_instructions}\n\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. You MUST include every single piece of data provided below in your message.\n"
                "2. If an affirmation or relationship question is provided, you must explicitly mention it.\n"
                "3. If any online activities are provided, you MUST explicitly suggest ALL of them.\n"
                "4. Only after ensuring all data points are included should you embellish the message with your cute, bubbly tone.\n\n"
                "Here is the data for today:\n"
                f"Upcoming Events: {json.dumps(notion_data.get('events', []))}\n"
                f"Today's Reminders: {json.dumps(notion_data.get('reminders', []))}\n"
                f"Inspiration/Affirmation: {json.dumps(selected_affirmation) if selected_affirmation else 'None'}\n"
                f"Relationship Check-in Question: {json.dumps(selected_health) if selected_health else 'None'}\n"
                f"Online Activities Ideas: {json.dumps(selected_activities) if selected_activities else 'None'}\n\n"
                "Please synthesize this into a cohesive daily message, strictly following the CRITICAL INSTRUCTIONS above."
            )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Failed to generate message from Gemini: {e}")
            return "Good meowning! ☀️ I tried to write something super cute today, but my brain glitched owie :c. I love you both though, have a great day! ❤️ (@doberkai pls fix me)"
