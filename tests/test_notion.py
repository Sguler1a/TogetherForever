import pytest
from datetime import datetime, timedelta
import pytz
from src.notion_client import NotionDataFetcher

@pytest.fixture
def notion_fetcher():
    # Pass dummy token and ID for testing offline logic
    return NotionDataFetcher(token="dummy_token", parent_page_id="dummy_id")

def test_get_today_str(notion_fetcher):
    tz = pytz.timezone("America/Toronto")
    expected = datetime.now(tz).strftime("%Y-%m-%d")
    assert notion_fetcher._get_today_str() == expected

def test_get_future_date_str(notion_fetcher):
    tz = pytz.timezone("America/Toronto")
    expected = (datetime.now(tz) + timedelta(days=4)).strftime("%Y-%m-%d")
    assert notion_fetcher._get_future_date_str(4) == expected

def test_parse_results(notion_fetcher):
    # Mock some Notion API standard result
    mock_results = [
        {
            "id": "123",
            "url": "https://notion.so/123",
            "properties": {
                "Name": {
                    "type": "title",
                    "title": [{"plain_text": "Buy groceries"}]
                },
                "Date": {
                    "type": "date",
                    "date": {"start": "2024-05-01"}
                }
            }
        },
        {
            "id": "456",
            "url": "https://notion.so/456",
            "properties": {
                "Title": {
                    "type": "title",
                    "title": [{"plain_text": "Untitled item"}]
                }
            }
        }
    ]
    
    parsed = notion_fetcher._parse_results(mock_results, "Name")
    
    assert len(parsed) == 2
    assert parsed[0]["title"] == "Buy groceries"
    assert parsed[0]["date"] == "2024-05-01"
    assert parsed[0]["id"] == "123"
    
    # It should fallback to Title or Untitled
    assert parsed[1]["title"] == "Untitled item"
    assert "date" not in parsed[1]
