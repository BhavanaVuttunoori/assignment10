# app/models/user.py
from datetime import datetime, timedelta
import uuid
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
import base64
import json
import hmac
import hashlib
import time
from typing import Union

# Lightweight token creation/verification using HMAC-SHA256 to avoid external
# JWT dependencies in this environment. Tokens are of the form <payload>.<sig>
# where payload is URL-safe base64 of the JSON payload and sig is HMAC-SHA256.

class JWTError(Exception):
    pass
try:
    from pydantic import ValidationError
except Exception:
    try:
        from pydantic_core import ValidationError
    except Exception:
        # Fallback simple ValidationError for environments with incompatible pydantic
        class ValidationError(Exception):
            pass

from app.schemas.base import UserCreate
from app.schemas.user import UserResponse, Token
from app.config import settings

Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Use values from app.config.Settings (overridable via .env)
# SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES are read from `settings`

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(name={self.first_name} {self.last_name}, email={self.email})>"

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str) -> bool:
        """Verify a plain password against the hashed password."""
        # Compare against stored password_hash
        return pwd_context.verify(plain_password, self.password_hash)

    # Provide a write-only password property so code/tests can set `user.password = 'raw'`
    @property
    def password(self) -> None:  # pragma: no cover - write-only property
        raise AttributeError("password is write-only")

    @password.setter
    def password(self, raw_password: str) -> None:
        # If a pre-hashed password is provided (for tests or fixtures), detect it
        # and store it directly instead of hashing again. passlib's CryptContext
        # can identify whether a string is already a valid hash for the
        # configured schemes.
        try:
            identified = pwd_context.identify(raw_password)
        except Exception:
            identified = None

        if identified:
            # raw_password looks like an existing hash (bcrypt, etc.)
            self.password_hash = raw_password
        else:
            self.password_hash = self.hash_password(raw_password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = int(time.time() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).total_seconds())
        to_encode.update({"exp": expire})
        payload = json.dumps(to_encode, default=str).encode()
        b64 = base64.urlsafe_b64encode(payload).decode().rstrip("=")
        sig = hmac.new(settings.SECRET_KEY.encode(), b64.encode(), hashlib.sha256).hexdigest()
        return f"{b64}.{sig}"

    @staticmethod
    def verify_token(token: str) -> Optional[UUID]:
        """Verify and decode a JWT token."""
        try:
            # Split token into payload and signature
            payload_b64, sig = token.rsplit('.', 1)
            expected_sig = hmac.new(settings.SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected_sig):
                return None
            # Add padding and decode
            padding = '=' * (-len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode()
            payload = json.loads(payload_json)
            # Check expiry
            if payload.get('exp') and int(payload['exp']) < int(time.time()):
                return None
            user_id = payload.get('sub')
            return uuid.UUID(user_id) if user_id else None
        except (JWTError, ValueError):
            return None

    @classmethod
    def register(cls, db, user_data: Dict[str, Any]) -> "User":
        """Register a new user with validation."""
        try:
            # Validate password length first
            password = user_data.get('password', '')
            if len(password) < 6:  # Strictly less than 6 characters
                raise ValueError("Password must be at least 6 characters long")
            
            # Check if email/username exists
            existing_user = db.query(cls).filter(
                (cls.email == user_data.get('email')) |
                (cls.username == user_data.get('username'))
            ).first()
            
            if existing_user:
                raise ValueError("Username or email already exists")

            # Validate using Pydantic schema
            user_create = UserCreate.model_validate(user_data)
            
            # Create new user instance
            new_user = cls(
                first_name=user_create.first_name,
                last_name=user_create.last_name,
                email=user_create.email,
                username=user_create.username,
                is_active=True,
                is_verified=False
            )
            # use the write-only password setter to hash and set password_hash
            new_user.password = user_create.password
            
            db.add(new_user)
            db.flush()
            return new_user
            
        except ValidationError as e:
            raise ValueError(str(e)) # pragma: no cover
        except ValueError as e:
            raise e

    @classmethod
    def authenticate(cls, db, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return token with user data."""
        user = db.query(cls).filter(
            (cls.username == username) | (cls.email == username)
        ).first()

        if not user or not user.verify_password(password):
            return None # pragma: no cover

        user.last_login = datetime.utcnow()
        db.commit()

        # Create token response using Pydantic models
        user_response = UserResponse.model_validate(user)
        token_response = Token(
            access_token=cls.create_access_token({"sub": str(user.id)}),
            token_type="bearer",
            user=user_response
        )

        return token_response.model_dump()