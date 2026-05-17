import streamlit as st
from src.ingestion.loader import load_documents
from src.vectorstore.chroma_store import ChromaStore
from src.llm.brain import SecondBrain, PROVIDERS
from src.llm.ollama_client import (
    is_ollama_running, get_installed_models,
    RECOMMENDED_MODELS,
    get_install_instructions
)
from src.ui.dashboard import render_dashboard
from src.utils.tracker import WeakTopicTracker
from src.utils.retry import validate_api_key, validate_file_upload, validate_youtube_url
from src.persistence.session_store import (
    init_db, save_session, list_sessions, delete_session,
    save_chat_message, load_chat_history,
    save_flashcards, load_flashcards,
    save_quiz_score, load_quiz_scores
)
from src.features.youtube_loader import fetch_transcript, get_video_title
from src.features.flashcard_generator import export_to_csv, export_to_json
from src.logger import setup_logging
from src.config import config
import logging

setup_logging(log_dir=config.log_dir, log_level=config.log_level)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="🧠 AI Second Brain",
    page_icon="🧠",
    layout="wide"
)
init_db()

# ── Session state defaults ────────────────────────────────────────────────────
defaults = {
    "brain": None,
    "chat_history": [],
    "tracker": WeakTopicTracker(),
    "session_id": None,
    "flashcards": [],
    "quiz_questions": [],
    "quiz_index": 0,
    "quiz_score": 0,
    "quiz_wrong_topics": [],
    "quiz_active": False,
    "store": None,
    "quiz_result_saved": False,
    "fc_index": 0,
    "fc_show_back": False,
    "quiz_topic_label": "",
    "ollama_model": "llama3.2",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🧠 AI Second Brain")
    st.caption("Your personal AI study companion")
    st.divider()

    # ── Provider Selection ────────────────────────────────────────────────────
    st.subheader("🔑 LLM Provider")
    provider_label = st.selectbox(
        "Choose your AI provider",
        list(PROVIDERS.keys()),
        index=0
    )
    provider_id, key_label, key_hint = PROVIDERS[provider_label]

    # ── Ollama Section ────────────────────────────────────────────────────────
    if provider_id == "ollama":
        ollama_ok = is_ollama_running()

        if ollama_ok:
            st.success("✅ Ollama is running!")
            installed = get_installed_models()

            if installed:
                selected_model = st.selectbox(
                    "Choose a model",
                    installed,
                    index=0,
                    help="Models you have pulled via `ollama pull <model>`"
                )
                st.session_state.ollama_model = selected_model

                # Show model info if it's a recommended one
                if selected_model in RECOMMENDED_MODELS:
                    info = RECOMMENDED_MODELS[selected_model]
                    st.caption(
                        f"{info['speed']} · {info['size']} · "
                        f"{info['quality']} · {info['desc']}"
                    )

                # Speed benchmark warning
                if st.button("⚡ Test Speed", use_container_width=True, key="bench_btn"):
                    with st.spinner(f"Testing {selected_model} speed..."):
                        tps = benchmark_model(selected_model, timeout_sec=20)
                    if tps is None:
                        st.error(
                            "❌ Model is too slow or timed out.\n\n"
                            "Try: `ollama pull gemma2:2b` (fastest)"
                        )
                    elif tps < 2:
                        st.warning(
                            f"⚠️ {tps} tokens/sec — very slow. "
                            "Try gemma2:2b or use a cloud provider (Groq is free)."
                        )
                    elif tps < 5:
                        st.info(f"🐢 {tps} tokens/sec — usable but slow.")
                    else:
                        st.success(f"✅ {tps} tokens/sec — good speed!")
            else:
                st.warning("⚠️ No models installed yet.")
                st.markdown("**Pull a model first:**")
                st.code("ollama pull llama3.2", language="bash")

            # Show recommended models not yet installed
            not_installed = [
                m for m in RECOMMENDED_MODELS if m not in installed
            ]
            if not_installed:
                with st.expander("📦 More models you can pull"):
                    for m in not_installed:
                        info = RECOMMENDED_MODELS[m]
                        st.caption(
                            f"`ollama pull {m}` — {info['desc']} "
                            f"({info['size']}, {info['speed']})"
                        )
            api_key = ""  # No API key needed

        else:
            st.error("❌ Ollama is not running")
            with st.expander("📖 How to set up Ollama (free)", expanded=True):
                st.markdown(get_install_instructions())
            api_key = ""

    # ── Cloud Provider Section ────────────────────────────────────────────────
    else:
        api_key = st.text_input(key_label, type="password")
        st.caption(f"ℹ️ {key_hint}")

    st.divider()

    # ── Saved Sessions ────────────────────────────────────────────────────────
    st.subheader("📚 Saved Sessions")
    sessions = list_sessions()
    if sessions:
        for s in sessions:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(
                    f"📖 {s['name']}",
                    key=f"load_{s['id']}",
                    use_container_width=True
                ):
                    can_load = (
                        (provider_id == "ollama" and is_ollama_running())
                        or (provider_id != "ollama" and api_key)
                    )
                    if can_load:
                        try:
                            if provider_id != "ollama":
                                validate_api_key(api_key, provider_id)
                            store = ChromaStore()
                            st.session_state.store = store
                            st.session_state.session_id = s["id"]
                            st.session_state.chat_history = load_chat_history(s["id"])
                            st.session_state.tracker = WeakTopicTracker()
                            st.session_state.brain = SecondBrain(
                                store,
                                st.session_state.tracker,
                                provider=provider_id,
                                api_key=api_key,
                                ollama_model=st.session_state.ollama_model,
                            )
                            st.session_state.flashcards = load_flashcards(s["id"])
                            st.success(f"Loaded: {s['name']}")
                            logger.info("Session loaded: id=%s", s["id"])
                        except Exception as e:
                            st.error(f"❌ {e}")
                    else:
                        if provider_id == "ollama":
                            st.warning("Start Ollama first.")
                        else:
                            st.warning("Enter API key first.")
            with col2:
                if st.button("🗑️", key=f"del_{s['id']}"):
                    delete_session(s["id"])
                    st.rerun()
    else:
        st.caption("No saved sessions yet.")

    st.divider()

    # ── Upload Material ───────────────────────────────────────────────────────
    st.subheader("📂 Upload Study Material")
    session_name = st.text_input(
        "Session name", placeholder="e.g. DevOps Week 3"
    )
    uploaded_files = st.file_uploader(
        "Upload PDFs, PPTs, or TXT files",
        type=["pdf", "pptx", "txt"],
        accept_multiple_files=True
    )
    yt_url = st.text_input(
        "🎥 Or paste a YouTube URL",
        placeholder="https://youtube.com/watch?v=..."
    )

    # Determine if we're ready to process
    ollama_ready = provider_id == "ollama" and is_ollama_running() and bool(get_installed_models())
    cloud_ready = provider_id != "ollama" and bool(api_key)
    has_content = bool(uploaded_files) or bool(yt_url.strip())
    can_process = has_content and (ollama_ready or cloud_ready)

    if can_process:
        if st.button("🚀 Process & Index", use_container_width=True):
            with st.spinner("Reading and indexing your material..."):
                try:
                    all_docs = []
                    file_names = []

                    if uploaded_files:
                        for uf in uploaded_files:
                            validate_file_upload(uf.name, uf.size)
                        all_docs += load_documents(uploaded_files)
                        file_names += [f.name for f in uploaded_files]

                    if yt_url.strip():
                        validate_youtube_url(yt_url.strip())
                        yt_docs = fetch_transcript(yt_url.strip())
                        all_docs += yt_docs
                        title = get_video_title(yt_url.strip())
                        file_names.append(f"YouTube: {title}")

                    store = ChromaStore()
                    store.index(all_docs)
                    st.session_state.store = store

                    name = session_name.strip() or f"Session ({len(file_names)} files)"
                    sid = save_session(name, file_names, len(all_docs))
                    st.session_state.session_id = sid
                    st.session_state.chat_history = []
                    st.session_state.tracker = WeakTopicTracker()
                    st.session_state.brain = SecondBrain(
                        store,
                        st.session_state.tracker,
                        provider=provider_id,
                        api_key=api_key,
                        ollama_model=st.session_state.ollama_model,
                    )
                    st.session_state.flashcards = []
                    st.success(
                        f"✅ Indexed {len(all_docs)} chunks "
                        f"from {len(file_names)} source(s)!"
                    )
                    logger.info(
                        "Session created: name=%s chunks=%d", name, len(all_docs)
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
                    logger.error("Indexing failed: %s", e)
    elif has_content and not (ollama_ready or cloud_ready):
        if provider_id == "ollama":
            st.warning("⚠️ Start Ollama and pull a model first.")
        else:
            st.warning("⚠️ Enter your API key first.")

    st.divider()
    st.caption("Built by Bhanu Prakash 🚀")

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "💬 Chat",
    "📊 Dashboard",
    "📝 MCQ Quiz",
    "🃏 Flashcards",
    "🗺️ Concept Map",
    "📄 Summarize",
    "🔀 Compare",
])

