"""Verander verwachte_duur van integer naar time

Revision ID: b86dc2dd2609
Revises: cc0d4ef013d5
Create Date: 2024-12-02 15:09:53.057771

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b86dc2dd2609'
down_revision = 'cc0d4ef013d5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.alter_column('tijd',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.Time(),
               nullable=False)
        batch_op.alter_column('datum',
               existing_type=sa.DATE(),
               nullable=False)
        batch_op.alter_column('verwachte_duur',
               existing_type=sa.INTEGER(),
               type_=sa.Time(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.alter_column('verwachte_duur',
               existing_type=sa.Time(),
               type_=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('datum',
               existing_type=sa.DATE(),
               nullable=True)
        batch_op.alter_column('tijd',
               existing_type=sa.Time(),
               type_=sa.VARCHAR(length=50),
               nullable=True)

    # ### end Alembic commands ###
