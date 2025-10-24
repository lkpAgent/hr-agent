"""Change work_years to Float and convert existing data

Revision ID: 7f8e6d3da9c1
Revises: 079c42b7a8b8
Create Date: 2025-10-24 10:27:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f8e6d3da9c1'
down_revision = '079c42b7a8b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Alter resume_evaluations.work_years from String to Float.
    Attempt best-effort conversion of existing string values to numbers.
    """
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        # Use regex to extract the first numeric token and cast to double precision
        # Examples handled: "3年" -> 3, "1.5年" -> 1.5, "1-3年" -> 1, "约2年" -> 2
        op.alter_column(
            'resume_evaluations',
            'work_years',
            type_=sa.Float(),
            existing_type=sa.String(length=50),
            postgresql_using="NULLIF(regexp_replace(work_years, '^(?:[^0-9]*)(\\d+(?:\\.\\d+)?).*$', '\\1'), '')::double precision"
        )
    else:
        # Generic fallback: alter type without automatic conversion (may set NULL if incompatible)
        # Some dialects support implicit conversion; if not, values failing conversion will be NULL.
        op.alter_column(
            'resume_evaluations',
            'work_years',
            type_=sa.Float(),
            existing_type=sa.String(length=50),
            existing_nullable=True
        )


def downgrade() -> None:
    """Revert work_years back to String(50)."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        # Convert numeric back to text
        op.alter_column(
            'resume_evaluations',
            'work_years',
            type_=sa.String(length=50),
            existing_type=sa.Float(),
            postgresql_using='work_years::text'
        )
    else:
        op.alter_column(
            'resume_evaluations',
            'work_years',
            type_=sa.String(length=50),
            existing_type=sa.Float(),
            existing_nullable=True
        )