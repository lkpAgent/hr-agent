"""
User management endpoints
"""
from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import User as UserSchema, UserUpdate, UserCreate, UserStatusUpdate, UserPasswordReset
from app.schemas.role import Role as RoleSchema
from app.services.user_service import UserService
from app.api.deps import get_current_user, get_current_superuser

router = APIRouter()


@router.get("/", response_model=List[UserSchema])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserSchema = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all users (admin only)
    """
    user_service = UserService(db)
    users = await user_service.get_users(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get user by ID
    """
    user_service = UserService(db)
    user = await user_service.get_user(UUID(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Users can only see their own profile unless they're admin
    if user.id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update user
    """
    user_service = UserService(db)
    user = await user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Users can only update their own profile unless they're admin
    if user.id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    updated_user = await user_service.update_user(user.id, user_update,current_user)
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserSchema = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete user (admin only)
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await user_service.delete(user)
    return {"message": "User deleted successfully"}


@router.patch("/{user_id}/status")
async def update_status(
    user_id: str,
    data: UserStatusUpdate,
    current_user: UserSchema = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Map status to is_active
    is_active = True if data.status == "active" else False
    await user_service.update_user(user.id, UserUpdate(is_active=is_active), current_user)
    return {"message": "Status updated"}


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    data: UserPasswordReset,
    current_user: UserSchema = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await user_service.update_user(user.id, UserUpdate(password=data.password), current_user)
    return {"message": "Password reset"}


@router.get("/{user_id}/roles", response_model=List[RoleSchema])
async def get_user_roles(
    user_id: str,
    current_user: UserSchema = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    user_service = UserService(db)
    roles = await user_service.get_user_roles(UUID(user_id))
    return roles
@router.post("/", response_model=UserSchema)
async def create_user(
    user_data: UserCreate,
    current_user: UserSchema = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    user_service = UserService(db)
    user = await user_service.create_user(user_data)
    return user
