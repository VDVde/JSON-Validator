"""
User management API routes.
"""
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from google.auth.transport import requests as google_requests

# Google OAuth
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from .auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decode_token,
    generate_reset_token,
    generate_verification_token,
    hash_password,
    verify_password,
)
from .database import EmailVerificationToken, Language, PasswordResetToken, User, UserRole, get_db
from .email_service import send_password_reset_email, send_verification_email, send_welcome_email
from .models import (
    GoogleAuthRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    UserCreate,
    UserCreateByAdmin,
    UserListResponse,
    UserResponse,
    UserUpdate,
    UserUpdateByAdmin,
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])

# Google OAuth Client ID
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

# Skip email verification if SMTP is not configured (for development/testing)
SKIP_EMAIL_VERIFICATION = os.environ.get("SKIP_EMAIL_VERIFICATION", "false").lower() == "true"
# Check if SMTP is configured
SMTP_HOST = os.environ.get("SMTP_HOST", "")
AUTO_VERIFY_IF_NO_SMTP = not SMTP_HOST  # Auto-verify if no SMTP configured


def get_current_user_from_token(request: Request, db: Session = Depends(get_db)) -> User:
    """Extract and validate user from JWT token in Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = auth_header.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return user


def require_admin(user: User = Depends(get_current_user_from_token)) -> User:
    """Require admin role."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


# ============================================================================
# Public Authentication Routes
# ============================================================================

