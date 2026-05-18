"""
AI Second Brain — Streamlit UI entry point.
For the React frontend use: cd second-brain-frontend && npm run dev
For the FastAPI backend use: uvicorn api.main:app --reload --port 8000
"""
import streamlit as st
from src.logger import setup_logging
from src.config import config

setup_logging(log_dir=config.log_dir, log_level=config.log_level)

st.set_page_config(page_title="🧠 AI Second Brain", page_icon="🧠", layout="wide")

st.title("🧠 AI Second Brain")
st.info(
    "The full app is now running as a React + FastAPI stack.\n\n"
    "**Frontend:** `cd second-brain-frontend && npm run dev` → http://localhost:3000\n\n"
    "**Backend API:** `uvicorn api.main:app --reload --port 8000` → http://localhost:8000/docs"
)
