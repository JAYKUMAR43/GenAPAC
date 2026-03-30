import speech_recognition as sr
from pydub import AudioSegment
import os
import tempfile
import imageio_ffmpeg

# Explicitly tell pydub to use the static ffmpeg installed via pip
AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()

def process_audio(audio_data: bytes) -> str:
    """
    Take binary audio data, convert to WAV, and run through Google Speech Recognition.
    Configured for English (India) to better handle Hinglish.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as f_in:
        f_in.write(audio_data)
        temp_in = f_in.name
    
    temp_out = temp_in + ".wav"
    
    try:
        # Convert audio format
        audio = AudioSegment.from_file(temp_in)
        audio.export(temp_out, format="wav")
        
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_out) as source:
            audio_file = recognizer.record(source)
            # Using en-IN handles a mix of English and accents decently. 
            # You can also use 'hi-IN' if it's purely Hindi.
            text = recognizer.recognize_google(audio_file, language="en-IN")
            return text
            
    except sr.UnknownValueError:
        return "" # Audio was not understood
    except sr.RequestError:
        return "" # Could not request results
    except Exception as e:
        print(f"STT Error: {e}")
        return ""
    finally:
        # Cleanup
        if os.path.exists(temp_in):
            os.remove(temp_in)
        if os.path.exists(temp_out):
            os.remove(temp_out)