@router.post("/register", response_model=MessageResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Determine admin role based on ADMIN_EMAILS environment variable
    admin_emails_env = os.environ.get("ADMIN_EMAILS", "")
    admin_emails = [email.strip().lower() for email in admin_emails_env.split(",") if email.strip()]
    is_admin = user_data.email.lower() in admin_emails

    # Auto-verify if SMTP is not configured or explicitly skipped
    should_auto_verify = SKIP_EMAIL_VERIFICATION or AUTO_VERIFY_IF_NO_SMTP

    # Create user
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=UserRole.ADMIN if is_admin else UserRole.USER,
        language=Language(user_data.language),
        is_verified=should_auto_verify  # Auto-verify if no SMTP
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Only send verification email if SMTP is configured
    if not should_auto_verify:
        # Create verification token
        token = generate_verification_token()
        verification = EmailVerificationToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(verification)
        db.commit()

        # Send verification email
        send_verification_email(user.email, token, user_data.language)

        return MessageResponse(
            message="Registration successful. Please check your email to verify your account.",
            success=True
        )

    # If SMTP not configured, user is auto-verified
    role_msg = " You have been assigned the Admin role." if is_admin else ""
    return MessageResponse(
        message=f"Registration successful. Your account is now active.{role_msg}",
        success=True
    )


@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login with email and password."""
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email first"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token = create_access_token(user.id, user.email, user.role.value)

    return LoginResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            email=user.email,
            role=user.role.value,
            language=user.language.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login
        )
    )


@router.post("/google", response_model=LoginResponse)
def google_auth(auth_data: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Login or register with Google OAuth."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured"
        )

    try:
        # Verify the Google token
        idinfo = id_token.verify_oauth2_token(
            auth_data.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

        google_id = idinfo['sub']
        email = idinfo['email']
        email_verified = idinfo.get('email_verified', False)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        ) from e

    # Check if user exists by Google ID or email
    user = db.query(User).filter(
        (User.google_id == google_id) | (User.email == email)
    ).first()

    if user:
        # Update Google ID if not set
        if not user.google_id:
            user.google_id = google_id

        # Verify email if Google says it's verified
        if email_verified and not user.is_verified:
            user.is_verified = True

        user.last_login = datetime.utcnow()
        db.commit()
    else:
        # Create new user
        user = User(
            email=email,
            google_id=google_id,
            role=UserRole.USER,
            language=Language.DE,
            is_verified=email_verified,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Send welcome email
        send_welcome_email(email, "de")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    # Create access token
    access_token = create_access_token(user.id, user.email, user.role.value)

    return LoginResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            email=user.email,
            role=user.role.value,
            language=user.language.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login
        )
    )


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email with token."""
    verification = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token == token,
        EmailVerificationToken.used == False,
        EmailVerificationToken.expires_at > datetime.utcnow()
    ).first()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    user = db.query(User).filter(User.id == verification.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Mark as verified
    user.is_verified = True
    verification.used = True
    db.commit()

    # Send welcome email
    send_welcome_email(user.email, user.language.value)

    return MessageResponse(message="Email verified successfully")


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(request_data: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset."""
    user = db.query(User).filter(User.email == request_data.email).first()

    # Always return success to prevent email enumeration
    if not user:
        return MessageResponse(message="If an account exists with this email, a reset link will be sent.")

    # Create reset token
    token = generate_reset_token()
    reset = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db.add(reset)
    db.commit()

    # Send reset email
    send_password_reset_email(user.email, token, user.language.value)

    return MessageResponse(message="If an account exists with this email, a reset link will be sent.")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(reset_data: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Reset password with token."""
    reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == reset_data.token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()

    if not reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    user = db.query(User).filter(User.id == reset.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update password
    user.password_hash = hash_password(reset_data.new_password)
    reset.used = True
    db.commit()

    return MessageResponse(message="Password reset successfully")


# ============================================================================
# Authenticated User Routes
# ============================================================================

@router.get("/me", response_model=UserResponse)
def get_current_user(user: User = Depends(get_current_user_from_token)):
    """Get current user profile."""
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role.value,
        language=user.language.value,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.patch("/me", response_model=UserResponse)
def update_current_user(
    update_data: UserUpdate,
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    if update_data.language:
        user.language = Language(update_data.language)

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role.value,
        language=user.language.value,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    password_data: PasswordChange,
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Change password for logged-in user."""
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change password for OAuth-only account"
        )

    if not verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    user.password_hash = hash_password(password_data.new_password)
    db.commit()

    return MessageResponse(message="Password changed successfully")


# ============================================================================
# Admin Routes
# ============================================================================

@admin_router.get("/users", response_model=UserListResponse)
def list_users(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    total = db.query(User).count()
    users = db.query(User).offset(skip).limit(limit).all()

    return UserListResponse(
        users=[
            UserResponse(
                id=u.id,
                email=u.email,
                role=u.role.value,
                language=u.language.value,
                is_active=u.is_active,
                is_verified=u.is_verified,
                created_at=u.created_at,
                last_login=u.last_login
            )
            for u in users
        ],
        total=total
    )


@admin_router.post("/users", response_model=UserResponse)
def create_user(
    user_data: UserCreateByAdmin,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password) if user_data.password else None,
        role=UserRole(user_data.role),
        language=Language(user_data.language),
        is_verified=user_data.is_verified
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # If no password set, send verification email so user can set password
    if not user_data.password:
        token = generate_verification_token()
        verification = EmailVerificationToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(verification)
        db.commit()
        send_verification_email(user.email, token, user_data.language)

    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role.value,
        language=user.language.value,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login=user.last_login
    )


@admin_router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role.value,
        language=user.language.value,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login=user.last_login
    )


@admin_router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    update_data: UserUpdateByAdmin,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent admin from demoting themselves
    if user.id == admin.id and update_data.role == "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself"
        )

    if update_data.language:
        user.language = Language(update_data.language)
    if update_data.role:
        user.role = UserRole(update_data.role)
    if update_data.is_active is not None:
        user.is_active = update_data.is_active
    if update_data.is_verified is not None:
        user.is_verified = update_data.is_verified

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role.value,
        language=user.language.value,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login=user.last_login
    )


@admin_router.delete("/users/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent admin from deleting themselves
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    db.delete(user)
    db.commit()

    return MessageResponse(message="User deleted successfully")
