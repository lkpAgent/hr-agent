"""
User management endpoints
"""
from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import User as UserSchema, UserUpdate, UserCreate, Role as RoleSchema, RoleCreate, AssignRolesRequest
from app.services.user_service import UserService, RoleService
from app.api.deps import get_current_user, get_current_admin_by_role

router = APIRouter()


@router.get("/", response_model=List[UserSchema])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserSchema = Depends(get_current_admin_by_role),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all users (admin only)
    """
    user_service = UserService(db)
    users = await user_service.get_all_users(skip=skip, limit=limit)
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
    user = await user_service.get_user_any(UUID(user_id))
    
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
    user = await user_service.get_user_any(UUID(user_id))
    
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
    
    updated_user = await user_service.update_user(user.id, user_update, current_user)
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserSchema = Depends(get_current_admin_by_role),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete user (admin only)
    """
    user_service = UserService(db)
    user = await user_service.get_user(UUID(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await user_service.delete_user(user.id, current_user)
    return {"message": "User deleted successfully"}


# Admin-only user management

@router.post("/admin/users", response_model=UserSchema)
async def admin_create_user(
    user_create: UserCreate,
    current_user: UserSchema = Depends(get_current_admin_by_role),
    db: AsyncSession = Depends(get_db)
) -> Any:
    user_service = UserService(db)
    user = await user_service.create_user(user_create)
    return user


@router.get("/admin/users/{user_id}/roles", response_model=List[RoleSchema])
async def admin_list_user_roles(
    user_id: str,
    current_user: UserSchema = Depends(get_current_admin_by_role),
    db: AsyncSession = Depends(get_db)
) -> Any:
    role_service = RoleService(db)
    roles = await role_service.list_user_roles(UUID(user_id))
    return roles


@router.put("/admin/users/{user_id}/roles", response_model=List[RoleSchema])
async def admin_assign_user_roles(
    user_id: str,
    payload: AssignRolesRequest,
    current_user: UserSchema = Depends(get_current_admin_by_role),
    db: AsyncSession = Depends(get_db)
) -> Any:
    role_service = RoleService(db)
    roles = await role_service.assign_roles_to_user(UUID(user_id), payload.role_ids)
    return roles


# Admin-only role management

@router.get("/admin/roles", response_model=List[RoleSchema])
async def admin_list_roles(
    current_user: UserSchema = Depends(get_current_admin_by_role),
    db: AsyncSession = Depends(get_db)
) -> Any:
    role_service = RoleService(db)
    return await role_service.list_roles()


@router.post("/admin/roles", response_model=RoleSchema)
async def admin_create_role(
    role_create: RoleCreate,
    current_user: UserSchema = Depends(get_current_admin_by_role),
    db: AsyncSession = Depends(get_db)
) -> Any:
    role_service = RoleService(db)
    return await role_service.create_role(role_create.name, role_create.description, role_create.is_builtin or False)


@router.delete("/admin/roles/{role_id}")
async def admin_delete_role(
    role_id: str,
    current_user: UserSchema = Depends(get_current_admin_by_role),
    db: AsyncSession = Depends(get_db)
) -> Any:
    role_service = RoleService(db)
    ok = await role_service.delete_role(UUID(role_id))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return {"message": "Role deleted successfully"}


# Current user roles (accessible to any authenticated user)
@router.get("/me/roles", response_model=List[RoleSchema])
async def get_my_roles(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    role_service = RoleService(db)
    return await role_service.list_user_roles(current_user.id)