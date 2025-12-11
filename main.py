import os
from typing import Optional
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import httpx

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Authentication Proxy Layer")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Get backend URLs from environment variables
QUERY_URL = os.getenv("QUERY_URL")
BACKEND_FRO_FRONTEND_URL = os.getenv("BACKEND_FRO_FRONTEND_URL")

AUTHENTICATION_HEADER_NAME_BFF=os.getenv("AUTHENTICATION_HEADER_NAME_BFF")
AUTHENTICATION_HEADER_NAME_QUERY=os.getenv("AUTHENTICATION_HEADER_NAME_QUERY")

BFF_KEY=os.getenv("BFF_KEY")
QUERY_KEY=os.getenv("QUERY_KEY")

# Validate that required environment variables are set
if not QUERY_URL:
    raise ValueError("QUERY_URL environment variable is not set")
if not BACKEND_FRO_FRONTEND_URL:
    raise ValueError("BACKEND_FRO_FRONTEND_URL environment variable is not set")
if not AUTHENTICATION_HEADER_NAME_BFF:
    raise ValueError("AUTHENTICATION_HEADER_NAME_BFF environment variable is not set")
if not AUTHENTICATION_HEADER_NAME_QUERY:
    raise ValueError("AUTHENTICATION_HEADER_NAME_QUERY environment variable is not set")
if not BFF_KEY:
    raise ValueError("BFF_KEY environment variable is not set")
if not QUERY_KEY:
    raise ValueError("QUERY_KEY environment variable is not set")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "query_url": QUERY_URL,
        "backend_fro_frontend_url": BACKEND_FRO_FRONTEND_URL
    }

def determine_backend_url(path: str) -> Optional[str]:
    """
    Determine which backend URL to use based on the request path.
    
    Args:
        path: The request path
        
    Returns:
        Backend URL or None if no match
    """
    if "v1/" in path:
        print("Using QUERY_URL")
        return QUERY_URL
    elif "categories" in path or "data/" in path:
        print("Using BACKEND_FRO_FRONTEND_URL")
        return BACKEND_FRO_FRONTEND_URL
    return None



@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_request(path: str, request: Request):
    """
    Catch-all proxy route that forwards requests to appropriate backends.
    """
    # Determine which backend to forward to
    print(f"Requesting {path}")
    backend_url = determine_backend_url(path)
    print(f"Backend URL: {backend_url}")
    
    if not backend_url:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    # Construct the target URL
    target_url = f"{backend_url.rstrip('/')}/{path}"
    
    print(f"Target URL: {target_url}")
    
    # Get query parameters
    query_params = dict(request.query_params)
    
    # Get request body - read it for any request that might have one
    body = None
    try:
        body = await request.body()
        # If body is empty, set to None so httpx doesn't send empty content
        print(f"Body: {body}")
        if not body:
            body = None
    except Exception:
        pass
    
    # Prepare headers - only remove headers that would cause issues
    # Forward everything else as-is
    headers = {}
    for key, value in request.headers.items():
        # Skip headers that should not be forwarded
        if key.lower() not in ["host", "connection"]:
            headers[key] = value

    # Inject auth header per target backend
    if backend_url == QUERY_URL:
        headers[AUTHENTICATION_HEADER_NAME_QUERY] = f"Bearer {QUERY_KEY}"
    elif backend_url == BACKEND_FRO_FRONTEND_URL:
        headers[AUTHENTICATION_HEADER_NAME_BFF] = f"Bearer {BFF_KEY}"

    print(f"Headers: {headers}")
    # Forward the request to the backend
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                params=query_params if query_params else None,
                headers=headers,
                content=body,
                follow_redirects=True
            )
                        
            print(f"Response: {response.text}")
            # Forward response exactly as received from backend
            # Only remove connection header (required for HTTP/1.1)
            response_headers = {}
            for key, value in response.headers.items():
                if key.lower() != "connection":
                    response_headers[key] = value
            
            # Return the response exactly as it came from the backend
            return Response(
                response.text
            )
    
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Gateway timeout: Backend service did not respond in time"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=502,
            detail="Bad gateway: Unable to connect to backend service"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Backend error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal proxy error: {str(e)}"
        )



