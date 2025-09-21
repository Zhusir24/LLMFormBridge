from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token
from app.utils.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.exceptions import AuthenticationError
from datetime import timedelta
from app.config import settings


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, user_data: UserCreate) -> User:
        """注册新用户"""
        # 检查用户名是否存在
        if self.db.query(User).filter(User.username == user_data.username).first():
            raise AuthenticationError("Username already registered")

        # 检查邮箱是否存在
        if self.db.query(User).filter(User.email == user_data.email).first():
            raise AuthenticationError("Email already registered")

        # 创建新用户
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password)
        )

        # 第一个用户设为超级用户
        if self.db.query(User).count() == 0:
            user.is_superuser = True

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def authenticate_user(self, login_data: UserLogin) -> User:
        """验证用户"""
        user = self.db.query(User).filter(User.username == login_data.username).first()

        if not user:
            raise AuthenticationError("Invalid username or password")

        if not verify_password(login_data.password, user.password_hash):
            raise AuthenticationError("Invalid username or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        return user

    def login_user(self, login_data: UserLogin) -> Token:
        """用户登录"""
        user = self.authenticate_user(login_data)

        # 创建访问令牌
        access_token = create_access_token(data={"sub": user.username})
        refresh_token = create_refresh_token(data={"sub": user.username})

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    def refresh_token(self, refresh_token: str) -> Token:
        """刷新令牌"""
        from app.utils.security import verify_token

        payload = verify_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token")

        username = payload.get("sub")
        user = self.db.query(User).filter(User.username == username).first()

        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        # 创建新的访问令牌
        access_token = create_access_token(data={"sub": user.username})
        new_refresh_token = create_refresh_token(data={"sub": user.username})

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    def get_user_by_username(self, username: str) -> User:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()