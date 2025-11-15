"""
Authentication endpoints
"""
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash
from app.schemas.auth import Token, UserCreate, UserLogin
from app.schemas.user import User as UserSchema, UserWithRoles, Role as RoleSchema
from app.services.user_service import UserService, RoleService
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserSchema)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user
    """
    user_service = UserService(db)
    
    # Check if user already exists
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    existing_user = await user_service.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    user = await user_service.create_user(user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Login and get access token
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Login attempt for username: {form_data.username}")
        
        user_service = UserService(db)
        logger.info("UserService created successfully")
        
        user = await user_service.authenticate(form_data.username, form_data.password)
        logger.info(f"Authentication result: {user is not None}")
        
        if not user:
            logger.warning(f"Authentication failed for username: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted login: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        logger.info(f"Creating access token for user: {user.username}")
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        logger.info(f"Login successful for user: {user.username}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: UserSchema = Depends(get_current_user)
) -> Any:
    """
    Refresh access token
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.get("/me", response_model=UserWithRoles)
async def get_current_user_info(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get current user information
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"📋 /me endpoint called")
        logger.info(f"👤 Current user type: {type(current_user)}")
        logger.info(f"👤 Current user: {current_user}")
        role_service = RoleService(db)
        roles = await role_service.list_user_roles(current_user.id)
        return {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "phone": current_user.phone,
            "department": current_user.department,
            "position": current_user.position,
            "employee_id": current_user.employee_id,
            "role": current_user.role,
            "is_superuser": current_user.is_superuser,
            "is_verified": current_user.is_verified,
            "is_active": current_user.is_active,
            "bio": current_user.bio,
            "avatar_url": current_user.avatar_url,
            "last_login": current_user.last_login,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at,
            "roles": [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "is_builtin": r.is_builtin,
                    "created_at": r.created_at,
                    "updated_at": r.updated_at,
                }
                for r in roles
            ],
        }
    except Exception as e:
        logger.error(f"❌ Error in /me endpoint: {e}")
        raise