# ── Shared "not ready" helper ─────────────────────────────────────────────────
def not_ready_msg():
    if provider_id == "ollama":
        if not is_ollama_running():
            st.error("❌ Ollama is not running. Start it with: `ollama serve`")
        elif not get_installed_models():
            st.warning("⚠️ No models installed. Run: `ollama pull llama3.2`")
        else:
            st.info("👈 Upload your study material and click **Process & Index**.")
    else:
        st.info(
            "👈 Choose a provider, enter your API key, "
            "upload study material, and click **Process & Index**."
        )

# ── TAB 1: Chat ───────────────────────────────────────────────────────────────
with tab1:
    st.subheader("💬 Chat with your notes")
    if not st.session_state.brain:
        not_ready_msg()
    else:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ask anything from your notes..."):
            st.session_state.chat_history.append(
                {"role": "user", "content": prompt}
            )
            if st.session_state.session_id:
                save_chat_message(st.session_state.session_id, "user", prompt)

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                brain = st.session_state.brain

                if brain.provider == "ollama":
                    # Stream tokens word-by-word for Ollama (no waiting!)
                    # First retrieve context + sources
                    chunks = brain.store.query(prompt, n_results=3)
                    sources = list({c["source"] for c in chunks}) if chunks else []
                    context = "\n\n".join(c["text"] for c in chunks) if chunks else ""

                    if not chunks:
                        response = "I couldn\'t find relevant information in your notes."
                        st.markdown(response)
                    else:
                        ollama_prompt = (
                            f"Answer this question using ONLY the notes below. "
                            f"Be concise.\n\n"
                            f"NOTES:\n{context}\n\n"
                            f"Q: {prompt}\nA:"
                        )
                        response = st.write_stream(
                            brain.stream_ollama_response(ollama_prompt)
                        )
                        brain.tracker.log_question(prompt)
                else:
                    # Cloud providers — full response at once
                    with st.spinner("Thinking..."):
                        response, sources = brain.ask(
                            prompt, st.session_state.chat_history
                        )
                    st.markdown(response)

                if sources:
                    with st.expander("📎 Sources used"):
                        for s in sources:
                            st.caption(f"• {s}")

            st.session_state.chat_history.append(
                {"role": "assistant", "content": response}
            )
            if st.session_state.session_id:
                save_chat_message(
                    st.session_state.session_id, "assistant", response
                )

