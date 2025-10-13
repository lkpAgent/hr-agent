"""restructure_exam_results_table

Revision ID: a47691a04a41
Revises: b25a4952495f
Create Date: 2025-10-12 22:23:24.071990

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a47691a04a41'
down_revision = 'b25a4952495f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 删除exam_answer_details表（如果存在）
    try:
        op.drop_table('exam_answer_details')
    except:
        pass
    
    # 修改exam_results表结构
    # 添加新字段
    op.add_column('exam_results', sa.Column('exam_name', sa.String(length=200), nullable=True, comment='考试名称'))
    op.add_column('exam_results', sa.Column('exam_data', sa.JSON(), nullable=True, comment='完整考试数据JSON，包含试卷内容、学生答案、评分结果等'))
    
    # 删除不需要的字段
    try:
        op.drop_column('exam_results', 'exam_id')
        op.drop_column('exam_results', 'score_percentage')
        op.drop_column('exam_results', 'start_time')
        op.drop_column('exam_results', 'duration_minutes')
        op.drop_column('exam_results', 'student_answers')
        op.drop_column('exam_results', 'scoring_result')
    except:
        pass


def downgrade() -> None:
    # 删除新的exam_results表
    op.drop_table('exam_results')
    
    # 恢复旧的exam_results表结构（这里只是示例，实际使用时需要根据之前的结构来恢复）
    op.create_table('exam_results',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('exam_id', sa.UUID(), nullable=False),
        sa.Column('student_name', sa.String(length=100), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('total_possible_score', sa.Float(), nullable=False),
        sa.Column('total_actual_score', sa.Float(), nullable=False),
        sa.Column('score_percentage', sa.Float(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('submit_time', sa.DateTime(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('student_answers', sa.JSON(), nullable=True),
        sa.Column('scoring_result', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='completed'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'])
    )
    
    # 恢复exam_answer_details表
    op.create_table('exam_answer_details',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('exam_result_id', sa.UUID(), nullable=False),
        sa.Column('question_id', sa.UUID(), nullable=False),
        sa.Column('question_number', sa.Integer(), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_options', sa.JSON(), nullable=True),
        sa.Column('correct_answer', sa.Text(), nullable=True),
        sa.Column('question_explanation', sa.Text(), nullable=True),
        sa.Column('question_score', sa.Float(), nullable=False),
        sa.Column('student_answer', sa.Text(), nullable=True),
        sa.Column('actual_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_correct', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['exam_result_id'], ['exam_results.id']),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'])
    )