"""rename_uploaded_by_id_to_user_id

Revision ID: aea3521bf67c
Revises: d26f470d5e3a
Create Date: 2025-10-03 20:12:34.872406

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aea3521bf67c'
down_revision = 'd26f470d5e3a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename uploaded_by_id column to user_id
    op.alter_column('documents', 'uploaded_by_id', new_column_name='user_id')


def downgrade() -> None:
    # Rename user_id column back to uploaded_by_id
    op.alter_column('documents', 'user_id', new_column_name='uploaded_by_id')