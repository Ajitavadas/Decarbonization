"""
Custom exceptions and global error handlers
"""

from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError


class AppException(Exception):
    """Base exception for application errors"""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ClimatiqAPIError(AppException):
    """Exception for Climatiq API errors"""
    def __init__(self, message: str, status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(message, status_code)


class DatabaseError(AppException):
    """Exception for database errors"""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotFoundError(AppException):
    """Exception for resource not found"""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ValidationException(AppException):
    """Exception for validation errors"""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class AuthenticationError(AppException):
    """Exception for authentication errors"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(AppException):
    """Exception for authorization errors"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Global handler for custom application exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "path": str(request.url)
        }
    )


async def validation_exception_handler(
    request: Request, 
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """Global handler for Pydantic validation errors"""
    # Convert errors to JSON-safe format (handle bytes objects)
    def make_json_safe(obj):
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        elif isinstance(obj, dict):
            return {k: make_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_json_safe(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(make_json_safe(item) for item in obj)
        return obj
    
    errors = make_json_safe(exc.errors())
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": errors,
            "path": str(request.url)
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global handler for unhandled exceptions"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "path": str(request.url)
        }
    )
