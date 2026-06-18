# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8118 to the outside world
EXPOSE 8000

# Run with a single gevent worker: it handles many concurrent SSE connections
# via greenlets, and keeps the in-process update broadcast authoritative (a
# multi-worker setup would only share state through the database).
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--worker-class", "gevent", "--workers", "1", "app:app"]
