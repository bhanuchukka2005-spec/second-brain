# 🧠 NoteMind — React Frontend

Modern React frontend for the NoteMind project.
Built with Vite, TypeScript, Tailwind CSS, and Zustand.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Copy env file
cp .env.example .env.local

# 3. Make sure the FastAPI backend is running
cd ../second-brain-ai
uvicorn api.main:app --reload --port 8000

# 4. Start the dev server
npm run dev
```

Open `http://localhost:3000`

---

## 📁 Structure

```
src/
├── api/
│   └── client.ts          # Axios API client (auth, sessions, chat, study)
├── components/
│   ├── chat/
│   │   └── ChatPanel.tsx  # Chat with streaming support
│   ├── flashcards/
│   │   └── FlashcardViewer.tsx
│   ├── layout/
│   │   ├── AppLayout.tsx  # Sidebar + nav
│   │   ├── AuthGuard.tsx  # Protected route wrapper
│   │   └── ProviderPicker.tsx
│   └── quiz/
│       └── QuizView.tsx   # Adaptive MCQ quiz
├── pages/
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   └── SessionPage.tsx    # Main dashboard
├── store/
│   └── index.ts           # Zustand stores (auth, sessions, chat, provider)
├── types/
│   └── index.ts           # TypeScript types (match FastAPI schemas)
├── App.tsx                # Routes
└── main.tsx               # Entry point
```

---

## 🛠 Tech Stack

- **React 18** + **TypeScript**
- **Vite** — fast dev server with API proxy
- **Tailwind CSS** — utility-first styling
- **Zustand** — lightweight global state
- **Axios** — HTTP client with auth interceptor
- **React Router v6** — client-side routing

---

## 📦 Build for Production

```bash
npm run build
# Output in dist/ — serve with any static host
```

---

## 🔗 Connect to Backend

The Vite dev server proxies `/api/*` to `http://localhost:8000`.
In production, set `VITE_API_URL` in `.env.local` to your backend URL.
