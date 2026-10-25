"""
SecondBrain: unified LLM interface supporting 8 providers including
Ollama (local, no API key required).
"""
import logging
from typing import List, Optional, Tuple

from src.vectorstore.chroma_store import ChromaStore
from src.utils.tracker import WeakTopicTracker
from src.utils.retry import retry_with_backoff, validate_api_key
from src.features.flashcard_generator import parse_flashcards_from_text
from src.features.quiz_engine import parse_mcqs, get_difficulty_prompt
from src.features.concept_map import get_concept_map_prompt, parse_mermaid_from_response
from src.config import config

logger = logging.getLogger(__name__)

PROVIDERS: dict = {
    "🖥️ Local — Ollama (No API Key)": ("ollama",    "",               "Free & private — runs on your machine"),
    "Groq (Free & Fast ⚡)":           ("groq",      "Groq API Key",   "Get free key → console.groq.com"),
    "Gemini (Google)":                 ("gemini",    "Gemini API Key", "Get free key → aistudio.google.com"),
    "OpenAI (GPT-4o Mini)":            ("openai",    "OpenAI API Key", "Get key → platform.openai.com"),
    "Anthropic (Claude)":              ("anthropic", "Anthropic API Key", "Get key → console.anthropic.com"),
    "Mistral AI":                      ("mistral",   "Mistral API Key","Get free key → console.mistral.ai"),
    "Cohere":                          ("cohere",    "Cohere API Key", "Get free key → dashboard.cohere.com"),
    "Together AI (Free Models)":       ("together",  "Together API Key","Get free key → api.together.xyz"),
}


