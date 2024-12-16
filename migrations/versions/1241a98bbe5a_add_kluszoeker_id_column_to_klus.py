"""Add kluszoeker_id column to Klus

Revision ID: 1241a98bbe5a
Revises: 70cb7fab6cf2
Create Date: 2024-12-16 19:22:34.151513

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1241a98bbe5a'
down_revision = '70cb7fab6cf2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.add_column(sa.Column('kluszoeker_id', sa.String(length=10), nullable=True))
        batch_op.create_foreign_key(None, 'persoon', ['kluszoeker_id'], ['idnummer'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('kluszoeker_id')

    # ### end Alembic commands ###