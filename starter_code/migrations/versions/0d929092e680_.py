"""empty message

Revision ID: 0d929092e680
Revises: fbd0f2f06ed3
Create Date: 2020-10-05 16:35:07.356701

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d929092e680'
down_revision = 'fbd0f2f06ed3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('artist', sa.Column('website', sa.String(length=500), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('artist', 'website')
    # ### end Alembic commands ###
