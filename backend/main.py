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

# Create DB schemas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Multi-Agent AI Assistant")

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
async def serve_frontend():
    index_path = os.path.join(BASE_DIR, "dist", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"detail": "Frontend not built yet. Please run build script."}



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
