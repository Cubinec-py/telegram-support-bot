"""Add Ticket.last_activity_at, drop redundant Message.is_from_user

Revision ID: 002
Revises: 001
Create Date: 2026-08-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'tickets',
        sa.Column('last_activity_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.alter_column('tickets', 'last_activity_at', server_default=None)

    op.drop_column('messages', 'is_from_user')


def downgrade() -> None:
    op.add_column('messages', sa.Column('is_from_user', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.alter_column('messages', 'is_from_user', server_default=None)

    op.drop_column('tickets', 'last_activity_at')
