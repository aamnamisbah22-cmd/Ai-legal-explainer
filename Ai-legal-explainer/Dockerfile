# Use a lightweight python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    USE_TF=0 \
    USE_TORCH=1 \
    PORT=8000

# Set working directory
WORKDIR /app

# Install system dependencies (needed for compiling certain packages if binary wheels aren't found)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU-only first to avoid massive GPU build size and save RAM/disk usage
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application files
COPY server.py .
COPY .env.example .

# Create uploads directory (to be mounted as a persistent volume in production)
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Start FastAPI server using uvicorn (disable reload for production performance)
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
