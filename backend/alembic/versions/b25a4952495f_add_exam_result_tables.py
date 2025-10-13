"""add_exam_result_tables

Revision ID: b25a4952495f
Revises: 9d899c6b07ba
Create Date: 2025-10-12 22:10:25.491718

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b25a4952495f'
down_revision = '9d899c6b07ba'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create exam_results table
    op.create_table('exam_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('exam_id', postgresql.UUID(as_uuid=True), nullable=False, comment='试卷ID'),
        sa.Column('student_name', sa.String(length=100), nullable=False, comment='考生姓名'),
        sa.Column('department', sa.String(length=100), nullable=True, comment='考生部门'),
        sa.Column('total_possible_score', sa.Float(), nullable=False, comment='试卷总分'),
        sa.Column('total_actual_score', sa.Float(), nullable=False, comment='实际得分'),
        sa.Column('score_percentage', sa.Float(), nullable=True, comment='得分率'),
        sa.Column('start_time', sa.DateTime(), nullable=True, comment='开始考试时间'),
        sa.Column('submit_time', sa.DateTime(), nullable=True, comment='提交时间'),
        sa.Column('duration_minutes', sa.Integer(), nullable=True, comment='实际考试时长(分钟)'),
        sa.Column('student_answers', sa.JSON(), nullable=True, comment='学生原始答案JSON'),
        sa.Column('scoring_result', sa.JSON(), nullable=True, comment='Dify评分原始结果'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='考试状态'),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exam_results_id'), 'exam_results', ['id'], unique=False)

    # Create exam_answer_details table
    op.create_table('exam_answer_details',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('exam_result_id', postgresql.UUID(as_uuid=True), nullable=False, comment='考试结果ID'),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False, comment='题目ID'),
        sa.Column('question_number', sa.Integer(), nullable=False, comment='题目编号'),
        sa.Column('question_type', sa.String(length=50), nullable=False, comment='题目类型'),
        sa.Column('question_text', sa.Text(), nullable=False, comment='题目内容'),
        sa.Column('question_options', sa.JSON(), nullable=True, comment='题目选项'),
        sa.Column('correct_answer', sa.Text(), nullable=True, comment='标准答案'),
        sa.Column('question_explanation', sa.Text(), nullable=True, comment='题目解析'),
        sa.Column('question_score', sa.Float(), nullable=False, comment='题目分值'),
        sa.Column('student_answer', sa.Text(), nullable=True, comment='学生答案'),
        sa.Column('actual_score', sa.Float(), nullable=False, comment='实际得分'),
        sa.Column('is_correct', sa.String(length=20), nullable=True, comment='答题正确性'),
        sa.ForeignKeyConstraint(['exam_result_id'], ['exam_results.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exam_answer_details_id'), 'exam_answer_details', ['id'], unique=False)


def downgrade() -> None:
    # Drop exam_answer_details table
    op.drop_index(op.f('ix_exam_answer_details_id'), table_name='exam_answer_details')
    op.drop_table('exam_answer_details')
    
    # Drop exam_results table
    op.drop_index(op.f('ix_exam_results_id'), table_name='exam_results')
    op.drop_table('exam_results')