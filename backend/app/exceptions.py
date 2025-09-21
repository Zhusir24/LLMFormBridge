from fastapi import HTTPException, status


class LLMBridgeException(Exception):
    """Base exception for LLM Bridge"""
    pass


class AuthenticationError(LLMBridgeException):
    """Authentication related errors"""
    pass


class CredentialValidationError(LLMBridgeException):
    """Credential validation errors"""
    pass


class LLMProviderError(LLMBridgeException):
    """LLM provider related errors"""
    pass


class RateLimitError(LLMBridgeException):
    """Rate limit exceeded"""
    pass


# HTTP Exceptions
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

forbidden_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not enough permissions",
)

not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found",
)

validation_exception = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Validation error",
)

rate_limit_exception = HTTPException(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    detail="Rate limit exceeded",
)