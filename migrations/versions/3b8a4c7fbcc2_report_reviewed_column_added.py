"""Report Reviewed Column Added

Revision ID: 3b8a4c7fbcc2
Revises: 76898f8ac346
Create Date: 2021-11-07 22:31:04.835460

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b8a4c7fbcc2'
down_revision = '76898f8ac346'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('report', sa.Column('reviewed', sa.Boolean(), nullable=False, default=False))


def downgrade():
    op.drop_column('report', 'reviewed')

