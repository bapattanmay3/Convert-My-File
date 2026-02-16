# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# These are required by WeasyPrint, pdf2image (poppler), and other conversion libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libffi-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    zlib1g-dev \
    # WeasyPrint requirements
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    # Poppler for pdf2image
    poppler-utils \
    # Pandoc for legacy doc conversion
    pandoc \
    # File type detection
    libmagic1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure the uploads directory exists
RUN mkdir -p uploads

# Make port 10000 available to the world outside this container (Render default)
EXPOSE 10000

# Define environment variable
ENV FLASK_APP=app.py
ENV RENDER=true

# Run gunicorn when the container launches
# We use --timeout to handle longer conversions
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", 1, "--threads", 1, "--timeout", 300, "--preload", "app:app"]
