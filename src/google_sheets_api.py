import os
import json
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsFetcher:
    def __init__(self, credentials_path: str, sheet_id: str, timezone_str: str = "America/Toronto"):
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.tz = pytz.timezone(timezone_str)
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.client = self._authenticate()
        self.spreadsheet = self._get_spreadsheet()

    def _authenticate(self):
        try:
            # Check if credentials path exists as a file, otherwise assume it might be a JSON string from env
            if os.path.exists(self.credentials_path):
                credentials = Credentials.from_service_account_file(
                    self.credentials_path, scopes=self.scopes
                )
            else:
                 # Fallback for when credentials are passed directly as a JSON string in env
                 creds_dict = json.loads(self.credentials_path)
                 # Fix escaped newlines in the private key so the PEM can be loaded
                 if 'private_key' in creds_dict:
                     creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
                 credentials = Credentials.from_service_account_info(
                     creds_dict, scopes=self.scopes
                 )
            return gspread.authorize(credentials)
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            return None

    def _get_spreadsheet(self):
        if not self.client:
            return None
        try:
            return self.client.open_by_key(self.sheet_id)
        except Exception as e:
            logger.error(f"Failed to open spreadsheet '{self.sheet_id}': {e}")
            return None

    def _get_today_str(self):
        return datetime.now(self.tz).strftime("%Y-%m-%d")

    def _parse_date(self, date_str):
        if not date_str:
            return None
        # Handle formats like YYYY-MM-DD or MM/DD/YYYY
        try:
            if "/" in date_str:
                return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            return date_str # Return as is if format is unknown but present

    def _get_worksheet_records(self, title):
        if not self.spreadsheet:
            return []
        try:
             # Find worksheet by title (case-insensitive approximation)
             for ws in self.spreadsheet.worksheets():
                 if title.lower() in ws.title.lower():
                     # get_all_records returns list of dicts with headers as keys
                     records = ws.get_all_records()
                     return [{str(k).strip(): v for k, v in row.items()} for row in records]
             logger.warning(f"Worksheet matching '{title}' not found.")
             return []
        except Exception as e:
             logger.error(f"Error reading worksheet '{title}': {e}")
             return []

    def get_events(self):
        records = self._get_worksheet_records("Events")
        today = self._get_today_str()
        
        events = []
        for row in records:
            name = row.get("Name", "")
            date_raw = str(row.get("Date", ""))
            
            if not name or not date_raw:
                continue
                
            date_val = self._parse_date(date_raw)
            if date_val and date_val >= today: # Only future or today's events
                 events.append({
                     "title": name,
                     "date": date_val
                 })
                 
        # Sort by date
        return sorted(events, key=lambda x: x["date"])

    def get_reminders(self):
        records = self._get_worksheet_records("Reminders")
        today = self._get_today_str()
        
        reminders = []
        for row in records:
            task = row.get("Task", "")
            start_raw = str(row.get("Date", ""))
            end_raw = str(row.get("End Date", ""))
            
            if not task or not start_raw:
                 continue
                 
            start_date = self._parse_date(start_raw)
            end_date = self._parse_date(end_raw) if end_raw else start_date
            
            # Check if today falls within range
            if start_date and start_date <= today and end_date >= today:
                reminders.append({
                    "title": task,
                    "date_start": start_date,
                    "date_end": end_date
                })
        
        return reminders

    def get_upcoming_reminders(self):
        records = self._get_worksheet_records("Reminders")
        today = self._get_today_str()
        
        reminders = []
        for row in records:
            task = row.get("Task", "")
            start_raw = str(row.get("Date", ""))
            end_raw = str(row.get("End Date", ""))
            
            if not task or not start_raw:
                 continue
                 
            start_date = self._parse_date(start_raw)
            end_date = self._parse_date(end_raw) if end_raw else start_date
            
            # Check if end date is today or in the future
            if end_date and end_date >= today:
                reminders.append({
                    "title": task,
                    "date_start": start_date,
                    "date_end": end_date
                })
        
        # Sort by start date
        return sorted(reminders, key=lambda x: x["date_start"] if x["date_start"] else "")

    def get_affirmations(self):
        records = self._get_worksheet_records("Affirmations")
        affirmations = []
        for row in records:
             quote = row.get("Quote", "")
             if quote:
                 affirmations.append({"title": quote})
        return affirmations
            
    def get_relationship_health(self):
         records = self._get_worksheet_records("Health")
         questions = []
         for row in records:
              question = row.get("Question", "")
              if question:
                  questions.append({"title": question})
         return questions

    def get_online_activities(self):
         records = self._get_worksheet_records("Online Activities")
         activities = []
         for row in records:
             name = row.get("Name", "")
             length = row.get("Length", "")
             
             if name:
                 activities.append({
                     "title": name,
                     "length": length
                 })
         return activities

    def fetch_all_data(self):
        """Aggregate all queries into a single data dictionary matching previous structure."""
        if not self.spreadsheet:
            logger.error("Cannot fetch data: Spreadsheet not initialized.")
            return {
                "events": [],
                "reminders": [],
                "affirmations": [],
                "health": [],
                "online_activities": []
            }
            
        return {
            "events": self.get_events(),
            "reminders": self.get_reminders(),
            "affirmations": self.get_affirmations(),
            "health": self.get_relationship_health(),
            "online_activities": self.get_online_activities()
        }

    def _append_row_by_header(self, title, row_dict):
        if not self.spreadsheet:
            return False
        try:
            for ws in self.spreadsheet.worksheets():
                if title.lower() in ws.title.lower():
                    headers = ws.row_values(1)
                    row_data = []
                    for h in headers:
                        row_data.append(row_dict.get(h, ""))
                    ws.append_row(
                        row_data,
                        value_input_option="USER_ENTERED",
                        insert_data_option="INSERT_ROWS"
                    )
                    return True
            logger.warning(f"Worksheet matching '{title}' not found for appending.")
            return False
        except Exception as e:
            logger.error(f"Error appending to worksheet '{title}': {e}")
            return False

    def add_event(self, name: str, date: str, location: str = ""):
        return self._append_row_by_header("Events", {"Name": name, "Date": date, "Location": location})

    def add_reminder(self, task: str, start_date: str, end_date: str = ""):
        # If no end_date provided, default to start_date or empty in sheet? 
        # Notion usually defaults end date to empty if it's identical or not a range. 
        # But we'll follow what the user provides.
        return self._append_row_by_header("Reminders", {"Task": task, "Date": start_date, "End Date": end_date})

    def add_affirmation(self, quote: str):
        return self._append_row_by_header("Affirmations", {"Quote": quote})

    def add_health_question(self, question: str):
        return self._append_row_by_header("Health", {"Question": question})

    def add_online_activity(self, name: str, length: str):
        return self._append_row_by_header("Online Activities", {"Name": name, "Length": length})
