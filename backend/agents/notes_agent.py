from sqlalchemy.orm import Session
from backend.models import Note

class NotesAgent:
    def handle(self, intent_data: dict, db: Session) -> dict:
        intent = intent_data.get("intent")
        entities = intent_data.get("entities", {})
        
        if intent == "notes.create":
            content = entities.get("content")
            if not content:
                return {"status": "error", "response": "Note content is missing."}
            
            note = Note(content=content)
            db.add(note)
            db.commit()
            db.refresh(note)
            return {"status": "success", "response": "Note saved successfully.", "data": {"note_id": note.id, "content": note.content}}
            
        elif intent == "notes.list":
            notes = db.query(Note).all()
            if not notes:
                return {"status": "success", "response": "You have no notes saved.", "data": {"notes": []}}
            note_list = [{"id": n.id, "content": n.content} for n in notes]
            response_text = f"You have {len(note_list)} notes."
            return {"status": "success", "response": response_text, "data": {"notes": note_list}}
            
        return {"status": "error", "response": "Invalid notes intent."}
