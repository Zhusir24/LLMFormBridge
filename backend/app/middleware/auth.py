from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.utils.security import verify_token
import logging

logger = logging.getLogger(__name__)


class JWTMiddleware(BaseHTTPMiddleware):
    """JWT认证中间件"""

    def __init__(self, app, skip_paths: list = None):
        super().__init__(app)
        self.skip_paths = skip_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/login",
            "/api/auth/register",
        ]

    async def dispatch(self, request: Request, call_next):
        # 跳过不需要认证的路径
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # 检查Authorization头
        authorization = request.headers.get("Authorization")
        if not authorization:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authorization header missing"}
            )

        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")

            # 验证token
            payload = verify_token(token)
            if payload is None:
                raise ValueError("Invalid token")

            # 将用户信息添加到请求状态
            request.state.user = payload
            return await call_next(request)

        except Exception as e:
            logger.warning(f"Authentication failed: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Could not validate credentials"}
            )