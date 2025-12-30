# Backend Dockerfile
# Uses Python 3.12 with uv for fast dependency installation

FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt ./

# Install Python dependencies using uv
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Run with uvicorn for ASGI support (needed for async views)
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
