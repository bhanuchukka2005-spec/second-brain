# 🧠 AI Second Brain for Students

> The most advanced open-source AI study companion. Works 100% locally — no API key needed.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32-red?logo=streamlit)
![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-orange)
![Ollama](https://img.shields.io/badge/Local-Ollama-black?logo=ollama)
![Providers](https://img.shields.io/badge/Cloud-7%20Providers-blueviolet)
![Tests](https://img.shields.io/badge/Tests-75%20passing-brightgreen?logo=pytest)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🎯 What is this?

**AI Second Brain** is a production-grade AI study companion built on RAG (Retrieval Augmented Generation). Upload your PDFs, lecture slides, or YouTube lectures — then have a full conversation with all of it.

**No API key required.** Run it 100% locally using [Ollama](https://ollama.com) — free, private, offline. Or plug in any of 7 cloud providers if you prefer.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🖥️ **Local LLM (Ollama)** | Run LLaMA, Mistral, Gemma locally — no API key, no internet |
| ☁️ **7 Cloud Providers** | Groq, Gemini, OpenAI, Anthropic, Mistral, Cohere, Together AI |
| 💬 **Chat with memory** | Multi-turn conversation with source citations per answer |
| 📚 **Persistent sessions** | SQLite-backed — save and reload your indexed notes anytime |
| 🎥 **YouTube support** | Paste a URL, it indexes the transcript automatically |
| 📝 **Adaptive MCQ Quiz** | Gets harder on topics you get wrong |
| 🃏 **Flashcard generator** | Anki-compatible CSV + JSON export |
| 🗺️ **Concept map** | Auto-generates a Mermaid mindmap from your notes |
| 📄 **Summarizer** | One-click summary of any topic |
| 🔀 **Topic comparison** | Compare two concepts side-by-side |
| 📊 **Weak topic dashboard** | Plotly visualizations of your knowledge gaps |
| 🔁 **Retry logic** | Exponential backoff on all cloud API calls |
| 🛡️ **Input validation** | API keys, file types, YouTube URLs validated before use |
| 📋 **Structured logging** | Rotating file logs + console output |
| 🧪 **75 unit tests** | pytest suite covering all core modules |
| ⚙️ **CI/CD** | GitHub Actions — tests on Python 3.11 & 3.12 on every push |
| 🐳 **Docker Compose** | One-command deployment with volume persistence |

---

## 🖥️ Local Setup (No API Key — Recommended)

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh   # Mac/Linux
# Windows: download from https://ollama.com/download

# 2. Pull a model (choose one)
ollama pull llama3.2       # Recommended — fast & capable (2GB)
ollama pull mistral        # Great for Q&A (4GB)
ollama pull gemma2:2b      # Lightweight for low-RAM machines (1.6GB)

# 3. Start Ollama
ollama serve

# 4. Clone and run the app
git clone https://github.com/YOUR_USERNAME/second-brain-ai
cd second-brain-ai
pip install -r requirements.txt
streamlit run app.py
```

Select **"🖥️ Local — Ollama (No API Key)"** in the sidebar and you're ready!

---

## ☁️ Cloud Providers (Optional)

| Provider | Model | Free Key |
|---|---|---|
| **Groq** ⭐ | LLaMA 3.3 70B | [console.groq.com](https://console.groq.com) |
| **Gemini** | gemini-2.0-flash | [aistudio.google.com](https://aistudio.google.com) |
| **OpenAI** | gpt-4o-mini | [platform.openai.com](https://platform.openai.com) |
| **Anthropic** | claude-3-5-haiku | [console.anthropic.com](https://console.anthropic.com) |
| **Mistral AI** | mistral-small | [console.mistral.ai](https://console.mistral.ai) |
| **Cohere** | command-r-plus | [dashboard.cohere.com](https://dashboard.cohere.com) |
| **Together AI** | LLaMA 3.3 70B | [api.together.xyz](https://api.together.xyz) |

---

## 🐳 Docker Compose

```bash
cp .env.example .env
docker-compose up --build
```

Open `http://localhost:8501`

---

## 🧪 Running Tests

```bash
pip install pytest pytest-cov
pytest tests/ -v
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## 🏗️ Architecture

```
User Uploads (PDF / PPTX / TXT / YouTube URL)
        ↓
  Input Validation (file type, size, URL format)
        ↓
  Document Loader + YouTube Transcript API
        ↓
  Text Chunker (configurable size + overlap)
        ↓
  ChromaDB Vector Store (embeddings + source metadata)
        ↓
  Query → Top-K Retrieval with source attribution
        ↓
  ┌─────────────────────────────┐
  │  LLM Router                 │
  │  ├── Ollama (local, free)   │
  │  └── Cloud (7 providers)    │
  │      └── Retry + backoff    │
  └─────────────────────────────┘
        ↓
  Chat / MCQ / Flashcards / Concept Map / Summary / Compare
        ↓
  SQLite Persistence (sessions, history, scores, flashcards)
```

---

## 📁 Project Structure

```
second-brain-ai/
├── app.py                              # Main Streamlit app (7 tabs)
├── pytest.ini                          # Test config
├── docker-compose.yml                  # Full stack deployment
├── .env.example                        # Environment template
├── .github/workflows/ci.yml            # GitHub Actions CI
├── src/
│   ├── config.py                       # Centralised config (dotenv)
│   ├── logger.py                       # Rotating logs
│   ├── llm/
│   │   ├── brain.py                    # Unified LLM brain (8 providers)
│   │   └── ollama_client.py            # Local Ollama HTTP client
│   ├── vectorstore/chroma_store.py     # ChromaDB + source metadata
│   ├── ingestion/loader.py             # PDF, PPTX, TXT chunker
│   ├── persistence/session_store.py    # SQLite persistence
│   ├── features/
│   │   ├── youtube_loader.py           # YouTube transcript ingestion
│   │   ├── flashcard_generator.py      # Anki CSV/JSON export
│   │   ├── quiz_engine.py              # Adaptive MCQ parser
│   │   └── concept_map.py              # Mermaid mindmap generator
│   ├── ui/dashboard.py                 # Plotly weak topic dashboard
│   └── utils/
│       ├── retry.py                    # Exponential backoff + validation
│       └── tracker.py                  # Keyword topic tracker
└── tests/
    ├── test_tracker.py
    ├── test_quiz_engine.py
    ├── test_flashcard_generator.py
    ├── test_retry.py
    ├── test_session_store.py
    └── test_ollama_client.py
```

---

## ⚙️ Configuration (.env)

```env
LOG_LEVEL=INFO
CHUNK_SIZE=500
CHUNK_OVERLAP=50
RETRIEVAL_TOP_K=5
MAX_RETRIES=3
```

---

## 🔮 Roadmap

- [ ] Phase 2 — FastAPI backend (REST API)
- [ ] Phase 3 — React frontend
- [ ] Phase 4 — PostgreSQL + Supabase Auth
- [ ] Voice Q&A mode
- [ ] Browser extension
- [ ] `pip install second-brain` package

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, standards, and PR process.

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

## 👨‍💻 Author

**Bhanu Prakash** — [@bhanuchukka2005-spec](https://github.com/bhanuchukka2005-spec)

Drop a ⭐ if this helped you!
