FROM python:3.11-slim
WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# install python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY . .

ENV PORT=8000
EXPOSE 8000

# Use a shell form so the PORT environment variable is expanded at runtime
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
