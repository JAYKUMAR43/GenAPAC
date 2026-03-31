# Stage 1: Build Frontend
FROM node:18 AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Final Backend Image
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y ffmpeg libasound-dev portaudio19-dev python3-pyaudio && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy frontend build from Stage 1 into backend's dist folder
COPY --from=frontend-build /app/frontend/dist ./backend/dist

# Expose the API port
EXPOSE 8000

# Run the app via uvicorn from the root
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
