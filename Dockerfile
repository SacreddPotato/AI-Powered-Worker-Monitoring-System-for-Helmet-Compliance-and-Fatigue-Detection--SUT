# Use Miniconda (comes with pre-built binaries for dlib)
FROM continuumio/miniconda3

# Set working directory
WORKDIR /app

# Install system dependencies (needed for OpenCV & Dlib)
# We use standard Debian packages here; miniconda is based on Debian
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 1. Install dlib from Conda-Forge (FAST, uses pre-built binary)
RUN conda install -y -c conda-forge dlib

# 2. Install the rest of your Python packages
COPY requirements.txt .
# Remove dlib from requirements.txt so pip doesn't try to compile it again
RUN sed -i '/dlib/d' requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Command to run your app
CMD ["python", "app.py"]