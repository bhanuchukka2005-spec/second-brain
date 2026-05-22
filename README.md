# 🧠 AI Second Brain

> Full-stack AI study companion. Chat with your notes, ace your exams.

---

## 📁 Project Structure

```
second-brain/
├── second-brain-ai/         ← Python backend (FastAPI + Streamlit)
└── second-brain-frontend/   ← React frontend (Vite + TypeScript)
```

---

## 🚀 Quick Start

### Backend
```bash
cd second-brain-ai
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```
API docs at `http://localhost:8000/docs`

### Frontend
```bash
cd second-brain-frontend
npm install
npm run dev
```
App at `http://localhost:3000`

---

## 🧪 Run Tests
```bash
cd second-brain-ai
pytest tests/ -v
```

---

## 🔑 Providers Supported
Groq · Gemini · OpenAI · Anthropic · Mistral · Cohere · Together AI · Ollama (local, no API key)

---

Built by **Bhanu Prakash** — drop a ⭐ if this helped!