from backend.tools.base_tool import BaseTool
from backend.models import Task
from sqlalchemy.orm import Session

class TaskTool(BaseTool):
    name = "TaskTool"
    description = "Manage user tasks including creation, listing, and completion."

    def execute(self, input_data: dict) -> dict:
        action = input_data.get("action")
        db: Session = input_data.get("db")
        
        if not db:
            return {"status": "error", "response": "Database session missing in tool payload."}

        if action == "create":
            title = input_data.get("title")
            if not title:
                return {"status": "error", "response": "Task title is missing. What task do you want me to add?"}
            task = Task(title=title)
            db.add(task)
            db.commit()
            db.refresh(task)
            return {"status": "success", "response": f"Task '{title}' created successfully.", "data": {"task_id": task.id, "title": task.title}}

        elif action == "list":
            tasks = db.query(Task).all()
            if not tasks:
                return {"status": "success", "response": "You have no tasks.", "data": {"tasks": []}}
            task_list = [{"id": t.id, "title": t.title, "status": t.status} for t in tasks]
            response_text = "Here are your tasks: " + ", ".join([f"[{t['status']}] {t['title']}" for t in task_list])
            return {"status": "success", "response": response_text, "data": {"tasks": task_list}}

        elif action == "complete":
            task_id = input_data.get("task_id")
            if not task_id:
                return {"status": "error", "response": "Task ID is missing."}
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return {"status": "error", "response": "Task not found."}
            task.status = "completed"
            db.commit()
            return {"status": "success", "response": f"Task '{task.title}' marked as complete.", "data": {"task_id": task.id}}

        return {"status": "error", "response": f"Invalid action '{action}' for TaskTool."}
