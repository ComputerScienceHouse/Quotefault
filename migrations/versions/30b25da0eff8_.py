"""empty message

Revision ID: 30b25da0eff8
Revises: 
Create Date: 2017-08-27 01:14:47.685133

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30b25da0eff8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('quote',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('submitter', sa.String(length=80), nullable=True),
    sa.Column('quote', sa.String(length=200), nullable=True),
    sa.Column('speaker', sa.String(length=50), nullable=True),
    sa.Column('quoteTime', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('quote')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('quote')
    # ### end Alembic commands ###