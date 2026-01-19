# Use Miniconda (which has the pre-compiled binaries we need)
FROM continuumio/miniconda3

WORKDIR /code

# 1. Install System Deps (OpenCV still needs these)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install dlib from Conda-Forge (PRE-COMPILED! No building!)
# This takes seconds, not minutes.
RUN conda install -y -c conda-forge dlib

# 3. Copy requirements (BUT REMOVE 'dlib' FROM IT FIRST)
COPY requirements.txt .

# 4. Install the rest of your app using pip
# (We use --ignore-installed to stop pip from fighting with Conda)
RUN pip install --no-cache-dir --ignore-installed -r requirements.txt

COPY . .

# Create uploads folder
RUN mkdir -p backend/uploads && chmod 777 backend/uploads

EXPOSE 7860

# We use 'python' provided by Conda
CMD ["python", "backend/app.py"]