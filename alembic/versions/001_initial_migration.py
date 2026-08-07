"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('language', sa.Enum('RU', 'EN', 'ES', 'UK', name='userlanguage'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)

    # Create managers table
    op.create_table('managers',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('ONLINE', 'OFFLINE', 'BUSY', name='managerstatus'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_managers_telegram_id'), 'managers', ['telegram_id'], unique=True)

    # Create tickets table
    op.create_table('tickets',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('ticket_number', sa.String(length=20), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('manager_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.Enum('OPEN', 'IN_PROGRESS', 'WAITING_USER', 'CLOSED', name='ticketstatus'), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['manager_id'], ['managers.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tickets_ticket_number'), 'tickets', ['ticket_number'], unique=True)

    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('ticket_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('manager_id', sa.BigInteger(), nullable=True),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('is_from_user', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['manager_id'], ['managers.id'], ),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('messages')
    op.drop_index(op.f('ix_tickets_ticket_number'), table_name='tickets')
    op.drop_table('tickets')
    op.drop_index(op.f('ix_managers_telegram_id'), table_name='managers')
    op.drop_table('managers')
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_table('users')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS userlanguage')
    op.execute('DROP TYPE IF EXISTS managerstatus')
    op.execute('DROP TYPE IF EXISTS ticketstatus')

