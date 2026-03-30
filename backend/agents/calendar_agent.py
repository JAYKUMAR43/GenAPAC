from sqlalchemy.orm import Session
from backend.models import Event

class CalendarAgent:
    def handle(self, intent_data: dict, db: Session) -> dict:
        intent = intent_data.get("intent")
        entities = intent_data.get("entities", {})
        
        if intent == "calendar.create":
            title = entities.get("title")
            datetime_str = entities.get("datetime")
            if not title or not datetime_str:
                return {"status": "error", "response": "Event title or time is missing. Please provide both."}
            
            event = Event(title=title, datetime=datetime_str)
            db.add(event)
            db.commit()
            db.refresh(event)
            return {"status": "success", "response": f"Event '{title}' scheduled for {datetime_str} successfully.", "data": {"event_id": event.id, "title": event.title, "time": event.datetime}}
            
        elif intent == "calendar.list":
            events = db.query(Event).all()
            if not events:
                return {"status": "success", "response": "You have no events scheduled.", "data": {"events": []}}
            event_list = [{"id": e.id, "title": e.title, "time": e.datetime} for e in events]
            response_text = "Your schedule: " + ", ".join([f"'{e['title']}' at {e['time']}" for e in event_list])
            return {"status": "success", "response": response_text, "data": {"events": event_list}}
            
        return {"status": "error", "response": "Invalid calendar intent."}
