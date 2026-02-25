import pytest
from src.generator import MessageGenerator
from google import genai

# Mock the response
class MockResponse:
    def __init__(self, text):
        self.text = text

# Mock the models service inside the client
class MockModels:
    def generate_content(self, model, contents):
        if "no upcoming events" in contents:
            return MockResponse("Mocked empty state positive message 💖")
        return MockResponse("Mocked data synthesis message ✨")

# Mock the Client
class MockClient:
    def __init__(self, api_key=None):
        self.models = MockModels()

@pytest.fixture
def mock_genai(monkeypatch):
    monkeypatch.setattr(genai, "Client", MockClient)

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
