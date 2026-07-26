"""
Authentication endpoints — username/password and Google OAuth.
"""
import logging
from fastapi import APIRouter, HTTPException, status
from api.models.schemas import (
    RegisterRequest, LoginRequest, GoogleLoginRequest,
    TokenResponse, UserResponse,
)
from src.db.user_store import (
    create_user, get_user_by_username,
    verify_password, create_access_token,
    get_or_create_google_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from src.db.google_auth import verify_google_token
from api.dependencies import CurrentUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
             summary="Register a new account")
async def register(body: RegisterRequest) -> UserResponse:
    user = create_user(body.username, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' is already taken."
        )
    logger.info("New user registered: %s", body.username)
    return UserResponse(id=user["id"], username=user["username"], created_at=user["created_at"])


@router.post("/login", response_model=TokenResponse, summary="Login with username and password")
async def login(body: LoginRequest) -> TokenResponse:
    user = get_user_by_username(body.username)
    if not user or not user.get("password_hash") or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user["id"], user["username"])
    logger.info("User logged in: %s", body.username)
    return TokenResponse(access_token=token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@router.post("/google", response_model=TokenResponse, summary="Login or register with Google")
async def google_login(body: GoogleLoginRequest) -> TokenResponse:
    """
    Verify a Google ID token (obtained client-side via Google Sign-In)
    and return our own JWT. Creates a new account automatically on first login.
    """
    google_user = verify_google_token(body.id_token)
    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Google token. Please try signing in again."
        )

    user = get_or_create_google_user(
        email=google_user["email"],
        name=google_user["name"],
        google_sub=google_user["google_sub"],
        picture=google_user.get("picture", ""),
    )

    token = create_access_token(user["id"], user["username"])
    logger.info("Google login: %s (%s)", user["username"], google_user["email"])
    return TokenResponse(access_token=token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@router.get("/me", response_model=UserResponse, summary="Get current user info")
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        created_at=current_user["created_at"]
    )