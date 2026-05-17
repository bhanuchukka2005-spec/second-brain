"""
Authentication endpoints.
POST /auth/register  — create a new account
POST /auth/login     — get a JWT token
GET  /auth/me        — get current user info
"""
import logging
from fastapi import APIRouter, HTTPException, status
from api.models.schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from api.models.auth import (
    create_user, get_user_by_username,
    verify_password, create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from api.dependencies import CurrentUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
async def register(body: RegisterRequest) -> UserResponse:
    """
    Create a new user account.
    Username must be 3-50 alphanumeric characters.
    Password must be at least 8 characters.
    """
    user = create_user(body.username, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' is already taken."
        )
    logger.info("New user registered: %s", body.username)
    return UserResponse(
        id=user["id"],
        username=user["username"],
        created_at=user["created_at"]
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get access token"
)
async def login(body: LoginRequest) -> TokenResponse:
    """
    Authenticate with username and password.
    Returns a JWT bearer token valid for 24 hours.
    Include this token in the Authorization header for all protected endpoints:
    `Authorization: Bearer <token>`
    """
    user = get_user_by_username(body.username)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user["id"], user["username"])
    logger.info("User logged in: %s", body.username)
    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info"
)
async def get_me(current_user: CurrentUser) -> UserResponse:
    """Returns the currently authenticated user's profile."""
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        created_at=current_user["created_at"]
    )
