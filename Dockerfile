# --- Stage 1: Build Frontend ---
FROM node:20-slim as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Final Image ---
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn uvicorn

# Copy backend code
COPY src/ ./src/
COPY .env .

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./static

# Expose port
EXPOSE 8000

# Command to run with Gunicorn for scaling
CMD ["gunicorn", "src.api:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
