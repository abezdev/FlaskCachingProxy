import gzip
import os
import json
from concurrent.futures import ThreadPoolExecutor

import requests
from flask import Flask, Response, g, request
from redis import ConnectionPool, Redis


app = Flask(__name__)

PROXY_URL = os.environ.get("PROXY_URL")
print(f"Starting Caching Proxy with upstream URL: {PROXY_URL}")

PROXY_EXPIRY = int(os.environ.get("PROXY_EXPIRY", 1800))  # Seconds
print(f"Cache expiry set to: {PROXY_EXPIRY} seconds")

REDIS_HOST = os.environ.get("REDIS_HOST")
print(f"Connecting to Redis at: {REDIS_HOST}")

REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
print(f"Using Redis port: {REDIS_PORT}")

REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")

#replace with MongoDB
# Setup the global pool
redis_pool = ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=0,
    max_connections=20,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
)


executor = ThreadPoolExecutor(max_workers=10)

# Setup ONE global thread-safe client (Remove @app.before_request completely) 
r = Redis(connection_pool=redis_pool)



def fetch_from_upstream(url):
    """Fetch data from upstream server"""
    try:
        response = requests.get(
            url,
            timeout=(3, 10),
            stream=True,
            headers={
                "User-Agent": "CachingProxy/1.0",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            },
        )
        return response
    except requests.RequestException as e:
        print(f"Error fetching from upstream: {e}")
        return None


def compress_data(data):
    # Separate the body (bytes) from the metadata (dict)
    meta = {
        "status_code": data["status_code"],
        "headers": data["headers"]
    }
    # Encode metadata to JSON, then combine with the body using a separator
    # Or better yet: store them in a Redis Hash instead of one big string
    return gzip.compress(json.dumps(meta).encode() + b"|||" + data["content"])

def decompress_data(compressed_data):
    raw = gzip.decompress(compressed_data)
    meta_part, body_part = raw.split(b"|||", 1)
    meta = json.loads(meta_part.decode())
    return {
        "status_code": meta["status_code"],
        "headers": meta["headers"],
        "content": body_part
    }

@app.route("/", defaults={"path": ""}, methods=["GET"])
@app.route("/<path:path>", methods=["GET"])
def caching_proxy(path):
    if path == "favicon.ico" or path == "/favicon.ico":
        return Response("favicon", status=204)
    print(f"Received drrr for path: {path}")
    cache_key = f"cache:{request.full_path}"
    print(f"test 1 - Cache key: {cache_key}")
    try:
        # Use global 'r' client directly
        cached_data = r.get(cache_key)
        if cached_data is not None:
            # Cache hit - decompress and return
            response_data = decompress_data(cached_data)
            print(f"test 4 - Response data: {response_data}")
            response = Response(
                response_data["content"],
                response_data["status_code"],
                response_data["headers"],
            )
            response.headers["X-Cache"] = "HIT"
 
            return response
    except Exception as e:
        # Cache error - continue to fetch from upstream
        print(f"Error accessing cache: {e}")
        pass

    # Cache miss - fetch from upstream
    print(f"test 2 - Cache miss for key: {cache_key}")
    full_uri = f"{PROXY_URL}{request.full_path}"
    print(f"Fetching full_uri from upstream: {full_uri}")
    upstream_response = fetch_from_upstream(full_uri)

    if upstream_response is None:
        return Response("Upstream server error", 502)

    # Prepare response
    response = Response(
        upstream_response.content,
        upstream_response.status_code,
        upstream_response.headers.items(),
    )
    response.headers["X-Cache"] = "MISS"

    # Cache the response asynchronously (fire and forget)
    print(f"test 3 - Cache the response asynchronously (fire and forget)")
    if upstream_response.status_code == 200:
        response_data = {
            "content": upstream_response.content,
            "status_code": upstream_response.status_code,
            "headers": dict(upstream_response.headers),
        }
        print(f"test 5 - Response data to cache: {response_data['content']}")
        # Store in cache asynchronously
        # Pass the thread-safe global 'r' safely into the executor
        executor.submit(store_in_cache, r, cache_key, response_data, PROXY_EXPIRY)

    return response


@app.route('/testCounter', methods=['GET'])
def testCounter():
    # Increment a visitor counter in Redis
    visits = r.incr('counter')
    return f"Hello World! This page has been viewed {visits} times."

def store_in_cache(redis_client, key, data, expiry):
    """Store data in cache asynchronously"""
    try:
        compressed_data = compress_data(data)
        redis_client.set(key, compressed_data, ex=expiry)
    except Exception as e:
        # Log error but don't affect the response
        pass


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.route("/cache/clear", methods=["POST"])
def clear_cache():
    """Clear cache endpoint"""
    try:
        r.flushdb() # Use global client
        return {"status": "cache cleared"}
    except Exception as e:
        return {"error": str(e)}, 500
    


if __name__ == "__main__":    app.run(host="0.0.0.0", port=5000)