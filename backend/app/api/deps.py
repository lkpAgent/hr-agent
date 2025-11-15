"""
API dependencies for authentication and authorization
"""
from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, Role, UserRoleAssociation
from app.schemas.user import User as UserSchema
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get current authenticated user
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("🔍 get_current_user called")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        logger.info(f"🔑 Decoding token: {token[:20]}...")
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        logger.info(f"👤 Extracted user_id: {user_id}")
        if user_id is None:
            logger.error("❌ No user_id in token payload")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"❌ JWT decode error: {e}")
        raise credentials_exception
    
    try:
        from uuid import UUID
        user_service = UserService(db)
        logger.info(f"🔍 Looking up user with id: {user_id}")
        user_uuid = UUID(user_id)
        user = await user_service.get_user(user_uuid)
        
        if user is None:
            logger.error(f"❌ User not found with id: {user_id}")
            raise credentials_exception
        
        logger.info(f"✅ User found: {user.username}, active: {user.is_active}")
        
        if not user.is_active:
            logger.error(f"❌ User {user.username} is inactive")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        logger.info(f"✅ Returning user: {user.username}")
        return user
    except Exception as e:
        logger.error(f"❌ Error in get_current_user: {e}")
        raise


async def get_current_hr_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current HR user (HR Manager or HR Specialist)
    """
    from app.models.user import UserRole
    
    if current_user.role not in [UserRole.HR_MANAGER, UserRole.HR_SPECIALIST] and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR permissions required"
        )
    return current_user


async def get_current_admin_by_role(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    query = (
        select(Role)
        .join(UserRoleAssociation, Role.id == UserRoleAssociation.role_id)
        .where(UserRoleAssociation.user_id == current_user.id, Role.is_active == True)
    )
    result = await db.execute(query)
    roles = {r.name for r in result.scalars().all()}
    if "超级管理员" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员角色"
        )
    return current_user


def require_any_role_names(required: List[str]):
    async def dependency(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> User:
        query = (
            select(Role)
            .join(UserRoleAssociation, Role.id == UserRoleAssociation.role_id)
            .where(UserRoleAssociation.user_id == current_user.id, Role.is_active == True)
        )
        result = await db.execute(query)
        roles = {r.name for r in result.scalars().all()}
        if not any(name in roles for name in required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="角色权限不足"
            )
        return current_user
    return dependency