# ── TAB 2: Dashboard ──────────────────────────────────────────────────────────
with tab2:
    st.subheader("📊 Weak Topics Dashboard")
    if st.session_state.session_id:
        scores = load_quiz_scores(st.session_state.session_id)
        if scores:
            st.subheader("🏆 Quiz Score History")
            for s in scores[:5]:
                pct = round(s["score"] / s["total"] * 100)
                st.metric(
                    label=f"Quiz — {s['topic'] or 'General'} · {s['timestamp'][:10]}",
                    value=f"{s['score']}/{s['total']}",
                    delta=f"{pct}%"
                )
            st.divider()

    if st.session_state.tracker.has_data():
        render_dashboard(st.session_state.tracker)
    else:
        st.info(
            "Start chatting with your notes and the dashboard "
            "will track your knowledge gaps here."
        )

# ── TAB 3: Adaptive MCQ Quiz ──────────────────────────────────────────────────
with tab3:
    st.subheader("📝 Adaptive MCQ Quiz")
    if not st.session_state.brain:
        not_ready_msg()
    else:
        if not st.session_state.quiz_active:
            topic = st.text_input(
                "Quiz topic (or leave blank for random)", key="quiz_topic"
            )
            num_q = st.slider("Number of questions", 5, 20, 10, key="quiz_num")

            if st.button("⚡ Start Quiz", use_container_width=True):
                with st.spinner("Generating adaptive quiz..."):
                    _, parsed = st.session_state.brain.generate_mcqs_structured(
                        topic, num_q, st.session_state.quiz_wrong_topics
                    )
                if parsed:
                    st.session_state.quiz_questions = parsed
                    st.session_state.quiz_index = 0
                    st.session_state.quiz_score = 0
                    st.session_state.quiz_active = True
                    st.session_state.quiz_topic_label = topic
                    st.rerun()
                else:
                    st.error("Could not parse quiz questions. Try again.")
        else:
            questions = st.session_state.quiz_questions
            idx = st.session_state.quiz_index

            if idx < len(questions):
                q = questions[idx]
                total = len(questions)
                st.progress(idx / total, text=f"Question {idx + 1} of {total}")
                st.markdown(f"### Q{idx + 1}. {q['question']}")

                answer = st.radio(
                    "Choose your answer:",
                    list(q["options"].items()),
                    format_func=lambda x: f"{x[0]}) {x[1]}",
                    key=f"q_{idx}"
                )

                if st.button("Submit Answer ✅", key=f"submit_{idx}"):
                    chosen = answer[0]
                    correct = q["answer"]
                    if chosen == correct:
                        st.success(f"✅ Correct! {q.get('explanation', '')}")
                        st.session_state.quiz_score += 1
                    else:
                        st.error(
                            f"❌ Wrong. Correct: {correct}. "
                            f"{q.get('explanation', '')}"
                        )
                        words = q["question"].split()[:3]
                        st.session_state.quiz_wrong_topics.extend(words)

                    st.session_state.quiz_index += 1
                    st.rerun()
            else:
                score = st.session_state.quiz_score
                total = len(questions)
                pct = round(score / total * 100)

                if not st.session_state.get("quiz_result_saved", False):
                    st.balloons()
                    if st.session_state.session_id:
                        save_quiz_score(
                            st.session_state.session_id,
                            score, total,
                            st.session_state.get("quiz_topic_label", "")
                        )
                    st.session_state.quiz_result_saved = True

                st.markdown("## 🎉 Quiz Complete!")
                col1, col2, col3 = st.columns(3)
                col1.metric("Score", f"{score}/{total}")
                col2.metric("Percentage", f"{pct}%")
                col3.metric(
                    "Grade",
                    "A" if pct >= 90 else
                    "B" if pct >= 75 else
                    "C" if pct >= 60 else "F"
                )

                if st.button("🔄 Retake (Harder)", use_container_width=True):
                    st.session_state.quiz_active = False
                    st.session_state.quiz_result_saved = False
                    st.rerun()
                if st.button("🆕 New Quiz", use_container_width=True):
                    st.session_state.quiz_active = False
                    st.session_state.quiz_wrong_topics = []
                    st.session_state.quiz_result_saved = False
                    st.session_state.quiz_topic_label = ""
                    st.rerun()

