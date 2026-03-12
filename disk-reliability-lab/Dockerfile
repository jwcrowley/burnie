FROM python:3.11-slim

WORKDIR /lab

# Install system dependencies
RUN apt-get update && apt-get install -y \
    smartmontools \
    e2fsprogs \
    fio \
    hdparm \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Default command (can be overridden in compose)
CMD ["python3", "api_server.py"]
