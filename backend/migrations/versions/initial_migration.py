"""Initial migration

Revision ID: initial_migration
Revises: 
Create Date: 2024-04-27 16:48:31.573

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create enum type for delivery status
    delivery_status = postgresql.ENUM('pending', 'in_progress', 'delivered', 'failed', 'max_retries_exceeded',
                                     name='deliverystatus')
    delivery_status.create(op.get_bind())

    # Create subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_url', sa.String(), nullable=False),
        sa.Column('secret', sa.String(), nullable=True),
        sa.Column('event_types', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create webhook_deliveries table
    op.create_table('webhook_deliveries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'delivered', 'failed', 'max_retries_exceeded',
                                   name='deliverystatus'), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_attempt', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_retry', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.String(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('webhook_deliveries')
    op.drop_table('subscriptions')
    delivery_status = postgresql.ENUM('pending', 'in_progress', 'delivered', 'failed', 'max_retries_exceeded',
                                     name='deliverystatus')
    delivery_status.drop(op.get_bind())