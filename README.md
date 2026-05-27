# Caching Proxy

A high-performance caching proxy server built with Flask and Redis that intercepts HTTP requests, caches responses, and reduces upstream server load.

## Overview

This project implements a forward proxy that sits between clients and an upstream server. It automatically caches GET requests and returns cached responses on subsequent requests, dramatically reducing latency and server load. Perfect for reducing expensive API calls, improving application performance, or implementing request throttling.

## Features

- **Request Caching**: Automatically caches HTTP GET responses from upstream servers
- **Redis-Backed**: Uses Redis for distributed, persistent caching across multiple instances
- **Compression**: Compresses cached data with gzip to minimize memory usage
- **Configurable Expiry**: Set custom cache TTL (time-to-live) via environment variables
- **Docker Support**: Fully containerized with Docker and Docker Compose for easy deployment
- **Thread-Safe**: Handles concurrent requests efficiently with ThreadPoolExecutor
- **Production Ready**: Deployed with Gunicorn for optimal performance

## How It Works

1. Client sends a GET request to the proxy
2. Proxy checks Redis cache for the response
3. If cached and not expired → returns cached response immediately
4. If not cached → fetches from upstream server, caches it, and returns to client
5. Cached responses are compressed to save memory

## Prerequisites

- **Python 3.11+** (if running locally)
- **Redis 7+** (for caching backend)
- **Docker & Docker Compose** (optional, for containerized deployment)


### Local Development

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start Redis (ensure it's running):
   ```bash
   redis-server
   ```

4. Set environment variables and run:
   ```bash
   # On Windows (PowerShell):
   $env:PROXY_URL = "https://api.example.com"
   $env:REDIS_HOST = "localhost"
   python -m flask run
   
   # On macOS/Linux:
   export PROXY_URL="https://api.example.com"
   export REDIS_HOST="localhost"
   python -m flask run
   ```

## Usage

### Making Requests

Simply request any path through the proxy:

```bash
# First request (fetches from upstream, caches result)
curl http://localhost:5000/api/users

# Second request (returns cached result)
curl http://localhost:5000/api/users
```

### Docker Compose Services

- **Web Service**: Flask proxy running on port 5000
- **Redis Service**: Cache backend on port 6379

## Project Structure

```
├── CachingProxy.py       # Main Flask application
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker image configuration
├── compose.yaml         # Docker Compose multi-container setup
├── LICENSE              # Project license
└── README.md            # This file
```

## Performance Benefits

- **Reduced Latency**: Cached responses return instantly (typically <1ms)
- **Lower Bandwidth**: Reduces data transfer to upstream servers
- **Improved Reliability**: Can return cached data even if upstream is slow
- **Scalability**: Redis allows caching across distributed instances

## Development

To modify the caching logic or add features:

1. Edit `CachingProxy.py`
2. Test locally with the venv setup
3. Build and test the Docker image:
   ```bash
   docker build -t caching-proxy .
   docker run -e PROXY_URL=https://api.example.com -e REDIS_HOST=redis caching-proxy
   ```

## License

See [MIT License] file for details.

## Support

For issues or questions, please refer to the project documentation or open an issue on the repository.
