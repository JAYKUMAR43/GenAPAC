from backend.tools.base_tool import BaseTool
from backend.models import Event
from sqlalchemy.orm import Session

class CalendarTool(BaseTool):
    name = "CalendarTool"
    description = "Manage user calendar events."

    def execute(self, input_data: dict) -> dict:
        action = input_data.get("action")
        db: Session = input_data.get("db")
        
        if not db:
            return {"status": "error", "response": "Database session missing."}

        if action == "create":
            title = input_data.get("title")
            datetime_str = input_data.get("datetime")
            if not title or not datetime_str:
                return {"status": "error", "response": "Event title or time is missing. Please provide both."}
            event = Event(title=title, datetime=datetime_str)
            db.add(event)
            db.commit()
            db.refresh(event)
            return {"status": "success", "response": f"Event '{title}' scheduled for {datetime_str} successfully.", "data": {"event_id": event.id, "title": event.title, "time": event.datetime}}

        elif action == "list":
            events = db.query(Event).all()
            if not events:
                return {"status": "success", "response": "You have no events scheduled.", "data": {"events": []}}
            event_list = [{"id": e.id, "title": e.title, "time": e.datetime} for e in events]
            response_text = "Your schedule: " + ", ".join([f"'{e['title']}' at {e['time']}" for e in event_list])
            return {"status": "success", "response": response_text, "data": {"events": event_list}}

        return {"status": "error", "response": f"Invalid action '{action}' for CalendarTool."}
