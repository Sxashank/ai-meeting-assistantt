Here is a **clean professional README.md** you can directly copy and paste into your GitHub repository root.

---

# AI Meeting Assistant – Full Stack Application

## Overview

AI Meeting Assistant is a full-stack web application that allows users to upload meeting audio recordings and automatically generates:

* Speech transcription
* Speaker diarization (who spoke when)
* Meeting summary
* Action items extraction
* Speaker-aware transcript labeling

The system uses modern AI models for speech processing and natural language understanding and provides a web-based interface for easy usage.

---

## Features

* Audio file upload from browser
* Automatic speech-to-text transcription
* Optional multi-speaker diarization
* AI-powered meeting summarization
* Action item extraction
* Secure environment variable handling
* Production-ready backend with FastAPI
* React + Vite frontend
* Docker support

---

## Tech Stack

### Frontend

* React
* Vite
* Tailwind CSS
* JavaScript

### Backend

* FastAPI
* Python 3.10+
* Whisper (speech recognition)
* Pyannote Audio (speaker diarization)
* Transformers (summarization)
* Torch
* Uvicorn

---

## Project Structure

```
ai-meeting-assistant/
│
├── backend/
│   ├── app/
│   ├── services/
│   ├── utils/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

## Prerequisites

Make sure the following are installed on your system:

### System Requirements

* Python 3.10 or higher
* Node.js 18 or higher
* Git
* FFmpeg (required for audio processing)

---

## Install FFmpeg

### Windows

Download FFmpeg from:

```
https://ffmpeg.org/download.html
```

Add FFmpeg to system PATH.

Verify installation:

```
ffmpeg -version
```

---

## Backend Setup

### Step 1: Navigate to Backend Folder

```
cd backend
```

---

### Step 2: Create Virtual Environment

```
python -m venv venv
```

Activate virtual environment:

Windows:

```
venv\Scripts\activate
```

Linux / Mac:

```
source venv/bin/activate
```

---

### Step 3: Install Dependencies

```
pip install -r requirements.txt
```

---

### Step 4: Create Environment File

Inside `backend` folder create a file named `.env`

Add:

```
HF_TOKEN=your_huggingface_token_here
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
USE_ONNX=true
```

Note:
Do not commit `.env` file to GitHub.

---

### Step 5: Run Backend Server

```
python -m uvicorn app.main:app --reload
```

Backend will run on:

```
http://127.0.0.1:8000
```

Swagger API docs:

```
http://127.0.0.1:8000/docs
```

---

## Frontend Setup

### Step 1: Navigate to Frontend Folder

```
cd frontend
```

---

### Step 2: Install Dependencies

```
npm install
```

---

### Step 3: Configure API URL

Create `.env` file inside frontend folder:

```
VITE_API_URL=http://127.0.0.1:8000
```

---

### Step 4: Start Frontend Server

```
npm run dev
```

Frontend will run on:

```
http://localhost:5173
```

---

## How The Application Works

### Step 1: Audio Upload

User uploads an audio file through the frontend interface.

Supported formats:

* WAV
* MP3
* M4A
* FLAC
* OGG

---

### Step 2: Backend Processing Pipeline

After upload, the backend performs the following steps:

1. Audio Preprocessing

   * Audio is normalized and resampled.

2. Speech Transcription

   * Whisper model converts speech to text.

3. Speaker Diarization (Optional)

   * Pyannote model detects multiple speakers and timestamps.

4. Transcript Merging

   * Transcription segments are aligned with speaker segments.

5. Summarization

   * Transformer model generates meeting summary.

6. Action Item Extraction

   * NLP logic extracts tasks and responsibilities.

---

### Step 3: Result Display

Frontend displays:

* Full transcript with speakers
* Summary panel
* Action items list
* Meeting duration

---

## Docker Deployment (Optional)

### Build and Run Using Docker

From project root:

```
docker-compose up --build
```

Backend will run on:

```
http://localhost:8000
```

Frontend will run on:

```
http://localhost:3000
```

---

## Environment Security

* API tokens are stored in `.env` files
* `.env` files are ignored using `.gitignore`
* GitHub secret scanning protection enabled

Never push real API tokens to GitHub.

---

## Production Deployment

Backend can be deployed on:

* Render
* Railway
* AWS
* DigitalOcean

Frontend can be deployed on:

* Vercel
* Netlify

---

## Author

Shashank
AI Meeting Assistant Project

---

