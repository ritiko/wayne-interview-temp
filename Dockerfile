FROM python:3.11-slim

# Create a non-root user and group
RUN addgroup --system celerygroup && adduser --system --ingroup celerygroup celeryuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

#Fix: use netcat-openbsd instead of virtual 'netcat'
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy project files
COPY . .

# Create media and uploads folders if they don't exist and set permissions
RUN mkdir -p /app/media/uploads && \
    chown -R celeryuser:celerygroup /app/media

# Set full permissions for app
RUN chown -R celeryuser:celerygroup /app

# Copy entrypoint and wait-for-postgres scripts
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER celeryuser

# Expose the Django app port
EXPOSE 8000

# Set entrypoint to the custom script
ENTRYPOINT ["/entrypoint.sh"]