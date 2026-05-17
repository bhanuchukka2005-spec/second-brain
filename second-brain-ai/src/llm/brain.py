"""
SecondBrain: unified LLM interface supporting 8 providers including
Ollama (local, no API key required).
All cloud API calls include retry logic with exponential backoff.
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

# Ollama is the first option — no API key needed
PROVIDERS: dict[str, Tuple[str, str, str]] = {
    "🖥️ Local — Ollama (No API Key)": ("ollama",    "",              "Free & private — runs on your machine"),
    "Groq (Free & Fast ⚡)":           ("groq",      "Groq API Key",  "Get free key → console.groq.com"),
    "Gemini (Google)":                 ("gemini",    "Gemini API Key","Get free key → aistudio.google.com"),
    "OpenAI (GPT-4o Mini)":            ("openai",    "OpenAI API Key","Get key → platform.openai.com"),
    "Anthropic (Claude)":              ("anthropic", "Anthropic API Key","Get key → console.anthropic.com"),
    "Mistral AI":                      ("mistral",   "Mistral API Key","Get free key → console.mistral.ai"),
    "Cohere":                          ("cohere",    "Cohere API Key","Get free key → dashboard.cohere.com"),
    "Together AI (Free Models)":       ("together",  "Together API Key","Get free key → api.together.xyz"),
}


class SecondBrain:
    """
    Unified AI brain supporting 8 LLM providers.
    Ollama runs fully locally — no API key, no internet, no cost.
    All other providers use cloud APIs with automatic retry/backoff.
    """

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

        # Only validate API key for cloud providers
        if self.provider != "ollama":
            validate_api_key(api_key, self.provider)

        self._init_client(api_key)
        logger.info(
            "SecondBrain initialized: provider=%s%s",
            self.provider,
            f" model={ollama_model}" if self.provider == "ollama" else ""
        )

    def _init_client(self, api_key: str) -> None:
        """Initialize the appropriate LLM client."""
        if self.provider == "ollama":
            # No client object needed — we call ollama_client directly
            self.client = None
            self.model = self.ollama_model
            logger.info("Ollama client ready: model=%s", self.model)

        elif self.provider == "groq":
            from groq import Groq
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.3-70b-versatile"

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
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.together.xyz/v1",
            )
            self.model = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"

        else:
            raise ValueError(
                f"Unsupported provider: '{self.provider}'. "
                f"Choose from: {list(PROVIDERS.keys())}"
            )

    def _call_ollama(self, prompt: str, max_tokens: int = 800) -> str:
        """
        Call local Ollama with reduced token limit for speed.
        Uses streaming internally so each token arrives fast.
        """
        from src.llm.ollama_client import call_ollama
        # Local models are slower — cap tokens and use tighter prompts
        return call_ollama(self.model, prompt, max_tokens)

    def stream_ollama_response(self, prompt: str):
        """
        Generator: yields tokens one by one for Streamlit st.write_stream().
        Only used for the Chat tab — gives instant feedback to the user.
        """
        from src.llm.ollama_client import stream_ollama
        yield from stream_ollama(self.model, prompt, max_tokens=600)

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def _call_cloud(self, prompt: str) -> str:
        """Call cloud LLM with automatic retry on transient errors."""
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

        return "⚠️ Unknown provider — no response generated."

    def _call(self, prompt: str) -> str:
        """Unified call — routes to local Ollama or cloud provider."""
        logger.debug(
            "LLM call: provider=%s prompt_len=%d", self.provider, len(prompt)
        )
        if self.provider == "ollama":
            return self._call_ollama(prompt)
        return self._call_cloud(prompt)

    # ── Chat ──────────────────────────────────────────────────────────────────
    def ask(
        self,
        question: str,
        chat_history: Optional[List[dict]] = None,
    ) -> Tuple[str, List[str]]:
        """
        Answer a question using RAG over the student's notes.

        Args:
            question: The student's question.
            chat_history: Previous messages for conversational memory.

        Returns:
            Tuple of (answer_text, list_of_source_filenames)
        """
        if not question or not question.strip():
            return "Please enter a question.", []

        self.tracker.log_question(question)
        chunks = self.store.query(question, n_results=config.retrieval_top_k)

        if not chunks:
            logger.warning("No chunks found for query: %s", question[:80])
            return (
                "I couldn't find relevant information in your notes. "
                "Try uploading more material or rephrasing your question.",
                [],
            )

        context = "\n\n".join(c["text"] for c in chunks)
        sources = list({c["source"] for c in chunks})

        memory = ""
        if chat_history and len(chat_history) > 1:
            recent = chat_history[-6:]
            memory = "\nPREVIOUS CONVERSATION:\n"
            memory += "\n".join(
                f"{m['role'].upper()}: {m['content']}" for m in recent
            )
            memory += "\n"

        # Shorter prompt for Ollama (local models are slower with long prompts)
        if self.provider == "ollama":
            prompt = (
                f"Answer this question using ONLY the notes below. "
                f"Be concise.\n\n"
                f"NOTES:\n{context}\n\n"
                f"Q: {question}\nA:"
            )
        else:
            prompt = (
                "You are a smart study assistant. Answer using ONLY the context "
                "below from the student's notes. If the answer is not in the context, "
                'say "This doesn\'t seem to be covered in your notes." '
                "Be clear, concise, and student-friendly.\n"
                f"{memory}\n"
                f"CONTEXT FROM NOTES:\n{context}\n\n"
                f"STUDENT QUESTION:\n{question}\n\nANSWER:"
            )

        try:
            answer = self._call(prompt)
            logger.info("Question answered: sources=%s", sources)
            return answer, sources
        except Exception as e:
            logger.error("Failed to answer question: %s", e)
            return f"⚠️ Error: {e}", []

    # ── Summarize ─────────────────────────────────────────────────────────────
    def summarize(self, topic: str = "") -> str:
        """Summarize the indexed material, optionally focused on a topic."""
        query = topic.strip() or "main concepts overview summary"
        chunks = self.store.query(query, n_results=10)
        if not chunks:
            return "Not enough material to summarize. Please upload more notes."

        context = "\n\n".join(c["text"] for c in chunks)
        focus = f"Focus on: {topic}" if topic.strip() else "Cover all major topics."
        prompt = (
            "Summarize the following study material clearly and concisely.\n"
            f"Use bullet points for key concepts. Keep it student-friendly.\n"
            f"{focus}\n\nMATERIAL:\n{context}\n\nSUMMARY:"
        )
        try:
            return self._call(prompt)
        except Exception as e:
            logger.error("Summarize failed: %s", e)
            return f"⚠️ Error generating summary: {e}"

    # ── MCQ Generation ────────────────────────────────────────────────────────
    def generate_mcqs_structured(
        self,
        topic: str,
        num_questions: int = 10,
        wrong_topics: Optional[List[str]] = None,
    ) -> Tuple[str, List[dict]]:
        """
        Generate MCQs with adaptive difficulty based on wrong_topics.

        Returns:
            Tuple of (raw_text, list_of_parsed_question_dicts)
        """
        if num_questions < 1:
            raise ValueError("num_questions must be at least 1")

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
                f"Generate exactly {num_questions} multiple choice questions "
                f"from the study material below.\n"
                f"{difficulty_hint}\n"
                "Format EXACTLY as:\n"
                "Q1. [Question]\nA) [Option]\nB) [Option]\nC) [Option]\nD) [Option]\n"
                "Answer: [Letter]\nExplanation: [Brief explanation]\n\n"
                f"STUDY MATERIAL:\n{context}\n{topic_line}\n\n"
                f"Generate {num_questions} MCQs:"
            )

        try:
            raw = self._call(prompt)
            parsed = parse_mcqs(raw)
            logger.info("Generated %d/%d MCQs", len(parsed), num_questions)
            return raw, parsed
        except Exception as e:
            logger.error("MCQ generation failed: %s", e)
            return f"⚠️ Error: {e}", []

    # ── Flashcards ────────────────────────────────────────────────────────────
    def generate_flashcards(
        self,
        topic: str,
        num_cards: int = 15,
    ) -> List[dict]:
        """Generate Anki-compatible flashcards from indexed notes."""
        if num_cards < 1:
            raise ValueError("num_cards must be at least 1")

        query = topic.strip() or "key concepts definitions"
        chunks = self.store.query(query, n_results=8)
        if not chunks:
            return []

        context = "\n\n".join(c["text"] for c in chunks)
        focus = f"Focus on: {topic}" if topic.strip() else ""

        prompt = (
            f"Create exactly {num_cards} flashcards from the study material below.\n"
            "Format EXACTLY as (repeat for each card):\n"
            "FRONT: [Question or concept]\nBACK: [Answer or definition]\n---\n\n"
            f"STUDY MATERIAL:\n{context}\n{focus}\n\n"
            f"Generate {num_cards} flashcards:"
        )

        try:
            raw = self._call(prompt)
            cards = parse_flashcards_from_text(raw)
            logger.info("Generated %d flashcards", len(cards))
            return cards
        except Exception as e:
            logger.error("Flashcard generation failed: %s", e)
            return []

    # ── Concept Map ───────────────────────────────────────────────────────────
    def generate_concept_map(self, topic: str = "") -> str:
        """Generate a Mermaid mindmap string from indexed notes."""
        query = topic.strip() or "main concepts"
        chunks = self.store.query(query, n_results=8)
        if not chunks:
            return ""

        context = "\n\n".join(c["text"] for c in chunks)
        prompt = get_concept_map_prompt(context, topic)

        try:
            raw = self._call(prompt)
            mermaid = parse_mermaid_from_response(raw)
            logger.info("Concept map generated, length=%d", len(mermaid))
            return mermaid
        except Exception as e:
            logger.error("Concept map generation failed: %s", e)
            return ""

    # ── Study Plan ────────────────────────────────────────────────────────────
    def generate_study_plan(self, weak_topics: List[str]) -> str:
        """Generate a 7-day study plan based on the student's weak topics."""
        if not weak_topics:
            return "Keep chatting with your notes and I'll identify your weak areas!"

        prompt = (
            f"You are a study coach. A student struggles most with: "
            f"{', '.join(weak_topics)}.\n"
            "Create a focused 7-day study plan. Be specific, practical, "
            "and encouraging. Include daily goals, techniques, and time estimates.\n\n"
            "STUDY PLAN:"
        )

        try:
            return self._call(prompt)
        except Exception as e:
            logger.error("Study plan generation failed: %s", e)
            return f"⚠️ Error generating study plan: {e}"

    # ── Compare Topics ────────────────────────────────────────────────────────
    def compare_topics(self, topic_a: str, topic_b: str) -> str:
        """Compare two topics side-by-side using retrieved note chunks."""
        if not topic_a.strip() or not topic_b.strip():
            raise ValueError("Both topics must be non-empty strings.")

        chunks_a = self.store.query(topic_a, n_results=4)
        chunks_b = self.store.query(topic_b, n_results=4)

        if not chunks_a:
            return f"Could not find material on '{topic_a}' in your notes."
        if not chunks_b:
            return f"Could not find material on '{topic_b}' in your notes."

        ctx_a = "\n".join(c["text"] for c in chunks_a)
        ctx_b = "\n".join(c["text"] for c in chunks_b)

        prompt = (
            "Compare and contrast these two topics from the student's notes.\n"
            "Use a clear structure: Similarities, Differences, Key Takeaways.\n\n"
            f"TOPIC A — {topic_a}:\n{ctx_a}\n\n"
            f"TOPIC B — {topic_b}:\n{ctx_b}\n\nCOMPARISON:"
        )

        try:
            return self._call(prompt)
        except Exception as e:
            logger.error("Topic comparison failed: %s", e)
            return f"⚠️ Error comparing topics: {e}"
