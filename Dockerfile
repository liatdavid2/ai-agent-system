# Base image (CPU only)
FROM python:3.10-slim

# Prevent python from buffering stdout + force CPU
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=""

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install python dependencies
# torch is installed separately in Dockerfile (CPU-only)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
       torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose port (optional)
EXPOSE 8000

# Default command
CMD ["python", "main.py"]