# ── TAB 4: Flashcards ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("🃏 Flashcards")
    if not st.session_state.brain:
        not_ready_msg()
    else:
        col1, col2 = st.columns(2)
        with col1:
            fc_topic = st.text_input("Topic for flashcards", key="fc_topic")
        with col2:
            fc_num = st.slider("Number of cards", 5, 30, 15, key="fc_num")

        if st.button("🃏 Generate Flashcards", use_container_width=True):
            with st.spinner("Creating flashcards..."):
                cards = st.session_state.brain.generate_flashcards(fc_topic, fc_num)
            if cards:
                st.session_state.flashcards = cards
                if st.session_state.session_id:
                    save_flashcards(st.session_state.session_id, cards, fc_topic)
                st.success(f"✅ Generated {len(cards)} flashcards!")
            else:
                st.warning("Could not generate flashcards. Try a different topic.")

        if st.session_state.flashcards:
            st.divider()
            cards = st.session_state.flashcards
            idx = st.session_state.fc_index % len(cards)
            card = cards[idx]

            st.markdown(f"**Card {idx + 1} of {len(cards)}**")
            if not st.session_state.fc_show_back:
                st.info(f"**FRONT:**\n\n{card['front']}")
                if st.button("👁️ Reveal Answer", use_container_width=True):
                    st.session_state.fc_show_back = True
                    st.rerun()
            else:
                st.success(f"**BACK:**\n\n{card['back']}")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("⬅️ Previous", use_container_width=True):
                        st.session_state.fc_index = max(0, idx - 1)
                        st.session_state.fc_show_back = False
                        st.rerun()
                with col_b:
                    if st.button("➡️ Next", use_container_width=True):
                        st.session_state.fc_index = idx + 1
                        st.session_state.fc_show_back = False
                        st.rerun()

            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "📥 Export as CSV (Anki)",
                    data=export_to_csv(cards),
                    file_name="flashcards.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with c2:
                st.download_button(
                    "📥 Export as JSON",
                    data=export_to_json(cards),
                    file_name="flashcards.json",
                    mime="application/json",
                    use_container_width=True
                )

