# Authentication Proxy Layer

This FastAPI service acts as an authentication proxy layer that stands between clients and two backend services deployed on Choreo. It handles OAuth protocol authentication using generated keys, allowing clients to make requests without directly managing authentication credentials.

## Overview

The proxy layer authenticates requests coming from clients to two different services:
- **Query Service**: Handles requests containing `/v1` in the path
- **Backend for Frontend (BFF) Service**: Handles requests containing `/categories` or `/data` in the path

Each service uses its own OAuth protocol with distinct authentication headers and keys, which are automatically injected by this proxy layer.

## How It Works

1. **Client Request**: A client makes a request to the proxy endpoint
2. **Routing**: The proxy determines which backend service to route to based on the request path
3. **Authentication Injection**: The proxy automatically adds the appropriate OAuth Bearer token header based on the target service
4. **Request Forwarding**: The authenticated request is forwarded to the target backend service
5. **Response**: The backend response is returned to the client unchanged

## Configuration

Create a `.env` file in the project root with the following variables:

```env
# Backend Service URLs
QUERY_URL=http://your-query-service-url
BACKEND_FRO_FRONTEND_URL=http://your-bff-service-url

# Authentication Header Names
AUTHENTICATION_HEADER_NAME_BFF=your-bff-auth-header-name
AUTHENTICATION_HEADER_NAME_QUERY=your-query-auth-header-name

# OAuth Keys (generated from Choreo)
BFF_KEY=your-bff-oauth-key
QUERY_KEY=your-query-oauth-key
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your `.env` file with the required configuration

3. Run the service:
```bash
uvicorn main:app --reload
```

## API Endpoints

### Health Check
- `GET /health` - Returns the health status and configured backend URLs

### Proxy Endpoints
- All other endpoints are proxied to the appropriate backend service based on path patterns:
  - Paths containing `/v1` → `QUERY_URL`
  - Paths containing `/categories` or `/data` → `BACKEND_FRO_FRONTEND_URL`
  - Other paths → 404 Not Found

## Features

- **Automatic Authentication**: OAuth Bearer tokens are automatically injected based on the target service
- **Transparent Proxying**: Requests and responses are forwarded as-is, with only necessary authentication headers added
- **CORS Enabled**: Cross-origin requests are supported
- **Error Handling**: Graceful error handling for timeouts, connection errors, and backend errors

## Architecture

```
Client → Authentication Proxy Layer → Backend Services (Choreo)
                ↓
        OAuth Key Injection
```

The proxy layer eliminates the need for clients to manage OAuth credentials directly, centralizing authentication logic and simplifying client-side implementation.

