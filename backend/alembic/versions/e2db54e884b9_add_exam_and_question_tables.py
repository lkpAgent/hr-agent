"""add_exam_and_question_tables

Revision ID: e2db54e884b9
Revises: 50bc460f1b38
Create Date: 2025-10-12 13:57:58.302510

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e2db54e884b9'
down_revision = '079c42b7a8b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create exams table
    op.create_table('exams',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False, comment='试卷标题'),
        sa.Column('subject', sa.String(length=100), nullable=False, comment='科目'),
        sa.Column('description', sa.Text(), nullable=True, comment='试卷描述'),
        sa.Column('difficulty', sa.String(length=50), nullable=False, comment='难度等级'),
        sa.Column('duration', sa.Integer(), nullable=False, comment='考试时长(分钟)'),
        sa.Column('total_score', sa.Float(), nullable=False, comment='总分'),
        sa.Column('question_types', sa.JSON(), nullable=True, comment='题型配置'),
        sa.Column('question_counts', sa.JSON(), nullable=True, comment='题目数量配置'),
        sa.Column('knowledge_files', sa.JSON(), nullable=True, comment='知识库文件'),
        sa.Column('special_requirements', sa.Text(), nullable=True, comment='特殊要求'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exams_id'), 'exams', ['id'], unique=False)

    # Create questions table
    op.create_table('questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('exam_id', postgresql.UUID(as_uuid=True), nullable=False, comment='所属试卷ID'),
        sa.Column('question_type', sa.String(length=50), nullable=False, comment='题型'),
        sa.Column('question_text', sa.Text(), nullable=False, comment='题目内容'),
        sa.Column('options', sa.JSON(), nullable=True, comment='选择题选项'),
        sa.Column('correct_answer', sa.Text(), nullable=True, comment='正确答案'),
        sa.Column('score', sa.Float(), nullable=False, comment='分值'),
        sa.Column('order_index', sa.Integer(), nullable=False, comment='题目顺序'),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questions_id'), 'questions', ['id'], unique=False)


def downgrade() -> None:
    # Drop questions table
    op.drop_index(op.f('ix_questions_id'), table_name='questions')
    op.drop_table('questions')
    
    # Drop exams table
    op.drop_index(op.f('ix_exams_id'), table_name='exams')
    op.drop_table('exams')