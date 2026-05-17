# Contributing to AI Second Brain

Thank you for your interest in contributing! Here's everything you need to get started.

---

## 🛠️ Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/second-brain-ai
cd second-brain-ai
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pytest pytest-cov
cp .env.example .env            # fill in your API key
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing

# Run a specific test file
pytest tests/test_tracker.py -v
```

All PRs must pass tests before merging. Aim for >70% coverage on new code.

---

## 📐 Code Standards

- **Type hints** on all function signatures
- **Docstrings** on all public functions and classes
- **Logging** using `logger = logging.getLogger(__name__)` — no print statements
- **No hardcoded secrets** — use `.env` and `src/config.py`
- Run `python -m py_compile <file>` before committing

---

## 🔀 Pull Request Process

1. Fork the repo and create a branch: `git checkout -b feature/your-feature`
2. Write code + tests
3. Ensure all tests pass: `pytest tests/ -v`
4. Update `README.md` if you added a feature
5. Open a PR with a clear description of what you changed and why

---

## 🐛 Reporting Bugs

Open a GitHub Issue with:
- What you did
- What you expected
- What actually happened
- Your Python version and OS

---

## 💡 Feature Requests

Open a GitHub Issue with the `enhancement` label. Describe the use case and why it would benefit students.

---

## 📁 Project Structure Quick Reference

```
src/
├── config.py           # All configuration — edit here, not in code
├── logger.py           # Logging setup — call setup_logging() once
├── llm/brain.py        # LLM interface — add new providers here
├── features/           # Add new study features here
├── persistence/        # Database layer — add new tables here
├── utils/retry.py      # Retry logic + input validation
tests/                  # Mirror src/ structure for tests
```
