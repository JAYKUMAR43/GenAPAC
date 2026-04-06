from fastapi import FastAPI, UploadFile, File, Form, Depends
from typing import Optional
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
from backend.mcp_server import mcp_server


# Create DB schemas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Multi-Agent AI Assistant")

def check_scheduled_notifications():
    db = SessionLocal()
    try:
        notifications = db.query(Notification).filter(Notification.status == "pending").all()
        for n in notifications:
            try:
                # Assuming trigger_time format is 'YYYY-MM-DD HH:MM' or similar parsable string
                if n.trigger_time:
                    try:
                        # Try parsing exactly
                        trigger = datetime.strptime(n.trigger_time, "%Y-%m-%d %H:%M")
                    except ValueError:
                        # Fallback for ISO format or other formats
                        import dateutil.parser
                        trigger = dateutil.parser.parse(n.trigger_time)
                    
                    # Convert to naive local to compare or ensure both are UTC. Let's assume naive local for simplicity since format is 'YYYY-MM-DD HH:MM'
                    now = datetime.now()
                    if trigger.tzinfo:
                        now = datetime.now(trigger.tzinfo)
                        
                    if now >= trigger:
                        n.status = "triggered"
                        n.message = "⏰ Time arrived: " + n.message
                else:
                    # Legacy mock if no trigger_time
                    now = datetime.now(timezone.utc)
                    if n.created_at:
                        delta = now - n.created_at
                        if delta.total_seconds() > 15:
                            n.status = "triggered"
            except Exception as e:
                print("Notification trigger error:", e)
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

# MCP Server Integration
app.mount("/mcp", mcp_server.sse_app())


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
async def chat_endpoint(message: str = Form(...), history: Optional[str] = Form(None), db: Session = Depends(get_db)):
    """
    Handle text chat input (English, Hindi, Hinglish)
    """
    result = router_agent.handle(message, history, db)
    
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

from backend.services.gemini_service import analyze_document

@app.post("/upload")
async def upload_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Handle document/image uploads for AI extraction
    """
    file_bytes = await file.read()
    mime_type = file.content_type
    
    # Analyze the document
    result = analyze_document(file_bytes, mime_type)
    
    if result.get("status") == "success":
        # Pass the extracted text or intent directly to the router
        extracted_text = result.get("extracted_text", "")
        if extracted_text:
            router_result = router_agent.handle(f"Process this extracted document data carefully: {extracted_text}", None, db)
            
            response_text = router_result.get("response", "Document processed.")
            audio_url = generate_audio(response_text)
            router_result["audio_url"] = audio_url
            return router_result

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
