"""update problem ticket columns

Revision ID: 370585442352
Revises: 874807329c15
Create Date: 2026-05-20 16:40:04.524151
"""
from alembic import op
import sqlalchemy as sa


revision = '370585442352'
down_revision = '874807329c15'
branch_labels = None
depends_on = None


def upgrade():

    with op.batch_alter_table('problem_ticket', schema=None) as batch_op:
        batch_op.add_column(sa.Column('problem_number', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('priority_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('status_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('created_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('modified_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('hours', sa.Numeric(precision=10, scale=2), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True))

    op.execute("UPDATE problem_ticket SET problem_number = 'PRB-' || id WHERE problem_number IS NULL")

    with op.batch_alter_table('problem_ticket', schema=None) as batch_op:
        batch_op.create_index('ix_problem_ticket_problem_number', ['problem_number'], unique=True)
        batch_op.create_index('ix_problem_ticket_title', ['title'], unique=False)

        batch_op.create_foreign_key(
            'fk_problem_ticket_modified_by_id',
            'flicket_users',
            ['modified_by_id'],
            ['id']
        )

        batch_op.create_foreign_key(
            'fk_problem_ticket_category_id',
            'flicket_category',
            ['category_id'],
            ['id']
        )

        batch_op.create_foreign_key(
            'fk_problem_ticket_status_id',
            'flicket_status',
            ['status_id'],
            ['id']
        )

        batch_op.create_foreign_key(
            'fk_problem_ticket_created_by_id',
            'flicket_users',
            ['created_by_id'],
            ['id']
        )

        batch_op.create_foreign_key(
            'fk_problem_ticket_priority_id',
            'flicket_priorities',
            ['priority_id'],
            ['id']
        )

        batch_op.drop_column('ticket_number')


def downgrade():

    with op.batch_alter_table('problem_ticket', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ticket_number', sa.String(length=100), nullable=True))

    op.execute("UPDATE problem_ticket SET ticket_number = problem_number WHERE ticket_number IS NULL")

    with op.batch_alter_table('problem_ticket', schema=None) as batch_op:
        batch_op.drop_constraint('fk_problem_ticket_modified_by_id', type_='foreignkey')
        batch_op.drop_constraint('fk_problem_ticket_category_id', type_='foreignkey')
        batch_op.drop_constraint('fk_problem_ticket_status_id', type_='foreignkey')
        batch_op.drop_constraint('fk_problem_ticket_created_by_id', type_='foreignkey')
        batch_op.drop_constraint('fk_problem_ticket_priority_id', type_='foreignkey')

        batch_op.drop_index('ix_problem_ticket_title')
        batch_op.drop_index('ix_problem_ticket_problem_number')

        batch_op.drop_column('updated_at')
        batch_op.drop_column('hours')
        batch_op.drop_column('modified_by_id')
        batch_op.drop_column('created_by_id')
        batch_op.drop_column('status_id')
        batch_op.drop_column('category_id')
        batch_op.drop_column('priority_id')
        batch_op.drop_column('problem_number')