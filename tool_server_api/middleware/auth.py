"""Middleware de autenticación"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from config.settings import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware de autenticación por API Key.
    Rutas públicas: /docs, /openapi.json, /redoc, /health, /playground
    """
    
    async def dispatch(self, request: Request, call_next):
        # Rutas públicas (sin autenticación)
        public_paths = [
            '/docs',
            '/openapi.json',
            '/redoc',
            '/info',
            '/health',
            '/favicon.ico'
        ]
        
        # Permitir rutas públicas y playground
        if (request.url.path in public_paths or 
            '/playground/' in request.url.path or 
            '/schema' in request.url.path):
            return await call_next(request)
        
        # Validar API Key
        api_key = request.headers.get("X-Tool-Api-Key")
        
        if api_key != settings.TOOL_API_KEY:
            raise HTTPException(
                status_code=401,
                detail="Acceso no autorizado. Proporciona un X-Tool-Api-Key válido."
            )
        
        return await call_next(request)