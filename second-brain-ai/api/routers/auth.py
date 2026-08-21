"""
Authentication endpoints — username/password, Google OAuth, and password reset.
Rate limited by IP on public endpoints to prevent brute force and spam.
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from api.models.schemas import (
    RegisterRequest, LoginRequest, GoogleLoginRequest,
    ForgotPasswordRequest, ResetPasswordRequest, MessageResponse,
    TokenResponse, UserResponse,
)
from src.db.user_store import (
    create_user, get_user_by_username, get_user_by_email,
    verify_password, create_access_token,
    get_or_create_google_user,
    create_reset_token, reset_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from src.db.google_auth import verify_google_token
from src.db.email_utils import send_password_reset_email
from src.utils.rate_limiter import rate_limit_by_ip
from api.dependencies import CurrentUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
    dependencies=[Depends(rate_limit_by_ip(max_requests=5, window_seconds=3600))],
)
async def register(body: RegisterRequest) -> UserResponse:
    user = create_user(body.username, body.password, body.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' or email is already taken."
        )
    logger.info("New user registered: %s", body.username)
    return UserResponse(id=user["id"], username=user["username"], created_at=user["created_at"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with username and password",
    dependencies=[Depends(rate_limit_by_ip(max_requests=10, window_seconds=300))],
)
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


@router.post(
    "/google",
    response_model=TokenResponse,
    summary="Login or register with Google",
    dependencies=[Depends(rate_limit_by_ip(max_requests=15, window_seconds=300))],
)
async def google_login(body: GoogleLoginRequest) -> TokenResponse:
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


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request a password reset email",
    dependencies=[Depends(rate_limit_by_ip(max_requests=3, window_seconds=3600))],
)
async def forgot_password(body: ForgotPasswordRequest) -> MessageResponse:
    """
    Sends a password reset link if an account with this username/email exists.
    Always returns the same generic message regardless of whether the account
    exists — this prevents attackers from using this endpoint to discover
    which usernames or emails are registered. Rate limited to 3/hour per IP
    to prevent using this endpoint to spam someone's inbox.
    """
    identifier = body.identifier.strip()
    user = get_user_by_email(identifier) if "@" in identifier else get_user_by_username(identifier)

    generic_message = (
        "If an account with that username or email exists, "
        "a password reset link has been sent."
    )

    if not user:
        logger.info("Password reset requested for unknown identifier: %s", identifier)
        return MessageResponse(message=generic_message)

    if not user.get("password_hash"):
        logger.info("Password reset requested for Google-only account: %s", user["username"])
        return MessageResponse(message=generic_message)

    if not user.get("email"):
        logger.warning("User %s has no email on file — cannot send reset link", user["username"])
        return MessageResponse(message=generic_message)

    token = create_reset_token(user["id"])
    send_password_reset_email(user["email"], user["username"], token)

    return MessageResponse(message=generic_message)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password using a valid token",
    dependencies=[Depends(rate_limit_by_ip(max_requests=10, window_seconds=3600))],
)
async def do_reset_password(body: ResetPasswordRequest) -> MessageResponse:
    """Validates the reset token and sets a new password if valid."""
    success = reset_password(body.token, body.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or has expired. Please request a new one."
        )
    logger.info("Password successfully reset via token")
    return MessageResponse(message="Your password has been reset. You can now log in.")


@router.get("/me", response_model=UserResponse, summary="Get current user info")
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        created_at=current_user["created_at"]
    )