class SecondBrain:
    def __init__(
        self,
        store: ChromaStore,
        tracker: WeakTopicTracker,
        provider: str,
        api_key: str = "",
        ollama_model: str = "llama3.2",
    ) -> None:
        self.store = store
        self.tracker = tracker
        self.provider = provider.lower().strip()
        self.ollama_model = ollama_model
        if self.provider != "ollama":
            validate_api_key(api_key, self.provider)
        self._init_client(api_key)
        logger.info("SecondBrain initialized: provider=%s", self.provider)

    def _init_client(self, api_key: str) -> None:
        if self.provider == "ollama":
            self.client = None
            self.model = self.ollama_model

        elif self.provider == "groq":
            from groq import Groq
            self.client = Groq(api_key=api_key)
            self.model = "openai/gpt-oss-20b"

        elif self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel("gemini-2.0-flash")
            self.model = "gemini-2.0-flash"

        elif self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-4o-mini"

        elif self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = "claude-3-5-haiku-20241022"

        elif self.provider == "mistral":
            from mistralai import Mistral
            self.client = Mistral(api_key=api_key)
            self.model = "mistral-small-latest"

        elif self.provider == "cohere":
            import cohere
            self.client = cohere.ClientV2(api_key=api_key)
            self.model = "command-r-plus"

        elif self.provider == "together":
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
            self.model = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"

        else:
            raise ValueError(f"Unsupported provider: '{self.provider}'")

    def _call_ollama(self, prompt: str, max_tokens: int = 600) -> str:
        from src.llm.ollama_client import call_ollama
        return call_ollama(self.model, prompt, max_tokens)

    def stream_ollama_response(self, prompt: str):
        from src.llm.ollama_client import stream_ollama
        yield from stream_ollama(self.model, prompt, max_tokens=400)

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def _call_cloud(self, prompt: str) -> str:
        if self.provider in ("groq", "openai", "together"):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=config.max_tokens,
            )
            return response.choices[0].message.content or ""

        elif self.provider == "gemini":
            response = self.client.generate_content(prompt)
            return response.text or ""

        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=config.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text or ""

        elif self.provider == "mistral":
            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""

        elif self.provider == "cohere":
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.message.content[0].text or ""

        return "⚠️ Unknown provider."

    def _call(self, prompt: str) -> str:
        if self.provider == "ollama":
            return self._call_ollama(prompt)
        return self._call_cloud(prompt)

    def ask(self, question: str, chat_history: Optional[List[dict]] = None) -> Tuple[str, List[str]]:
        if not question or not question.strip():
            return "Please enter a question.", []
        self.tracker.log_question(question)
        chunks = self.store.query(question, n_results=config.retrieval_top_k)
        if not chunks:
            return "I couldn't find relevant information in your notes. Try uploading more material.", []
        context = "\n\n".join(c["text"] for c in chunks)
        sources = list({c["source"] for c in chunks})
        memory = ""
        if chat_history and len(chat_history) > 1:
            recent = chat_history[-6:]
            memory = "\nPREVIOUS CONVERSATION:\n" + "\n".join(
                f"{m['role'].upper()}: {m['content']}" for m in recent
            ) + "\n"
        if self.provider == "ollama":
            ctx_words = chunks[0]["text"].split()[:300]
            prompt = f"Notes: {' '.join(ctx_words)}\n\nQ: {question}\nA:"
        else:
            prompt = (
                "You are a smart study assistant. Answer using ONLY the context below. "
                'If not in context say "This doesn\'t seem to be covered in your notes." '
                f"Be concise and student-friendly.\n{memory}\n"
                f"CONTEXT:\n{context}\n\nQUESTION:\n{question}\n\nANSWER:"
            )
        try:
            return self._call(prompt), sources
        except Exception as e:
            logger.error("ask() failed: %s", e)
            return f"⚠️ Error: {e}", []

    def summarize(self, topic: str = "") -> str:
        query = topic.strip() or "main concepts overview"
        chunks = self.store.query(query, n_results=10)
        if not chunks:
            return "Not enough material to summarize."
        context = "\n\n".join(c["text"] for c in chunks)
        focus = f"Focus on: {topic}" if topic.strip() else "Cover all major topics."
        prompt = f"Summarize clearly with bullet points. {focus}\n\nMATERIAL:\n{context}\n\nSUMMARY:"
        try:
            return self._call(prompt)
        except Exception as e:
            return f"⚠️ Error: {e}"

    def generate_mcqs_structured(
        self, topic: str, num_questions: int = 10, wrong_topics: Optional[List[str]] = None
    ) -> Tuple[str, List[dict]]:
        query = topic.strip() or "key concepts"
        chunks = self.store.query(query, n_results=8)
        if not chunks:
            return "Not enough material.", []
        context = "\n\n".join(c["text"] for c in chunks)
        difficulty_hint = get_difficulty_prompt(wrong_topics or [])
        topic_line = f"Topic: {topic}" if topic.strip() else ""
        if self.provider == "ollama":
            prompt = (
                f"Generate {num_questions} MCQs from the notes below.\n"
                "Format: Q1. [Question]\nA) B) C) D)\nAnswer: [Letter]\nExplanation: [brief]\n\n"
                f"NOTES:\n{context}\n{topic_line}\nGenerate {num_questions} MCQs:"
            )
        else:
            prompt = (
                f"Generate exactly {num_questions} MCQs from the study material below.\n"
                f"{difficulty_hint}\n"
                "Format EXACTLY as:\nQ1. [Question]\nA) [Option]\nB) [Option]\nC) [Option]\nD) [Option]\n"
                "Answer: [Letter]\nExplanation: [Brief explanation]\n\n"
                f"STUDY MATERIAL:\n{context}\n{topic_line}\n\nGenerate {num_questions} MCQs:"
            )
        try:
            raw = self._call(prompt)
            return raw, parse_mcqs(raw)
        except Exception as e:
            return f"⚠️ Error: {e}", []

    def generate_flashcards(self, topic: str, num_cards: int = 15) -> List[dict]:
        query = topic.strip() or "key concepts definitions"
        chunks = self.store.query(query, n_results=8)
        if not chunks:
            return []
        context = "\n\n".join(c["text"] for c in chunks)
        focus = f"Focus on: {topic}" if topic.strip() else ""
        prompt = (
            f"Create exactly {num_cards} flashcards from the study material below.\n"
            "Format EXACTLY as:\nFRONT: [Question or concept]\nBACK: [Answer]\n---\n\n"
            f"STUDY MATERIAL:\n{context}\n{focus}\n\nGenerate {num_cards} flashcards:"
        )
        try:
            return parse_flashcards_from_text(self._call(prompt))
        except Exception as e:
            logger.error("Flashcard generation failed: %s", e)
            return []

    def generate_concept_map(self, topic: str = "") -> str:
        query = topic.strip() or "main concepts"
        chunks = self.store.query(query, n_results=8)
        if not chunks:
            return ""
        context = "\n\n".join(c["text"] for c in chunks)
        try:
            return parse_mermaid_from_response(self._call(get_concept_map_prompt(context, topic)))
        except Exception as e:
            logger.error("Concept map failed: %s", e)
            return ""

    def generate_study_plan(self, weak_topics: List[str]) -> str:
        if not weak_topics:
            return "Keep chatting and I'll identify your weak areas!"
        prompt = (
            f"You are a study coach. Student struggles with: {', '.join(weak_topics)}.\n"
            "Create a focused 7-day study plan with daily goals and time estimates.\n\nSTUDY PLAN:"
        )
        try:
            return self._call(prompt)
        except Exception as e:
            return f"⚠️ Error: {e}"

    def compare_topics(self, topic_a: str, topic_b: str) -> str:
        if not topic_a.strip() or not topic_b.strip():
            raise ValueError("Both topics must be non-empty.")
        chunks_a = self.store.query(topic_a, n_results=4)
        chunks_b = self.store.query(topic_b, n_results=4)
        if not chunks_a:
            return f"No material found for '{topic_a}'."
        if not chunks_b:
            return f"No material found for '{topic_b}'."
        ctx_a = "\n".join(c["text"] for c in chunks_a)
        ctx_b = "\n".join(c["text"] for c in chunks_b)
        prompt = (
            "Compare and contrast these two topics. Use: Similarities, Differences, Key Takeaways.\n\n"
            f"TOPIC A — {topic_a}:\n{ctx_a}\n\nTOPIC B — {topic_b}:\n{ctx_b}\n\nCOMPARISON:"
        )
        try:
            return self._call(prompt)
        except Exception as e:
            return f"⚠️ Error: {e}"
