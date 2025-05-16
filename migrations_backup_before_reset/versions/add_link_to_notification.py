"""add link column to notification table

Revision ID: add_link_to_notification
Revises: 47838d12c451
Create Date: 2024-04-28

"""
revision = 'add_link_to_notification'
down_revision = '47838d12c451'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('notifications', sa.Column('link', sa.String(length=255), nullable=True))

def downgrade():
    op.drop_column('notifications', 'link') 