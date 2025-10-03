FROM python:3.11-slim

WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

# Install PyTorch CPU (smaller size) and other deps
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    torch==2.2.0 \
    torchvision==0.17.0 \
    --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir \
    numpy \
    pillow \
    opencv-python-headless \
    discord.py \
    tqdm \
    requests \
    onnxruntime \
    pymongo \
    motor

# Copy application code
COPY . .

# Don't create user - Railway handles this
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
