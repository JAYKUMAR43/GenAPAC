from backend.tools.base_tool import BaseTool
from backend.models import Notification
from sqlalchemy.orm import Session
from datetime import datetime

class NotificationTool(BaseTool):
    name = "NotificationTool"
    description = "Schedule or trigger notifications and reminders."

    def execute(self, input_data: dict) -> dict:
        action = input_data.get("action")
        db: Session = input_data.get("db")
        
        if not db:
            return {"status": "error", "response": "Database session missing."}

        if action == "schedule":
            message = input_data.get("message")
            trigger_time = input_data.get("trigger_time")
            if not message or not trigger_time:
                return {"status": "error", "response": "Message or trigger time missing for notification."}
            
            notification = Notification(message=message, trigger_time=trigger_time, status="pending")
            db.add(notification)
            db.commit()
            db.refresh(notification)
            return {"status": "success", "response": f"Reminder set for {trigger_time}.", "data": {"notification_id": notification.id}}

        elif action == "list":
            notifications = db.query(Notification).filter(Notification.status == "pending").all()
            if not notifications:
                return {"status": "success", "response": "No pending notifications.", "data": {"notifications": []}}
            notif_list = [{"id": n.id, "message": n.message, "trigger_time": n.trigger_time} for n in notifications]
            return {"status": "success", "response": f"You have {len(notif_list)} pending notifications.", "data": {"notifications": notif_list}}

        return {"status": "error", "response": f"Invalid action '{action}' for NotificationTool."}
