FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway (and most cloud hosts) inject a dynamic $PORT at runtime — the
# container must listen on whatever port they assign, not a fixed one.
# Default to 8000 for local `docker build && docker run` without compose.
EXPOSE 8000

# CMD (not ENTRYPOINT) is what makes this Dockerfile safely overridable.
# docker-compose's `command:` REPLACES CMD entirely, but only APPENDS to
# ENTRYPOINT — that mismatch was the bug: the old ENTRYPOINT hardcoded
# Streamlit, so overriding with a uvicorn command never actually worked.
#
# Shell form (not exec-array form) is required here so ${PORT:-8000}
# actually gets expanded by the shell at container start.
CMD sh -c "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"