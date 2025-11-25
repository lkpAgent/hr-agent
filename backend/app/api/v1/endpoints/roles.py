"""
Role management endpoints
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_superuser, get_current_user
from app.schemas.user import User as UserSchema
from app.schemas.role import Role as RoleSchema, RoleCreate, RoleUpdate
from app.services.role_service import RoleService


router = APIRouter()


@router.get("/", response_model=List[RoleSchema])
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    svc = RoleService(db)
    roles = await svc.list(skip=skip, limit=limit)
    return roles


@router.post("/", response_model=RoleSchema)
async def create_role(
    data: RoleCreate,
    current_user: UserSchema = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    svc = RoleService(db)
    role = await svc.create(data, created_by=str(current_user.id))
    return role


@router.get("/{role_id}", response_model=RoleSchema)
async def get_role(
    role_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    svc = RoleService(db)
    role = await svc.get(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.put("/{role_id}", response_model=RoleSchema)
async def update_role(
    role_id: str,
    data: RoleUpdate,
    current_user: UserSchema = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    svc = RoleService(db)
    role = await svc.get(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    updated = await svc.update(role, data, updated_by=str(current_user.id))
    return updated


@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    current_user: UserSchema = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    svc = RoleService(db)
    role = await svc.get(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.is_builtin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Built-in role cannot be deleted")
    await svc.delete(role)
    return {"message": "Role deleted"}
