FROM python:3.12-slim

WORKDIR /app

# gcc/g++ needed for some Python package compilations (lxml fallback)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Cache fastembed models in a predictable location inside the image
ENV FASTEMBED_CACHE_PATH=/app/models

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download sentence-transformers model at build time
COPY download_models.py .
RUN python download_models.py

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
