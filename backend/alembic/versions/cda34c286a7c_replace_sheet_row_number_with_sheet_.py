"""replace_sheet_row_number_with_sheet_item_id

Revision ID: cda34c286a7c
Revises: 2b9e9c5c4c7f
Create Date: 2025-01-07 05:51:20.598096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cda34c286a7c'
down_revision: Union[str, None] = '2b9e9c5c4c7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Replace sheet_row_number with sheet_item_id
    # First add the new column
    op.add_column('line_items', sa.Column('sheet_item_id', sa.String(), nullable=True))
    
    # Drop the old column
    op.drop_column('line_items', 'sheet_row_number')


def downgrade() -> None:
    # Restore sheet_row_number column
    op.add_column('line_items', sa.Column('sheet_row_number', sa.Integer(), nullable=True))
    
    # Drop the new column
    op.drop_column('line_items', 'sheet_item_id') 