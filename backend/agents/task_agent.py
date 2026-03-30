from sqlalchemy.orm import Session
from backend.models import Task

class TaskAgent:
    def handle(self, intent_data: dict, db: Session) -> dict:
        intent = intent_data.get("intent")
        entities = intent_data.get("entities", {})
        
        if intent == "task.create":
            title = entities.get("title")
            if not title:
                return {"status": "error", "response": "Task title is missing. What task do you want me to add?"}
            
            task = Task(title=title)
            db.add(task)
            db.commit()
            db.refresh(task)
            return {"status": "success", "response": f"Task '{title}' created successfully.", "data": {"task_id": task.id, "title": task.title}}
            
        elif intent == "task.list":
            tasks = db.query(Task).all()
            if not tasks:
                return {"status": "success", "response": "You have no tasks.", "data": {"tasks": []}}
            task_list = [{"id": t.id, "title": t.title, "status": t.status} for t in tasks]
            response_text = "Here are your tasks: " + ", ".join([f"[{t['status']}] {t['title']}" for t in task_list])
            return {"status": "success", "response": response_text, "data": {"tasks": task_list}}
            
        elif intent == "task.complete":
            task_id = entities.get("task_id")
            if not task_id:
                return {"status": "error", "response": "Task ID is missing."}
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return {"status": "error", "response": "Task not found."}
            task.status = "completed"
            db.commit()
            return {"status": "success", "response": f"Task '{task.title}' marked as complete.", "data": {"task_id": task.id}}
            
        return {"status": "error", "response": "Invalid task intent."}
