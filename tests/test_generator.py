import pytest
from src.generator import MessageGenerator
import google.generativeai as genai

# Mock the GenerativeModel
class MockResponse:
    def __init__(self, text):
        self.text = text

class MockModel:
    def generate_content(self, prompt):
        if "no upcoming events" in prompt:
            return MockResponse("Mocked empty state positive message 💖")
        return MockResponse("Mocked data synthesis message ✨")

@pytest.fixture
def mock_genai(monkeypatch):
    monkeypatch.setattr(genai, "configure", lambda api_key: None)
    monkeypatch.setattr(genai, "GenerativeModel", lambda model_name: MockModel())

def test_empty_state_generation(mock_genai):
    generator = MessageGenerator(api_key="dummy")
    empty_data = {"events": [], "reminders": [], "affirmations": [], "health": [], "online_activities": []}
    
    result = generator.generate_daily_message(empty_data)
    assert "Mocked empty state" in result
    
def test_data_synthesis_generation(mock_genai):
    generator = MessageGenerator(api_key="dummy")
    data = {
        "events": [{"title": "Date Night", "date": "2024-05-10"}],
        "reminders": [], "affirmations": [], "health": [], "online_activities": []
    }
    
    result = generator.generate_daily_message(data)
    assert "Mocked data synthesis" in result
