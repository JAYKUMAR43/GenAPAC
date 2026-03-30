# AI Productivity Assistant (Multi-Agent Architecture)

This is a production-ready, multi-agent AI Productivity Assistant built and designed for hackathons and professional scale. It features text and voice interaction support in English, Hindi, and Hinglish.

## Architecture Highlights
- **FastAPI Backend**: Rapid, asynchronous server backend.
- **Multi-Agent Routing**: Uses Gemini to route complex instructions logically to TaskManager, CalendarCoordinator, and NotesHandler.
- **SQLite & SQLAlchemy**: Robust database management for Tasks, Events, Notes, and a comprehensive Action Log.
- **Voice Interactions**: Full integration with WebM `MediaRecorder` audio capturing, Google Speech Recognition (tuned for english/indian accents), and server-side text-to-speech routing using gTTS.
- **Premium Glassmorphic UI**: High-fidelity frontend React + Vite environment with gorgeous styling matching an OS-level productivity suite.
- **RL / OpenEnv Ready**: A `env_wrapper.py` exposes standard RL interactions (`step`, `reset`, `state`) to make this compatible with Reinforcement Learning setups.

## Running Locally

### 1. Prerequisites
- Python 3.10+
- Node.js (v18+)

### 2. Backend Setup
```bash
# Set up a virtual environment AT THE ROOT LEVEL
python -m venv venv
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies 
pip install -r backend/requirements.txt

# Run the backend locally FROM THE ROOT FOLDER
uvicorn backend.main:app --reload
```
**Important:** Make sure you create a `.env` in the ROOT directory (where this README is) with:
`GEMINI_API_KEY=your_google_gemini_api_key_here`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Running via Docker Compute
If you want to just spin it all up via docker:
```bash
docker-compose up --build
```

You can then test on `http://localhost:5173`

*(Note: Audio recording in browser requires localhost or HTTPS)*
