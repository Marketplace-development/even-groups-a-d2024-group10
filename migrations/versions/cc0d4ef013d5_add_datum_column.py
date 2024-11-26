"""Add datum column

Revision ID: cc0d4ef013d5
Revises: 4e058de7e688
Create Date: 2024-11-27 17:47:42.887189

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc0d4ef013d5'
down_revision = '4e058de7e688'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.add_column(sa.Column('datum', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('verwachte_duur', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.drop_column('verwachte_duur')
        batch_op.drop_column('datum')

    # ### end Alembic commands ###
