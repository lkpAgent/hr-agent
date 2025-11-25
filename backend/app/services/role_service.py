"""
Role service
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate


class RoleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, skip: int = 0, limit: int = 100) -> List[Role]:
        result = await self.db.execute(select(Role).offset(skip).limit(limit).order_by(Role.created_at.desc()))
        return [row[0] for row in result.all()]

    async def get(self, role_id: str) -> Optional[Role]:
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def create(self, data: RoleCreate, created_by: Optional[str] = None) -> Role:
        role = Role(
            name=data.name,
            description=data.description,
            is_builtin=data.is_builtin,
            permissions=data.permissions or [],
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(role)
        await self.db.flush()
        await self.db.refresh(role)
        return role

    async def update(self, role: Role, data: RoleUpdate, updated_by: Optional[str] = None) -> Role:
        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(role, k, v)
        if updated_by:
            role.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(role)
        return role

    async def delete(self, role: Role) -> None:
        await self.db.delete(role)

    async def ensure_default_roles(self) -> None:
        existing = await self.db.execute(select(Role))
        names = {r.name for (r,) in existing.all()}
        to_create = []
        if "普通用户" not in names:
            to_create.append(Role(name="普通用户", description="系统普通用户", is_builtin=True, permissions=[]))
        if "超级管理员" not in names:
            to_create.append(Role(name="超级管理员", description="系统管理权限", is_builtin=True, permissions=[]))
        for r in to_create:
            self.db.add(r)
        if to_create:
            await self.db.flush()
