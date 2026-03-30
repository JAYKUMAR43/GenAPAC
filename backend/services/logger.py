from sqlalchemy.orm import Session
from backend.models import ActionLog

def log_action(db: Session, user_input: str, detected_intent: str, action_taken: str):
    log_entry = ActionLog(
        user_input=user_input,
        detected_intent=detected_intent,
        action_taken=action_taken
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
