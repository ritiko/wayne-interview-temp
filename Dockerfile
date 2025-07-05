FROM python:3.11-slim

# Create a non-root user and group
RUN addgroup --system celerygroup && adduser --system --ingroup celerygroup celeryuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy the Django project into the container
COPY . .

# Create media and uploads folders if they don't exist and set permissions
RUN mkdir -p /app/media/uploads && \
    chown -R celeryuser:celerygroup /app/media

# Set full permissions for app
RUN chown -R celeryuser:celerygroup /app

# Switch to non-root user
USER celeryuser

# Collect static files (make sure STATIC_ROOT is set in settings.py)
RUN python manage.py collectstatic --noinput

# Expose the default Django port
EXPOSE 8000

# Run the Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
