"""add_file_hash_to_documents

Revision ID: 39b959fba123
Revises: 
Create Date: 2025-10-03 20:09:11.333011

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '39b959fba123'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add file_hash column to documents table
    op.add_column('documents', sa.Column('file_hash', sa.String(length=64), nullable=True))
    
    # Create index on file_hash for better query performance
    op.create_index('ix_documents_file_hash', 'documents', ['file_hash'])


def downgrade() -> None:
    # Remove index and column
    op.drop_index('ix_documents_file_hash', table_name='documents')
    op.drop_column('documents', 'file_hash')