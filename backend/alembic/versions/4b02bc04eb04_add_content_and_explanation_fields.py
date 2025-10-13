"""add_content_and_explanation_fields

Revision ID: 4b02bc04eb04
Revises: e2db54e884b9
Create Date: 2025-10-12 14:06:07.798273

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b02bc04eb04'
down_revision = 'e2db54e884b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 在exams表中添加content字段
    op.add_column('exams', sa.Column('content', sa.Text(), nullable=True, comment='原始试卷内容'))
    
    # 在questions表中添加explanation字段
    op.add_column('questions', sa.Column('explanation', sa.Text(), nullable=True, comment='题目解释'))


def downgrade() -> None:
    # 删除添加的字段
    op.drop_column('questions', 'explanation')
    op.drop_column('exams', 'content')