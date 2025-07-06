"""add_sheet_row_number_to_line_items

Revision ID: 2b9e9c5c4c7f
Revises: e16a5ff5ad3b
Create Date: 2025-07-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '2b9e9c5c4c7f'
down_revision: Union[str, None] = 'e16a5ff5ad3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('line_items', sa.Column('sheet_row_number', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('line_items', 'sheet_row_number') 