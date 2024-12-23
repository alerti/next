# Use Debian Bullseye slim as base
FROM debian:bullseye-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libreadline-dev \
    libsqlite3-dev \
    libgdbm-dev \
    libdb5.3-dev \
    libbz2-dev \
    libexpat1-dev \
    liblzma-dev \
    tk-dev \
    libffi-dev \
    libgmp-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python 3.13
RUN wget https://www.python.org/ftp/python/3.13.0/Python-3.13.0.tgz \
    && tar xzf Python-3.13.0.tgz \
    && cd Python-3.13.0 \
    && ./configure --enable-optimizations \
    && make altinstall \
    && cd .. \
    && rm -rf Python-3.13.0 Python-3.13.0.tgz

# Set Python path and install core packages
ENV PATH="/usr/local/bin:${PATH}"
RUN python3.13 -m ensurepip \
    && python3.13 -m pip install --no-cache-dir --upgrade \
    pip \
    setuptools \
    wheel \
    python-dotenv

# Install dependencies
COPY requirements.txt .
RUN python3.13 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Flask environment
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST=0.0.0.0

# Expose port
EXPOSE 5000

# Run Flask
CMD ["python3.13", "-m", "flask", "run", "--host=0.0.0.0"]
