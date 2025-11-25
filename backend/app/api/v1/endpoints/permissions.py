"""
Permission endpoints (static tree for now)
"""
from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.schemas.user import User as UserSchema


router = APIRouter()


@router.get("/")
async def list_permissions(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return {"items": [
        {"id": "user.manage", "name": "用户管理", "code": "user.manage", "description": "用户管理相关权限"},
        {"id": "role.manage", "name": "角色管理", "code": "role.manage", "description": "角色管理相关权限"},
        {"id": "email.manage", "name": "邮箱管理", "code": "email.manage", "description": "邮箱管理相关权限"},
    ]}


@router.get("/tree")
async def permission_tree(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return {"items": [
        {
            "id": "user.manage",
            "name": "用户管理",
            "code": "user.manage",
            "description": "用户管理相关权限",
            "children": [
                {"id": "user.read", "name": "查看用户", "code": "user.read", "description": "查看用户列表和详情"},
                {"id": "user.create", "name": "创建用户", "code": "user.create", "description": "创建新用户"},
                {"id": "user.update", "name": "更新用户", "code": "user.update", "description": "更新用户信息"},
                {"id": "user.delete", "name": "删除用户", "code": "user.delete", "description": "删除用户"},
            ]
        },
        {
            "id": "role.manage",
            "name": "角色管理",
            "code": "role.manage",
            "description": "角色管理相关权限",
            "children": [
                {"id": "role.read", "name": "查看角色", "code": "role.read", "description": "查看角色列表和详情"},
                {"id": "role.create", "name": "创建角色", "code": "role.create", "description": "创建新角色"},
                {"id": "role.update", "name": "更新角色", "code": "role.update", "description": "更新角色信息"},
                {"id": "role.delete", "name": "删除角色", "code": "role.delete", "description": "删除角色"},
            ]
        },
        {
            "id": "email.manage",
            "name": "邮箱管理",
            "code": "email.manage",
            "description": "邮箱管理相关权限",
            "children": [
                {"id": "email.read", "name": "查看邮箱配置", "code": "email.read", "description": "查看邮箱配置列表"},
                {"id": "email.create", "name": "创建邮箱配置", "code": "email.create", "description": "创建新邮箱配置"},
                {"id": "email.update", "name": "更新邮箱配置", "code": "email.update", "description": "更新邮箱配置"},
                {"id": "email.delete", "name": "删除邮箱配置", "code": "email.delete", "description": "删除邮箱配置"},
                {"id": "email.test", "name": "测试邮箱连接", "code": "email.test", "description": "测试邮箱连接"},
                {"id": "email.fetch", "name": "抓取简历", "code": "email.fetch", "description": "手动触发简历抓取"},
            ]
        },
    ]}

