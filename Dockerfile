# Use a specific, stable version of Python (Bookworm)
FROM python:3.9-bookworm

# Set the working directory to /code
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    libgl1 \
    libglx-mesa0 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# FIX: Limit compilation to 1 thread to prevent RAM crash
ENV CMAKE_BUILD_PARALLEL_LEVEL=1

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies (Now dlib will compile safely)
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of your application code
COPY . .

# Create the uploads directory inside the container
RUN mkdir -p backend/uploads && chmod 777 backend/uploads

# Expose the port Hugging Face expects (7860)
EXPOSE 7860

# Command to run the application
CMD ["python", "backend/app.py"]