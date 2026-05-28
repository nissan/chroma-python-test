FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ ffmpeg \
    && rm -rf /var/lib/apt/lists/*

ENV FASTEMBED_CACHE_PATH=/app/models

COPY coding_agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install shared skills package with YouTube support
COPY skills ./skills
RUN pip install --no-cache-dir -e "./skills[youtube]" && pip install --no-cache-dir "starlette==0.46.2"

COPY coding_agent/download_models.py .
RUN python download_models.py

COPY coding_agent/ .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
