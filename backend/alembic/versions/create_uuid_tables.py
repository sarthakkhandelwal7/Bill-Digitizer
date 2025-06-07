"""create_uuid_tables

Revision ID: create_uuid_tables
Revises: 
Create Date: 2024-12-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'create_uuid_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable uuid-ossp extension for UUID generation
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create users table with UUID
    op.create_table('users',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('given_name', sa.String(), nullable=True),
        sa.Column('family_name', sa.String(), nullable=True),
        sa.Column('picture_url', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('auth_provider', sa.String(), nullable=True),
        sa.Column('google_id', sa.String(), nullable=True),
        sa.Column('google_verified_email', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=True),
        sa.Column('subscription_status', sa.String(), nullable=True),
        sa.Column('subscription_plan', sa.String(), nullable=True),
        sa.Column('trial_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('subscription_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('subscription_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('bills_processed_count', sa.Integer(), nullable=True),
        sa.Column('monthly_bills_limit', sa.Integer(), nullable=True),
        sa.Column('last_bill_processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timezone', sa.String(), nullable=True),
        sa.Column('locale', sa.String(), nullable=True),
        sa.Column('preferences', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for users table
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=True)
    op.create_index(op.f('ix_users_stripe_customer_id'), 'users', ['stripe_customer_id'], unique=True)
    
    # Create bills table with UUID
    op.create_table('bills',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True),
        sa.Column('document_type', sa.String(), nullable=True),
        sa.Column('merchant_company_name', sa.String(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('phone_number', sa.String(), nullable=True),
        sa.Column('date', sa.String(), nullable=True),
        sa.Column('time', sa.String(), nullable=True),
        sa.Column('transaction_id', sa.String(), nullable=True),
        sa.Column('subtotal', sa.Float(), nullable=True),
        sa.Column('tax', sa.Float(), nullable=True),
        sa.Column('discount_savings', sa.Float(), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=True),
        sa.Column('payment_method', sa.String(), nullable=True),
        sa.Column('card_last_four', sa.String(), nullable=True),
        sa.Column('approval_code', sa.String(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('other_info', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_bills_user_id')
    )
    
    # Create indexes for bills table
    op.create_index(op.f('ix_bills_id'), 'bills', ['id'], unique=False)
    op.create_index(op.f('ix_bills_user_id'), 'bills', ['user_id'], unique=False)
    op.create_index(op.f('ix_bills_merchant_company_name'), 'bills', ['merchant_company_name'], unique=False)
    op.create_index(op.f('ix_bills_transaction_id'), 'bills', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_bills_total_amount'), 'bills', ['total_amount'], unique=False)
    
    # Create line_items table with UUID
    op.create_table('line_items',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('total_price_per_item', sa.Float(), nullable=True),
        sa.Column('bill_id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], name='fk_line_items_bill_id')
    )
    
    # Create indexes for line_items table
    op.create_index(op.f('ix_line_items_id'), 'line_items', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('line_items')
    op.drop_table('bills') 
    op.drop_table('users') 