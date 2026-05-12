"""
Authentication API routes – Register, Login, and Get Current User.
Uses JWT (PyJWT) for tokens and bcrypt for password hashing.
"""
import os
import jwt
import json
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
import re
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "CHANGE_ME_TO_A_RANDOM_SECRET":
    import warnings
    warnings.warn("⚠️ JWT_SECRET_KEY is not set! Using insecure default. Set it in .env for production.")
    SECRET_KEY = "ai-coach-dev-fallback-key-DO-NOT-USE-IN-PROD"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing helpers using bcrypt directly
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# OAuth2 scheme for extracting Bearer tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

router = APIRouter()

# ──────────────────────────────────────────────
# JSON-file based user store (multi-user, persistent)
# ──────────────────────────────────────────────
USERS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "users.json"
)


def _load_users() -> list:
    """Load users from the JSON file."""
    if not os.path.exists(USERS_FILE):
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, "w") as f:
            json.dump([], f)
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_users(users: list):
    """Persist users to the JSON file."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def _find_user_by_email(email: str) -> Optional[dict]:
    """Look up a user by email (case-insensitive)."""
    users = _load_users()
    for u in users:
        if u["email"].lower() == email.lower():
            return u
    return None


def _next_user_id() -> int:
    users = _load_users()
    if not users:
        return 1
    return max(u["id"] for u in users) + 1


# ──────────────────────────────────────────────
# Pydantic Schemas
# ──────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserProfile(BaseModel):
    id: int
    name: str
    email: str


# ──────────────────────────────────────────────
# JWT Helpers
# ──────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Dependency - extracts and validates the current user from the JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        email = payload.get("email")
        if user_id is None or email is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = _find_user_by_email(email)
    if user is None:
        raise credentials_exception
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """Create a new user account."""
    # 1. Validate email format FIRST
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, req.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a strictly valid email address (e.g., name@example.com).",
        )

    # 2. Validate password strength
    password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%!&*])[A-Za-z\d@#$%!&*]{8,}$"
    if not re.match(password_regex, req.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long and include an uppercase, lowercase, number, and special character (@#$%!&*).",
        )

    # 3. Check for duplicates AFTER input is valid
    if _find_user_by_email(req.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    new_user = {
        "id": _next_user_id(),
        "name": req.name,
        "email": req.email.lower(),
        "password_hash": hash_password(req.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    users = _load_users()
    users.append(new_user)
    _save_users(users)

    # Also initialise an empty stats file for this user
    _init_user_stats(new_user["id"])

    token = create_access_token({"user_id": new_user["id"], "email": new_user["email"]})
    return TokenResponse(
        access_token=token,
        user={"id": new_user["id"], "name": new_user["name"], "email": new_user["email"]},
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Authenticate an existing user."""
    user = _find_user_by_email(req.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this email.",
        )

    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
        )

    token = create_access_token({"user_id": user["id"], "email": user["email"]})
    return TokenResponse(
        access_token=token,
        user={"id": user["id"], "name": user["name"], "email": user["email"]},
    )


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user


# ──────────────────────────────────────────────
# Helpers - Per-user stats initialisation
# ──────────────────────────────────────────────
STATS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data"
)


def _init_user_stats(user_id: int):
    """Create an empty stats JSON file for a new user."""
    path = os.path.join(STATS_DIR, f"user_{user_id}_stats.json")
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f)
