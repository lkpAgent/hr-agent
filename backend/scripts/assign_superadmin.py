#!/usr/bin/env python3
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import uuid

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings


def get_engine():
    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    return create_engine(sync_url, echo=False, pool_pre_ping=True)


def ensure_role(conn, name: str, description: str, is_builtin: bool = True):
    role = conn.execute(text("SELECT id FROM roles WHERE name = :name"), {"name": name}).fetchone()
    if role:
        return role[0]
    new_id = str(uuid.uuid4())
    conn.execute(
        text(
            """
            INSERT INTO roles (id, name, description, is_builtin, permissions, created_at, updated_at, is_active)
            VALUES (:id, :name, :description, :is_builtin, '[]'::json, NOW(), NOW(), true)
            ON CONFLICT (name) DO NOTHING
            """
        ),
        {"id": new_id, "name": name, "description": description, "is_builtin": is_builtin},
    )
    role = conn.execute(text("SELECT id FROM roles WHERE name = :name"), {"name": name}).fetchone()
    return role[0]


def get_user(conn, username: str):
    return conn.execute(text("SELECT id FROM users WHERE username = :u"), {"u": username}).fetchone()


def assign_superadmin(username: str):
    engine = get_engine()
    with engine.begin() as conn:
        user = get_user(conn, username)
        if not user:
            print(f"用户 '{username}' 不存在")
            return 1
        user_id = user[0]

        role_id = ensure_role(conn, "超级管理员", "系统管理权限", True)

        # Insert mapping if not exists
        exists = conn.execute(
            text("SELECT 1 FROM user_roles WHERE user_id = :uid AND role_id = :rid"),
            {"uid": user_id, "rid": role_id},
        ).fetchone()
        if not exists:
            conn.execute(
                text(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (:uid, :rid)"
                ),
                {"uid": user_id, "rid": role_id},
            )

        # Mark user as superuser
        conn.execute(
            text("UPDATE users SET is_superuser = true, updated_at = NOW() WHERE id = :uid"),
            {"uid": user_id},
        )

        print(f"已为用户 '{username}' 设置超级管理员角色并开启超管标识")
        return 0


def main():
    username = None
    if len(sys.argv) >= 2:
        username = sys.argv[1]
    if not username:
        print("用法: python scripts/assign_superadmin.py <username>")
        sys.exit(1)
    code = assign_superadmin(username)
    sys.exit(code)


if __name__ == "__main__":
    main()
