# ─────────────────────────────────────────
# Base image — Python 3.12 slim version
# ─────────────────────────────────────────
FROM python:3.12-slim

# ─────────────────────────────────────────
# Set working directory inside container
# ─────────────────────────────────────────
WORKDIR /app

# ─────────────────────────────────────────
# Install system dependencies
# (required for some Python packages like torch)
# ─────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ─────────────────────────────────────────
# Copy and install Python dependencies first
# (Docker caches this layer if requirements.txt
# doesn't change — speeds up rebuilds)
# ─────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────
# Copy the rest of the application code
# ─────────────────────────────────────────
COPY . .

# ─────────────────────────────────────────
# Create required directories
# ─────────────────────────────────────────
RUN mkdir -p data/uploads data/chroma_db

# ─────────────────────────────────────────
# Expose the port FastAPI runs on
# ─────────────────────────────────────────
EXPOSE 8000

# ─────────────────────────────────────────
# Command to run when container starts
# ─────────────────────────────────────────
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]