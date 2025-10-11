"""rename_content_to_extracted_content

Revision ID: d26f470d5e3a
Revises: 39b959fba123
Create Date: 2025-10-03 20:12:02.691837

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd26f470d5e3a'
down_revision = '39b959fba123'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename content column to extracted_content
    op.alter_column('documents', 'content', new_column_name='extracted_content')


def downgrade() -> None:
    # Rename extracted_content column back to content
    op.alter_column('documents', 'extracted_content', new_column_name='content')