# ── TAB 5: Concept Map ────────────────────────────────────────────────────────
with tab5:
    st.subheader("🗺️ Concept Map")
    if not st.session_state.brain:
        not_ready_msg()
    else:
        cm_topic = st.text_input(
            "Topic for concept map (or leave blank for full overview)",
            key="cm_topic"
        )
        if st.button("🗺️ Generate Concept Map", use_container_width=True):
            with st.spinner("Building concept map..."):
                mermaid_code = st.session_state.brain.generate_concept_map(cm_topic)
            if mermaid_code:
                st.markdown("### Your Concept Map")
                st.markdown(f"```mermaid\n{mermaid_code}\n```")
                st.download_button(
                    "📥 Download Mermaid Code",
                    data=mermaid_code,
                    file_name="concept_map.mmd",
                    mime="text/plain"
                )
            else:
                st.warning("Could not generate concept map. Try again.")

# ── TAB 6: Summarize ──────────────────────────────────────────────────────────
with tab6:
    st.subheader("📄 Summarize Your Notes")
    if not st.session_state.brain:
        not_ready_msg()
    else:
        sum_topic = st.text_input(
            "Topic to summarize (or leave blank for full summary)",
            key="sum_topic"
        )
        if st.button("📄 Generate Summary", use_container_width=True):
            with st.spinner("Summarizing..."):
                summary = st.session_state.brain.summarize(sum_topic)
            st.markdown(summary)
            st.download_button(
                "📥 Download Summary",
                data=summary,
                file_name="summary.txt",
                mime="text/plain"
            )

# ── TAB 7: Compare Topics ─────────────────────────────────────────────────────
with tab7:
    st.subheader("🔀 Compare Two Topics")
    if not st.session_state.brain:
        not_ready_msg()
    else:
        col1, col2 = st.columns(2)
        with col1:
            topic_a = st.text_input("Topic A", placeholder="e.g. Docker")
        with col2:
            topic_b = st.text_input("Topic B", placeholder="e.g. Kubernetes")

        if st.button("🔀 Compare", use_container_width=True):
            if topic_a.strip() and topic_b.strip():
                with st.spinner("Comparing topics..."):
                    comparison = st.session_state.brain.compare_topics(
                        topic_a, topic_b
                    )
                st.markdown(comparison)
                st.download_button(
                    "📥 Download Comparison",
                    data=comparison,
                    file_name="comparison.txt",
                    mime="text/plain"
                )
            else:
                st.warning("Please enter both topics.")
