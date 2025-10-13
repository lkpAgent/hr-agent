"""merge_branches

Revision ID: 9d899c6b07ba
Revises: 4b02bc04eb04, 50bc460f1b38
Create Date: 2025-10-12 22:09:41.941787

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d899c6b07ba'
down_revision = ('4b02bc04eb04', '50bc460f1b38')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass