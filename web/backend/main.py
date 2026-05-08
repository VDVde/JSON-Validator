import json
import logging
import os
import secrets
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
)
from fastapi.staticfiles import StaticFiles

# Add src to path to import validator
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = BASE_DIR / "src"
SCHEMA_DIR = BASE_DIR / "schemas"
sys.path.append(str(SRC_DIR))

from vdv463_validator import VDV463Validator  # noqa: E402

from .auth import decode_token  # noqa: E402
from .user_routes import admin_router  # noqa: E402

# Import user management routes
from .user_routes import router as auth_router  # noqa: E402

app = FastAPI(
    title="VDV463 Validator API",
    description="API for validating VDV463 JSON messages with user management",
    version="3.0.2"
)

# Include authentication and admin routers
app.include_router(auth_router)
app.include_router(admin_router)

# Security: Configure allowed CORS origins from environment
# Default is restrictive for production; override with comma-separated list
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000"
).split(",")

# Enable CORS with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Security: Maximum file upload size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# --- Security ---
security = HTTPBasic(auto_error=False)  # Don't auto-error, we handle auth ourselves
bearer_security = HTTPBearer(auto_error=False)  # JWT Bearer auth
# SECURITY: AUTH_SECRET must be set via environment variable
# No default password for security - app will require auth to be configured
AUTH_SECRET = os.environ.get("AUTH_SECRET", "")

# Optional: disable all authentication (e.g. for trusted internal networks)
# Set DISABLE_AUTH=true in the environment to bypass login entirely.
DISABLE_AUTH = os.environ.get("DISABLE_AUTH", "false").lower() in ("true", "1", "yes")
if DISABLE_AUTH:
    logger_tmp = logging.getLogger("security")
    logger_tmp.warning("⚠️  DISABLE_AUTH=true — all authentication checks are bypassed!")

# Rate limiting for brute-force protection
# Stores: {ip: [(timestamp, success), ...]}
login_attempts = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_ATTEMPTS = 5  # max failed attempts per window

# Security logging
logger = logging.getLogger("security")
logging.basicConfig(level=logging.INFO)

def check_rate_limit(request: Request) -> None:
    """Check if IP has exceeded rate limit for failed login attempts."""
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()

    # Clean old attempts
    login_attempts[client_ip] = [
        (ts, success) for ts, success in login_attempts[client_ip]
        if current_time - ts < RATE_LIMIT_WINDOW
    ]

    # Count failed attempts in window
    failed_count = sum(1 for ts, success in login_attempts[client_ip] if not success)

    if failed_count >= RATE_LIMIT_MAX_ATTEMPTS:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Try again in {RATE_LIMIT_WINDOW} seconds.",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)}
        )

def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    request: Request
):
    """
    Validates Basic Auth credentials.
    In production, AUTH_SECRET should be set via env var (format "user:pass").
    """
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limit before validating credentials
    check_rate_limit(request)

    if not AUTH_SECRET or ":" not in AUTH_SECRET:
        logger.error("AUTH_SECRET not configured properly")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication not configured. Set AUTH_SECRET environment variable."
        )

    correct_user, correct_pass = AUTH_SECRET.split(":", 1)

    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = correct_user.encode("utf8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )

    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = correct_pass.encode("utf8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )

    if not (is_correct_username and is_correct_password):
        # Log failed attempt
        login_attempts[client_ip].append((time.time(), False))
        logger.warning(f"Failed login attempt from IP: {client_ip}, user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "X-Basic"},
        )

    # Log successful attempt
    login_attempts[client_ip].append((time.time(), True))
    return credentials.username


def get_current_user_flexible(
    request: Request,
    basic_credentials: Annotated[HTTPBasicCredentials | None, Depends(security)] = None,
    bearer_token: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_security)] = None
):
    """
    Flexible authentication that accepts either JWT Bearer token or Basic Auth.
    When DISABLE_AUTH=true, all requests are accepted without credentials.
    """
    # ── Auth bypass ──────────────────────────────────────────────────────────
    if DISABLE_AUTH:
        return "anonymous"

    client_ip = request.client.host if request.client else "unknown"

    # First, try JWT Bearer token
    if bearer_token and bearer_token.credentials:
        payload = decode_token(bearer_token.credentials)
        if payload:
            return payload.get("email", "jwt_user")

    # Fall back to Basic Auth
    if basic_credentials:
        # Check rate limit
        check_rate_limit(request)

        if not AUTH_SECRET or ":" not in AUTH_SECRET:
            # If no Basic Auth configured, deny access
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        correct_user, correct_pass = AUTH_SECRET.split(":", 1)

        is_correct_username = secrets.compare_digest(
            basic_credentials.username.encode("utf8"),
            correct_user.encode("utf8")
        )
        is_correct_password = secrets.compare_digest(
            basic_credentials.password.encode("utf8"),
            correct_pass.encode("utf8")
        )

        if is_correct_username and is_correct_password:
            login_attempts[client_ip].append((time.time(), True))
            return basic_credentials.username
        else:
            login_attempts[client_ip].append((time.time(), False))
            logger.warning(f"Failed login attempt from IP: {client_ip}")

    # No valid authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        # Don't send WWW-Authenticate header to avoid browser popup
    )

