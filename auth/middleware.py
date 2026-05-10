from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .service import JWTError, decode_access_token


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path in ["/health", "/login", "/login/github", "/auth/github/callback"]:
            return await call_next(request)

        auth_header = request.headers.get("authorization")
        if not auth_header:
            return JSONResponse({"error": "Missing Authorization header"}, status_code=401)

        if not auth_header.startswith("Bearer "):
            return JSONResponse({"error": "Invalid Authorization format"}, status_code=401)

        token = auth_header.split(" ", 1)[1]

        try:
            payload = decode_access_token(token)
            request.state.user = payload["sub"]
        except JWTError:
            return JSONResponse({"error": "Invalid or expired token"}, status_code=401)

        return await call_next(request)