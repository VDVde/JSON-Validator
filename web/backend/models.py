"""
Pydantic models for request/response validation.
"""
import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    language: str = "de"

    @field_validator('language')
    def validate_language(cls, v):
        if v not in ['en', 'de']:
            raise ValueError('Language must be "en" or "de"')
        return v


class UserCreate(UserBase):
    """User registration model."""
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserCreateByAdmin(UserBase):
    """Admin creating a user model."""
    password: str | None = Field(None, min_length=8, max_length=128)
    role: str = "user"
    is_verified: bool = False

    @field_validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'admin']:
            raise ValueError('Role must be "user" or "admin"')
        return v


class UserUpdate(BaseModel):
    """User update model."""
    language: str | None = None

    @field_validator('language')
    def validate_language(cls, v):
        if v is not None and v not in ['en', 'de']:
            raise ValueError('Language must be "en" or "de"')
        return v


class UserUpdateByAdmin(UserUpdate):
    """Admin updating a user model."""
    role: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None

    @field_validator('role')
    def validate_role(cls, v):
        if v is not None and v not in ['user', 'admin']:
            raise ValueError('Role must be "user" or "admin"')
        return v


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    role: str
    language: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: datetime | None = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response model."""
    users: list[UserResponse]
    total: int


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator('new_password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class PasswordChange(BaseModel):
    """Password change model (for logged-in users)."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator('new_password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class GoogleAuthRequest(BaseModel):
    """Google OAuth token model."""
    credential: str  # The ID token from Google


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    success: bool = True
