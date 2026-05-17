import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from src.utils.tracker import WeakTopicTracker


def render_dashboard(tracker: WeakTopicTracker):
    weak_topics = tracker.get_weak_topics(top_n=10)

    if not weak_topics:
        st.info("Ask more questions to populate the dashboard.")
        return

    topics = [t[0] for t in weak_topics]
    counts = [t[1] for t in weak_topics]

    # ── Metric row ───────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Questions Asked", tracker.total_questions())
    col2.metric("Unique Topics Tracked", len(tracker.keyword_counter))
    col3.metric("Most Queried Topic", topics[0].capitalize() if topics else "—")

    st.divider()

    col_a, col_b = st.columns(2)

    # ── Bar chart ────────────────────────────────────────────────────────────
    with col_a:
        st.subheader("Most Queried Topics")
        fig_bar = go.Figure(go.Bar(
            x=counts[::-1],
            y=[t.capitalize() for t in topics[::-1]],
            orientation="h",
            marker_color="#6366f1",
            text=counts[::-1],
            textposition="outside"
        ))
        fig_bar.update_layout(
            margin=dict(l=0, r=20, t=10, b=10),
            height=320,
            xaxis_title="Times Asked",
            yaxis_title="",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Pie chart ────────────────────────────────────────────────────────────
    with col_b:
        st.subheader("Topic Distribution")
        fig_pie = px.pie(
            names=[t.capitalize() for t in topics],
            values=counts,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_layout(
            margin=dict(l=0, r=0, t=10, b=10),
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Study plan ───────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📅 Personalized Study Plan")
    st.caption("Based on the topics you ask about most, here's what to focus on:")

    if st.button("Generate My Study Plan ✨", use_container_width=True):
        if "brain" in st.session_state and st.session_state.brain:
            weak = tracker.get_top_topic_names(5)
            with st.spinner("Crafting your personalized study plan..."):
                plan = st.session_state.brain.generate_study_plan(weak)
            st.markdown(plan)

            st.download_button(
                "📥 Download Study Plan",
                data=plan,
                file_name="my_study_plan.txt",
                mime="text/plain",
                key="download_study_plan"
            )
        else:
            st.warning("Please upload and index your material first.")
