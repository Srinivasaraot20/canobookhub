"""Add missing columns to user and book tables

Revision ID: 050a613a0b51
Revises: 
Create Date: 2025-07-13 10:34:22.240201

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '050a613a0b51'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Only add the amazon_link column to the book table
    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.add_column(sa.Column('amazon_link', sa.String(length=500), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # Only drop the amazon_link column from the book table
    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.drop_column('amazon_link')

    # ### end Alembic commands ###
