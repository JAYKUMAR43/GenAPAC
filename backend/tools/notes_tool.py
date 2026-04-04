from backend.tools.base_tool import BaseTool
from backend.models import Note
from sqlalchemy.orm import Session

class NotesTool(BaseTool):
    name = "NotesTool"
    description = "Manage user notes."

    def execute(self, input_data: dict) -> dict:
        action = input_data.get("action")
        db: Session = input_data.get("db")
        
        if not db:
            return {"status": "error", "response": "Database session missing."}

        if action == "create":
            content = input_data.get("content")
            if not content:
                return {"status": "error", "response": "Note content is missing."}
            note = Note(content=content)
            db.add(note)
            db.commit()
            db.refresh(note)
            return {"status": "success", "response": "Note saved successfully.", "data": {"note_id": note.id, "content": note.content}}

        elif action == "list":
            notes = db.query(Note).all()
            if not notes:
                return {"status": "success", "response": "You have no notes saved.", "data": {"notes": []}}
            note_list = [{"id": n.id, "content": n.content} for n in notes]
            response_text = f"You have {len(note_list)} notes."
            return {"status": "success", "response": response_text, "data": {"notes": note_list}}

        return {"status": "error", "response": f"Invalid action '{action}' for NotesTool."}
