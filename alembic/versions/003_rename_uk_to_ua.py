"""Rename userlanguage enum value UK to UA

Revision ID: 003
Revises: 002
Create Date: 2026-08-07 00:00:00.000000

SQLAlchemy's native Enum(UserLanguage) stores the Python enum member's
*name* in Postgres (RU/EN/ES/UK), not its .value — so renaming the Python
member from UK to UA requires renaming the Postgres enum label too, or
existing/new rows using it will fail to load. ALTER TYPE ... RENAME VALUE
does this in place: existing rows keep pointing at the same enum OID, so
no data UPDATE is needed, they just read back as 'UA' afterwards.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE userlanguage RENAME VALUE 'UK' TO 'UA'")


def downgrade() -> None:
    op.execute("ALTER TYPE userlanguage RENAME VALUE 'UA' TO 'UK'")
