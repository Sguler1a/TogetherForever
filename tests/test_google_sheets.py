import pytest
from datetime import datetime, timedelta
import pytz
from unittest.mock import MagicMock, patch
from src.google_sheets_api import GoogleSheetsFetcher

@pytest.fixture
def sheets_fetcher():
    # Patch the authentication and spreadsheet initialization to avoid real API calls
    with patch('src.google_sheets_api.GoogleSheetsFetcher._authenticate', return_value=MagicMock()), \
         patch('src.google_sheets_api.GoogleSheetsFetcher._get_spreadsheet', return_value=MagicMock()):
        return GoogleSheetsFetcher(credentials_path="dummy_path.json", sheet_id="dummy_id")

def test_get_today_str(sheets_fetcher):
    tz = pytz.timezone("America/Toronto")
    expected = datetime.now(tz).strftime("%Y-%m-%d")
    assert sheets_fetcher._get_today_str() == expected

def test_parse_date(sheets_fetcher):
    # Test valid formats
    assert sheets_fetcher._parse_date("2024-05-01") == "2024-05-01"
    assert sheets_fetcher._parse_date("05/01/2024") == "2024-05-01"
    
    # Test invalid format returns original string
    assert sheets_fetcher._parse_date("not a date") == "not a date"
    
    # Test empty string returns None
    assert sheets_fetcher._parse_date("") is None

def test_get_events(sheets_fetcher):
    # Mock worksheet records
    mock_records = [
        {"Name": "Past Event", "Date": "2020-01-01"},
        {"Name": "Future Event", "Date": "2099-12-31"},
        {"Name": "Bad Date Event", "Date": "unknown"}
    ]
    with patch.object(sheets_fetcher, '_get_worksheet_records', return_value=mock_records):
        events = sheets_fetcher.get_events()
        
        # Should only return future events
        assert len(events) == 2
        assert events[0]["title"] == "Future Event"
        assert events[0]["date"] == "2099-12-31"

def test_get_reminders(sheets_fetcher):
    today = sheets_fetcher._get_today_str()
    past_date = (datetime.now(sheets_fetcher.tz) - timedelta(days=5)).strftime("%Y-%m-%d")
    future_date = (datetime.now(sheets_fetcher.tz) + timedelta(days=5)).strftime("%Y-%m-%d")

    mock_records = [
        {"Task": "Current Reminder", "Date": past_date, "End Date": future_date},
        {"Task": "Past Reminder", "Date": "2020-01-01", "End Date": "2020-01-02"},
        {"Task": "Single Day Reminder Today", "Date": today, "End Date": ""}
    ]
    
    with patch.object(sheets_fetcher, '_get_worksheet_records', return_value=mock_records):
        reminders = sheets_fetcher.get_reminders()
        
        assert len(reminders) == 2
        assert reminders[0]["title"] == "Current Reminder"
        assert reminders[1]["title"] == "Single Day Reminder Today"

def test_get_online_activities(sheets_fetcher):
    mock_records = [
        {"Name": "Activity 1", "Length": "Short"},
        {"Name": "Activity 2", "Length": "Long"},
        {"Name": "", "Length": "Short"} # Should be ignored due to empty name
    ]
    
    with patch.object(sheets_fetcher, '_get_worksheet_records', return_value=mock_records):
        activities = sheets_fetcher.get_online_activities()
        
        assert len(activities) == 2
        assert activities[0]["title"] == "Activity 1"
        assert activities[0]["length"] == "Short"
        assert activities[1]["title"] == "Activity 2"
        assert activities[1]["length"] == "Long"
