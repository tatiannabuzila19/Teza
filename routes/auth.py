from fastapi import APIRouter, HTTPException, status
from models.schemas import RegisterRequest, LoginRequest, TokenResponse
from services.auth_service import AuthService
from db.users import UserRepository

router = APIRouter()

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """Register a new user with hashed password."""
    UserRepository.init_db()

    if UserRepository.user_exists(req.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    user_id = UserRepository.create_user(req.username, req.password)
    token = AuthService.create_access_token(user_id, "user")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user_id,
        role="user",
    )

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Authenticate user and return JWT token."""
    UserRepository.init_db()
    
    # Debug logging
    print(f"[LOGIN] Attempting login for username: '{req.username}'")
    
    user = UserRepository.get_user_by_username(req.username)
    print(f"[LOGIN] User found: {user is not None}")
    
    if not user:
        print(f"[LOGIN] User not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    print(f"[LOGIN] Verifying password for user {user['username']}")
    print(f"[LOGIN] Incoming password length: {len(req.password)}")
    print(f"[LOGIN] Stored hash length: {len(user['password_hash'])}")
    
    is_valid = AuthService.verify_password(req.password, user["password_hash"])
    print(f"[LOGIN] Password verification result: {is_valid}")
    
    if not is_valid:
        print(f"[LOGIN] Password verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = AuthService.create_access_token(user["id"], user["role"])

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user["id"],
        role=user["role"],
    )
