"""Initial migration

Revision ID: 70cb7fab6cf2
Revises: 
Create Date: 2024-12-15 17:24:12.791755

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70cb7fab6cf2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bericht', schema=None) as batch_op:
        batch_op.drop_column('gelezen')

    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.alter_column('locatie',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=200),
               existing_nullable=False)

    with op.batch_alter_table('persoon', schema=None) as batch_op:
        batch_op.drop_column('is_active_flag')

    with op.batch_alter_table('rating', schema=None) as batch_op:
        batch_op.drop_constraint('unique_aanbieder_rating', type_='unique')
        batch_op.drop_constraint('unique_zoeker_rating', type_='unique')
        batch_op.drop_column('ingediend_door_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('rating', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ingediend_door_id', sa.VARCHAR(), autoincrement=False, nullable=True))
        batch_op.create_unique_constraint('unique_zoeker_rating', ['klusnummer', 'kluszoeker_id', 'klusaanbieder_id', 'vriendelijkheid_zoeker'])
        batch_op.create_unique_constraint('unique_aanbieder_rating', ['klusnummer', 'kluszoeker_id', 'klusaanbieder_id', 'vriendelijkheid_aanbieder'])

    with op.batch_alter_table('persoon', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active_flag', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=True))

    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.alter_column('locatie',
               existing_type=sa.String(length=200),
               type_=sa.VARCHAR(length=100),
               existing_nullable=False)

    with op.batch_alter_table('bericht', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gelezen', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=True))

    # ### end Alembic commands ###