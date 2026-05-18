FROM python:3.11-slim

WORKDIR /CachingProxy

# Install dependencies (Flask, Redis, Requests)
RUN pip install --no-cache-dir flask redis requests gunicorn

# Copy your application code
COPY . .

# Expose the Flask port
EXPOSE 5000

# Run the app using Gunicorn for production-ready performance
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "CachingProxy:app"]