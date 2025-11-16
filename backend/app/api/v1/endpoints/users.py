"""
User management endpoints
"""
from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import User as UserSchema, UserUpdate, UserCreate, Role as RoleSchema, RoleCreate, AssignRolesRequest, UserWithRoles
from app.services.user_service import UserService, RoleService
from app.api.deps import get_current_user, get_current_admin_by_role
from app.models.user import UserRole

router = APIRouter()


@router.get("/", response_model=List[UserWithRoles])
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
    role_service = RoleService(db)
    user_ids = [u.id for u in users]
    roles_map = await role_service.get_roles_for_users(user_ids)

    result: List[dict] = []
    for u in users:
        roles = roles_map.get(u.id, [])
        role_names = {r.name for r in roles}
        # 仅根据角色表确定管理员身份
        derived_role = UserRole.ADMIN if "超级管理员" in role_names else UserRole.EMPLOYEE
        result.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "phone": u.phone,
            "department": u.department,
            "position": u.position,
            "employee_id": u.employee_id,
            "role": derived_role,
            "is_superuser": u.is_superuser,
            "is_verified": u.is_verified,
            "is_active": u.is_active,
            "bio": u.bio,
            "avatar_url": u.avatar_url,
            "last_login": u.last_login,
            "created_at": u.created_at,
            "updated_at": u.updated_at,
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
        })
    return result


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