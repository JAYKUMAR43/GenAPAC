from fastapi import FastAPI, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


from backend.database import SessionLocal, engine, Base
from backend.agents.router_agent import RouterAgent
from backend.services.text_to_speech import generate_audio
from backend.services.speech_to_text import process_audio
import os

from apscheduler.schedulers.background import BackgroundScheduler
from backend.models import Notification
from datetime import datetime, timezone
from pydantic import BaseModel

# Create DB schemas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Multi-Agent AI Assistant")

def check_scheduled_notifications():
    db = SessionLocal()
    try:
        notifications = db.query(Notification).filter(Notification.status == "pending").all()
        for n in notifications:
            # Trigger if it has been pending for at least 15 seconds (Hackathon Mock)
            # Make sure both datetimes are offset-aware or naive to compare properly
            now = datetime.now(timezone.utc)
            if n.created_at:
                delta = now - n.created_at
                if delta.total_seconds() > 15:
                    n.status = "triggered"
        db.commit()
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(check_scheduled_notifications, 'interval', seconds=10)
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()


# CORS setup for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files for audio playback
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
AUDIO_DIR = os.path.join(STATIC_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Serve Frontend static files (Optional fallback)
FRONTEND_DIST = os.path.join(BASE_DIR, "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

@app.get("/")
async def api_root():
    """
    Root status page for the Backend API.
    """
    return {
        "status": "online",
        "message": "AI Productivity Assistant - Backend API is running.",
        "endpoints": {
            "chat": "/chat (POST)",
            "voice": "/voice (POST)",
            "audio": "/static/audio/ (GET)"
        }
    }




router_agent = RouterAgent()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/chat")
async def chat_endpoint(message: str = Form(...), db: Session = Depends(get_db)):
    """
    Handle text chat input (English, Hindi, Hinglish)
    """
    result = router_agent.handle(message, db)
    
    # Generate Audio response
    response_text = result.get("response", "Done.")
    audio_url = generate_audio(response_text)
    
    result["audio_url"] = audio_url
    return result

@app.post("/voice")
async def voice_endpoint(audio: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Handle voice audio input (WebM/WAV)
    """
    # 1. Speech to Text
    audio_bytes = await audio.read()
    text_input = process_audio(audio_bytes)
    
    if not text_input:
        return {
            "status": "error", 
            "intent": "unknown", 
            "response": "Could not understand audio.",
            "audio_url": generate_audio("I couldn't understand the audio. Could you please repeat?")
        }
    
    # 2. Process Intent & Action
    result = router_agent.handle(text_input, db)
    
    # 3. Text to Speech output
    response_text = result.get("response", "Done.")
    audio_url = generate_audio(response_text)
    
    result["audio_url"] = audio_url
    result["user_text_detected"] = text_input # Return what was recognized
    return result

class MarkReadRequest(BaseModel):
    notification_id: int

@app.get("/notifications")
def get_notifications(db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(Notification.status == "triggered").all()
    return {"notifications": [{"id": n.id, "message": n.message} for n in notifs]}

@app.post("/notifications/mark_read")
def mark_read(req: MarkReadRequest, db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == req.notification_id).first()
    if n:
        n.status = "read"
        db.commit()
        return {"status": "success"}
    return {"status": "error", "message": "Notification not found"}
