FROM continuumio/miniconda3

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 curl && \
    rm -rf /var/lib/apt/lists/*

# Install dlib via conda
RUN conda install -y -c conda-forge dlib

# Copy project
COPY . /app
WORKDIR /app

# Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Frontend build
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    cd frontend && npm ci && npm run build

# Django setup
WORKDIR /app/backend
RUN python manage.py collectstatic --noinput 2>/dev/null; true

# Uploads directory
RUN mkdir -p uploads/dev_videos && chmod -R 777 uploads

EXPOSE 7860

CMD ["daphne", "-b", "0.0.0.0", "-p", "7860", "sentinel.asgi:application"]
