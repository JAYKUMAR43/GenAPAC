import os
import uuid
from gtts import gTTS

# Ensure the static audio directory exists
AUDIO_STATIC_PATH = "backend/static/audio"
os.makedirs(AUDIO_STATIC_PATH, exist_ok=True)

def generate_audio(text: str, lang_code: str = 'en') -> str:
    """
    Generate an audio file from text using gTTS and return the URL path.
    """
    if not text:
        return ""
    
    try:
        tts = gTTS(text=text, lang=lang_code)
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(AUDIO_STATIC_PATH, filename)
        tts.save(filepath)
        return f"/static/audio/{filename}"
    except Exception as e:
        print(f"TTS Error: {e}")
        return ""
