# Use Python 3.9 as the base image
FROM python:3.9

# Set the working directory to /code
WORKDIR /code

# Install system dependencies required for OpenCV and Dlib
RUN apt-get update && apt-get install -y \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of your application code
COPY . .

# Create the uploads directory inside the container (to prevent permission errors)
RUN mkdir -p backend/uploads && chmod 777 backend/uploads

# Expose the port Hugging Face expects (7860)
EXPOSE 7860

# Command to run the application
# We use 'python' to run the app directly, ensuring __file__ paths work correctly
CMD ["python", "backend/app.py"]