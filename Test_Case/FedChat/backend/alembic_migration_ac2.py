"""Add AC-2 account management fields

Revision ID: ac2_account_management
Revises: 
Create Date: 2026-02-15

NIST 800-53 AC-2 - Account Management
Adds fields for account lifecycle tracking and automated management
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'ac2_account_management'
down_revision = None  # Set to your last migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add AC-2 compliance fields to users table"""
    
    # Add new columns to users table
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('account_locked_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('account_status', sa.String(50), server_default='active', nullable=False))
    op.add_column('users', sa.Column('disabled_reason', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('disabled_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('disabled_by', UUID(as_uuid=True), nullable=True))
    op.add_column('users', sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('password_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('account_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('last_modified', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('last_modified_by', UUID(as_uuid=True), nullable=True))
    
    # Add foreign key constraints
    op.create_foreign_key(
        'fk_users_disabled_by',
        'users', 'users',
        ['disabled_by'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_users_last_modified_by',
        'users', 'users',
        ['last_modified_by'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add index on account_status for faster queries
    op.create_index('ix_users_account_status', 'users', ['account_status'])
    
    # Add index on last_activity for inactivity checks
    op.create_index('ix_users_last_activity', 'users', ['last_activity'])


def downgrade() -> None:
    """Remove AC-2 compliance fields"""
    
    # Drop indexes
    op.drop_index('ix_users_last_activity', 'users')
    op.drop_index('ix_users_account_status', 'users')
    
    # Drop foreign keys
    op.drop_constraint('fk_users_last_modified_by', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_disabled_by', 'users', type_='foreignkey')
    
    # Drop columns
    op.drop_column('users', 'last_modified_by')
    op.drop_column('users', 'last_modified')
    op.drop_column('users', 'account_expires_at')
    op.drop_column('users', 'password_expires_at')
    op.drop_column('users', 'last_activity')
    op.drop_column('users', 'disabled_by')
    op.drop_column('users', 'disabled_at')
    op.drop_column('users', 'disabled_reason')
    op.drop_column('users', 'account_status')
    op.drop_column('users', 'account_locked_until')
    op.drop_column('users', 'failed_login_attempts')
