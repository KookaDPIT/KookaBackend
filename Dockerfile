FROM python:3.11-slim

# Tesseract + pachetele de limba. eng pentru cifre si cuvinte tip EXP/BEST BEFORE,
# ron pentru etichete romanesti (expira, valabil pana la).
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-ron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render injecteaza PORT la runtime, deci forma shell (nu exec) ca sa se expandeze.
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
