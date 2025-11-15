"""add_role_and_user_role_tables

Revision ID: c8a1f2d3e4b5
Revises: a47691a04a41
Create Date: 2025-11-15 10:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c8a1f2d3e4b5'
down_revision = 'a47691a04a41'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create role table
    op.create_table('role',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_builtin', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_role_name')
    )
    op.create_index(op.f('ix_role_id'), 'role', ['id'], unique=False)
    op.create_index(op.f('ix_role_name'), 'role', ['name'], unique=False)

    # Create user_role association table
    op.create_table('user_role',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role_user_id_role_id')
    )
    op.create_index(op.f('ix_user_role_id'), 'user_role', ['id'], unique=False)
    op.create_index(op.f('ix_user_role_user_id'), 'user_role', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_role_role_id'), 'user_role', ['role_id'], unique=False)

    # Seed default roles and assign testuser
    bind = op.get_bind()
    try:
        from datetime import datetime
        import uuid
        from app.core.security import get_password_hash

        now = datetime.utcnow()
        # Insert default roles if not exist
        roles = [
            {"name": "普通用户", "description": "默认普通用户角色", "is_builtin": True},
            {"name": "超级管理员", "description": "系统超级管理员角色", "is_builtin": True},
        ]

        for r in roles:
            exists = bind.execute(sa.text("SELECT 1 FROM role WHERE name = :name"), {"name": r["name"]}).fetchone()
            if not exists:
                bind.execute(sa.text(
                    """
                    INSERT INTO role (id, created_at, updated_at, is_active, created_by, updated_by, name, description, is_builtin)
                    VALUES (:id, :created_at, :updated_at, true, NULL, NULL, :name, :description, :is_builtin)
                    """
                ), {
                    "id": uuid.uuid4(),
                    "created_at": now,
                    "updated_at": now,
                    "name": r["name"],
                    "description": r["description"],
                    "is_builtin": r["is_builtin"],
                })

        # Ensure testuser exists with super admin role
        user = bind.execute(sa.text("SELECT id, is_superuser FROM users WHERE username = :u AND is_active = true"), {"u": "testuser"}).fetchone()
        if not user:
            hashed = get_password_hash("test123")
            user_id = uuid.uuid4()
            bind.execute(sa.text(
                """
                INSERT INTO users (id, created_at, updated_at, is_active, created_by, updated_by,
                                   username, email, full_name, hashed_password, role, is_superuser, is_verified)
                VALUES (:id, :created_at, :updated_at, true, NULL, NULL,
                        :username, :email, :full_name, :hashed_password, :role, :is_superuser, :is_verified)
                """
            ), {
                "id": user_id,
                "created_at": now,
                "updated_at": now,
                "username": "testuser",
                "email": "testuser@example.com",
                "full_name": "Test User",
                "hashed_password": hashed,
                "role": "admin",
                "is_superuser": True,
                "is_verified": True,
            })
        else:
            user_id = user[0]
            # Ensure is_superuser
            if not user[1]:
                bind.execute(sa.text("UPDATE users SET is_superuser = true WHERE id = :id"), {"id": user_id})

        # Assign super admin role
        super_admin_role = bind.execute(sa.text("SELECT id FROM role WHERE name = :name"), {"name": "超级管理员"}).fetchone()
        if super_admin_role:
            rid = super_admin_role[0]
            exists_link = bind.execute(sa.text("SELECT 1 FROM user_role WHERE user_id = :uid AND role_id = :rid"), {"uid": user_id, "rid": rid}).fetchone()
            if not exists_link:
                bind.execute(sa.text(
                    """
                    INSERT INTO user_role (id, created_at, updated_at, is_active, created_by, updated_by, user_id, role_id)
                    VALUES (:id, :created_at, :updated_at, true, NULL, NULL, :uid, :rid)
                    """
                ), {
                    "id": uuid.uuid4(),
                    "created_at": now,
                    "updated_at": now,
                    "uid": user_id,
                    "rid": rid,
                })
    except Exception:
        pass


def downgrade() -> None:
    op.drop_index(op.f('ix_user_role_role_id'), table_name='user_role')
    op.drop_index(op.f('ix_user_role_user_id'), table_name='user_role')
    op.drop_index(op.f('ix_user_role_id'), table_name='user_role')
    op.drop_table('user_role')

    op.drop_index(op.f('ix_role_name'), table_name='role')
    op.drop_index(op.f('ix_role_id'), table_name='role')
    op.drop_table('role')