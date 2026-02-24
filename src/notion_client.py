import os
from datetime import datetime, timedelta
import pytz
from notion_client import Client
import logging

logger = logging.getLogger(__name__)

class NotionDataFetcher:
    def __init__(self, token: str, parent_page_id: str, timezone_str: str = "America/Toronto"):
        self.notion = Client(auth=token)
        self.parent_page_id = parent_page_id
        self.tz = pytz.timezone(timezone_str)
        self.db_mappings = {}

    def fetch_databases(self):
        """Find inline databases within the parent page."""
        try:
            # Notion API block children allows pagination, but let's get standard first page
            response = self.notion.blocks.children.list(block_id=self.parent_page_id)
            for block in response.get("results", []):
                if block["type"] == "child_database":
                    title = block["child_database"]["title"].lower()
                    db_id = block["id"]
                    if "event" in title:
                        self.db_mappings["events"] = db_id
                    elif "reminder" in title:
                        self.db_mappings["reminders"] = db_id
                    elif "affirmation" in title or "note" in title:
                        self.db_mappings["affirmations"] = db_id
                    elif "health" in title or "relationship" in title or "check" in title:
                        self.db_mappings["health"] = db_id
                    elif "online" in title or "activity" in title:
                        self.db_mappings["online_activities"] = db_id
            
            logger.info(f"Discovered databases: {self.db_mappings}")
            return self.db_mappings
        except Exception as e:
            logger.error(f"Failed to fetch databases from parent page: {e}")
            return {}

    def _get_today_str(self):
        return datetime.now(self.tz).strftime("%Y-%m-%d")

    def _get_future_date_str(self, days: int):
        return (datetime.now(self.tz) + timedelta(days=days)).strftime("%Y-%m-%d")

    def get_events(self):
        db_id = self.db_mappings.get("events")
        if not db_id:
            return []
        
        today = self._get_today_str()
        future = self._get_future_date_str(7)
        
        try:
            response = self.notion.databases.query(
                database_id=db_id,
                filter={
                    "and": [
                        {"property": "Date", "date": {"on_or_after": today}},
                        {"property": "Date", "date": {"on_or_before": future}}
                    ]
                },
                sorts=[{"property": "Date", "direction": "ascending"}]
            )
            return self._parse_results(response.get("results", []), "Name")
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return []

    def get_reminders(self):
        db_id = self.db_mappings.get("reminders")
        if not db_id:
            return []
            
        today = self._get_today_str()
        try:
            # Assuming reminders have a Date property, or a Done checkbox
            response = self.notion.databases.query(
                database_id=db_id,
                filter={
                    "property": "Date",
                    "date": {"equals": today}
                }
            )
            return self._parse_results(response.get("results", []), "Task")
        except Exception as e:
            logger.error(f"Error fetching reminders: {e}")
            return []

    def get_affirmations(self):
        db_id = self.db_mappings.get("affirmations")
        if not db_id:
            return []
        try:
            response = self.notion.databases.query(database_id=db_id, page_size=100)
            return self._parse_results(response.get("results", []), "Quote")
        except Exception as e:
            logger.error(f"Error fetching affirmations: {e}")
            return []
            
    def get_relationship_health(self):
        db_id = self.db_mappings.get("health")
        if not db_id:
            return []
        try:
            response = self.notion.databases.query(database_id=db_id, page_size=100)
            return self._parse_results(response.get("results", []), "Question")
        except Exception as e:
            logger.error(f"Error fetching relationship health: {e}")
            return []

    def get_online_activities(self):
        db_id = self.db_mappings.get("online_activities")
        if not db_id:
            return []
        try:
            response = self.notion.databases.query(database_id=db_id, page_size=100)
            return self._parse_results(response.get("results", []), "Name")
        except Exception as e:
            logger.error(f"Error fetching online activities: {e}")
            return []

    def fetch_all_data(self):
        """Aggregate all queries into a single data dictionary."""
        if not self.db_mappings:
            self.fetch_databases()
            
        return {
            "events": self.get_events(),
            "reminders": self.get_reminders(),
            "affirmations": self.get_affirmations(),
            "health": self.get_relationship_health(),
            "online_activities": self.get_online_activities()
        }

    def _parse_results(self, results, title_prop_name="Name"):
        """Extract basic text and date fields from Notion API page objects."""
        parsed = []
        for page in results:
            props = page.get("properties", {})
            item = {"id": page["id"], "url": page["url"]}
            
            # Try varying common title property names
            title_keys = [title_prop_name, "Name", "Task", "Quote", "Question", "Title"]
            title_text = "Untitled"
            for tk in title_keys:
                if tk in props and props[tk].get("type") == "title":
                    title_array = props[tk].get("title", [])
                    if title_array:
                        title_text = "".join(t.get("plain_text", "") for t in title_array)
                    break
            item["title"] = title_text
            
            # Check for generic Date property
            if "Date" in props and props["Date"].get("type") == "date":
                date_obj = props["Date"].get("date")
                if date_obj:
                    item["date"] = date_obj.get("start")
            
            # Check for Location text property (rich_text)
            if "Location" in props and props["Location"].get("type") == "rich_text":
                location_array = props["Location"].get("rich_text", [])
                if location_array:
                    item["location"] = "".join(t.get("plain_text", "") for t in location_array)
            
            # Check for Length select dropdown (select)
            if "Length" in props and props["Length"].get("type") == "select":
                select_obj = props["Length"].get("select")
                if select_obj:
                    item["length"] = select_obj.get("name")
            
            parsed.append(item)
        return parsed
