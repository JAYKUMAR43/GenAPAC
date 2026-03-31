import sys
import os

# Add the repository root to sys.path so we can import from `backend`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
