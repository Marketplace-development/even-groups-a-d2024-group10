"""Add criteria to Rating model

Revision ID: cbe30a00be35
Revises: a4d70130d0e7
Create Date: 2024-12-08 19:06:51.132627

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cbe30a00be35'
down_revision = 'a4d70130d0e7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('categorie_statistiek', schema=None) as batch_op:
        batch_op.drop_constraint('categorie_statistiek_idnummer_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'persoon', ['idnummer'], ['idnummer'], ondelete='CASCADE')

    with op.batch_alter_table('rating', schema=None) as batch_op:
        batch_op.add_column(sa.Column('communicatie', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('betrouwbaarheid', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('tijdigheid', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('kwaliteit', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('algemene_ervaring', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('comment', sa.String(length=500), nullable=True))
        batch_op.drop_column('rating_aanbieder')
        batch_op.drop_column('comment_zoeker')
        batch_op.drop_column('rating_zoeker')
        batch_op.drop_column('comment_aanbieder')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('rating', schema=None) as batch_op:
        batch_op.add_column(sa.Column('comment_aanbieder', sa.VARCHAR(length=500), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('rating_zoeker', sa.INTEGER(), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('comment_zoeker', sa.VARCHAR(length=500), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('rating_aanbieder', sa.INTEGER(), autoincrement=False, nullable=False))
        batch_op.drop_column('comment')
        batch_op.drop_column('algemene_ervaring')
        batch_op.drop_column('kwaliteit')
        batch_op.drop_column('tijdigheid')
        batch_op.drop_column('betrouwbaarheid')
        batch_op.drop_column('communicatie')

    with op.batch_alter_table('categorie_statistiek', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('categorie_statistiek_idnummer_fkey', 'persoon', ['idnummer'], ['idnummer'], ondelete='SET DEFAULT')

    # ### end Alembic commands ###
