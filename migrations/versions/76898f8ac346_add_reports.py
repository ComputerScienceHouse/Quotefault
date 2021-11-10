"""Add reports

Revision ID: 76898f8ac346
Revises: 4f95c173f1d9
Create Date: 2021-04-23 01:18:03.934757

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '76898f8ac346'
down_revision = '4f95c173f1d9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('report',
    sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
    sa.Column('quote_id', sa.Integer(), nullable=False),
    sa.Column('reporter', sa.Text(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['quote_id'], ['quote.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('quote', sa.Column('hidden', sa.Boolean(), nullable=False, default=False))


def downgrade():
    op.drop_column('quote', 'hidden')
    op.drop_table('report')
