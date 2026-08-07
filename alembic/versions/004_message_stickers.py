"""Allow messages to carry a sticker instead of text

Revision ID: 004
Revises: 003
Create Date: 2026-08-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('messages', sa.Column('sticker_file_id', sa.String(length=255), nullable=True))
    op.alter_column('messages', 'message_text', existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    op.execute("UPDATE messages SET message_text = '' WHERE message_text IS NULL")
    op.alter_column('messages', 'message_text', existing_type=sa.Text(), nullable=False)
    op.drop_column('messages', 'sticker_file_id')
