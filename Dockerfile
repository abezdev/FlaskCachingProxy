FROM python:3.11-slim

WORKDIR /CachingProxy

# Copy your application code
COPY . .

# Install dependencies (Flask, Redis, Requests)
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask port
EXPOSE 5000

# Run the app using Gunicorn for production-ready performance
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "CachingProxy:app"]