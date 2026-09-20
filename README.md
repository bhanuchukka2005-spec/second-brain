# 🧠 AI Second Brain

> Chat with your notes. Ace your exams. Run it fully offline for free, or plug in your own API key for a cloud LLM — your choice.

A full-stack AI study companion — upload your notes, PDFs, slides, or YouTube lectures, then chat with them, generate quizzes, flashcards, concept maps, and summaries.

---

## ✨ Features

- 💬 **Chat with your notes** — RAG-based Q&A with source citations
- 📝 **Adaptive MCQ quizzes** — gets harder on topics you get wrong
- 🃏 **Flashcards** — Anki-compatible export
- 🗺️ **Concept maps** — rendered live as visual mind maps
- 📊 **Dashboard** — score history and performance charts
- 📄 **Summarize & compare** topics from your notes
- 🎥 **YouTube support** — index a video's transcript directly
- 🔑 **8 LLM providers** — run fully offline and free with local Ollama (no API key), or use your own key with Groq, Gemini, OpenAI, Anthropic, Mistral, Cohere, or Together AI
- 🔐 **Auth** — username/password, Google Sign-In, and password reset via email
- 🚦 **Rate limiting** — protects against abuse and runaway API costs
- 🗄️ **PostgreSQL persistence** — sessions and history survive backend restarts

---

## 🏗️ Architecture

```
second-brain/
├── second-brain-ai/          Python backend (FastAPI)
│   ├── api/                  Routes, schemas, auth dependencies
│   ├── src/
│   │   ├── db/                PostgreSQL, Google OAuth, email, vector store
│   │   ├── llm/                Unified brain — 8 providers
│   │   ├── features/           YouTube, flashcards, quizzes, concept maps
│   │   └── utils/               Retry logic, rate limiter, topic tracker
│   └── tests/                 pytest suite
│
└── second-brain-frontend/    React + TypeScript + Vite frontend
    └── src/
        ├── api/               Axios client
        ├── store/             Zustand state
        ├── components/        Chat, quiz, flashcards, layout
        └── pages/             Login, register, reset password, sessions
```

---

## 🚀 Local Development

### Backend
```bash
cd second-brain-ai
pip install -r requirements.txt
cp .env.example .env        # fill in PostgreSQL + JWT secret
uvicorn api.main:app --reload --port 8000
```
API docs: `http://localhost:8000/docs`

### Frontend
```bash
cd second-brain-frontend
npm install
npm run dev
```
App: `http://localhost:3000`

### Option A — run fully offline with Ollama (no API key)
```bash
ollama pull llama3.2
ollama serve
```
Select "🖥️ Local — Ollama" as the provider in the app.

### Option B — use your own API key
Select any of the 7 cloud providers (Groq, Gemini, OpenAI, Anthropic, Mistral, Cohere, Together AI) in the app's provider settings and paste in your key. Groq's free tier is a good starting point.

---

## 🧪 Tests

```bash
cd second-brain-ai
pytest tests/ -v
```

---

## 🌍 Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for step-by-step instructions to deploy the backend on Railway and the frontend on Vercel.

**Note:** Ollama only works for local development — it can't run on typical cloud hosts. For a deployed app, users should bring their own API key with a cloud provider (Groq's free tier is a good default).

---

## 🔑 Environment Variables (Backend)

| Variable | Purpose |
|---|---|
| `PG_HOST`, `PG_PORT`, `PG_DB`, `PG_USER`, `PG_PASSWORD` | PostgreSQL connection |
| `JWT_SECRET_KEY` | Signs auth tokens — use a long random string in production |
| `GOOGLE_CLIENT_ID` | Google Sign-In |
| `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` | Password reset emails (optional — logs to console if unset) |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend URLs |

Full list in `second-brain-ai/.env.example`.

---

## 📄 License

MIT

---

Built by **Bhanu Prakash** — drop a ⭐ if this helped you!