# --- Dependencies ---
def get_validator():
    # Instantiate validator with correct schema directory
    try:
        return VDV463Validator(schema_dir=SCHEMA_DIR)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# --- Endpoints ---

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/server-config")
def server_config():
    """Expose non-sensitive server configuration to the frontend."""
    return {
        "auth_disabled": DISABLE_AUTH,
    }

@app.get("/api/schemas", dependencies=[Depends(get_current_user_flexible)])
def list_schemas(validator: VDV463Validator = Depends(get_validator)):
    """List available schema versions."""
    versions = validator.schema_manager.get_available_versions()
    return {"schemas": versions}

@app.get("/api/schemas/{version}/{message_type}", dependencies=[Depends(get_current_user_flexible)])
def get_schema_detail(version: str, message_type: str):
    """Get the content of a specific schema file."""
    # Security: Comprehensive path traversal protection
    # Check for common path traversal patterns
    if ".." in version or ".." in message_type:
        raise HTTPException(status_code=400, detail="Invalid path parameters")

    # Validate characters (alphanumeric, dots, hyphens, underscores only)
    import re
    if not re.match(r'^[a-zA-Z0-9._-]+$', version) or not re.match(r'^[a-zA-Z0-9._-]+$', message_type):
        raise HTTPException(status_code=400, detail="Invalid path parameters")

    schema_path = (SCHEMA_DIR / version / f"{message_type}.json").resolve()

    # Verify the resolved path is still within SCHEMA_DIR
    if not str(schema_path).startswith(str(SCHEMA_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path parameters")

    if not schema_path.exists():
        raise HTTPException(status_code=404, detail="Schema not found")

    try:
        with open(schema_path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in schema: {e}") from e
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Error reading schema: {e}") from e

@app.post("/api/config", dependencies=[Depends(get_current_user_flexible)])
def upload_config(
    file: UploadFile = File(...)
):
    """Upload a custom validation configuration (rules)."""
    if not file.filename.endswith('.json') and not file.filename.endswith('.yaml') and not file.filename.endswith('.yml'):
        raise HTTPException(status_code=400, detail="Only .json or .yaml files are supported")

    try:
        content = file.file.read()
        content_str = content.decode('utf-8')

        # Verify it's valid YAML/JSON
        import yaml
        config = yaml.safe_load(content_str)

        # Return the verified config content so frontend can store it
        return {"status": "valid", "config": config}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid config file: {str(e)}") from e

@app.post("/api/validate", dependencies=[Depends(get_current_user_flexible)])
def validate_file(
    file: UploadFile = File(...),
    schema_version: str = Form("auto"),
    schema_only: bool = Form(False),
    config_content: str = Form(None),
    validator: VDV463Validator = Depends(get_validator)
):
    """
    Validate an uploaded JSON file.
    """
    if not file.filename or not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only .json files are supported")

    try:
        content = file.file.read()

        # Security: Check file size limit
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB"
            )

        content_str = content.decode('utf-8')

        # Configure validator version if requested
        if schema_version != "auto":
            validator.schema_version = schema_version

        # Write config to temp file if provided
        # In this stateless design, we use a temp file for the config per request
        if config_content:
            tmp_path = None
            try:
                # Create temp file for config
                fd, tmp_path = tempfile.mkstemp(suffix='.yaml', prefix='vdv_config_')
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
                        tmp.write(config_content)
                except Exception:
                    os.close(fd)
                    raise

                # Reload validator with new config
                validator = VDV463Validator(
                    SCHEMA_DIR,
                    config_path=Path(tmp_path),
                    schema_version=schema_version
                )

                # Run validation
                result = validator.validate_content(content_str, filename=file.filename, schema_only=schema_only)
                return result.to_dict()
            finally:
                # Clean up temp file - guaranteed cleanup
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass  # Best effort cleanup
        else:
            # Run validation with default/existing config
            result = validator.validate_content(content_str, filename=file.filename, schema_only=schema_only)
            return result.to_dict()

    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail="File must be valid UTF-8") from e
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}") from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}") from e
    except Exception as e:
        logger.exception("Unexpected validation error for file '%s': %s", file.filename, e)
        raise HTTPException(status_code=500, detail="Validation failed due to an internal error") from e

# --- Static Files ---
# Mount static files (Frontend)
# In Docker, we will copy dist to /app/web/frontend/dist
FRONTEND_DIST = BASE_DIR / "web" / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
