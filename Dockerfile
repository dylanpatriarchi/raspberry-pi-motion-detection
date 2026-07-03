# Raspberry Pi Motion Detection System
# Multi-arch base image works on both x86-64 dev machines and ARM Raspberry Pi.
FROM python:3.11-slim

# System libraries required by OpenCV at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first to leverage Docker layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source.
COPY . .

# Runtime output directories (also mounted as volumes in production).
RUN mkdir -p data/captured_images logs
VOLUME ["/app/data", "/app/logs"]

# Headless by default: no preview window inside a container.
ENTRYPOINT ["python3", "main.py"]
CMD ["--no-preview"]
