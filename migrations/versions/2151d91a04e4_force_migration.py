"""Force migration

Revision ID: 2151d91a04e4
Revises: 180503bd3476
Create Date: 2024-12-07 20:42:31.414369

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2151d91a04e4'
down_revision = '180503bd3476'
branch_labels = None
depends_on = None


def upgrade():
    # Voeg de kolom 'idnummer' toe zonder de NOT NULL-beperking
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.add_column(sa.Column('idnummer', sa.String(length=10), nullable=True))

    # Werk bestaande rijen bij met een standaardwaarde voor 'idnummer'
    op.execute("UPDATE klus SET idnummer = '0000000000' WHERE idnummer IS NULL")

    # Zet de kolom 'idnummer' op NOT NULL
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.alter_column('idnummer', nullable=False)

    # Werk bestaande rijen bij met een standaardwaarde voor 'categorie'
    op.execute("UPDATE klus SET categorie = 'onbekend' WHERE categorie IS NULL")

    # Zet de kolom 'categorie' op NOT NULL
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.alter_column('categorie', nullable=False)

    # Voer overige aanpassingen door
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.alter_column('beschrijving',
                              existing_type=sa.TEXT(),
                              nullable=False)
        batch_op.alter_column('locatie',
                              existing_type=sa.VARCHAR(length=100),
                              nullable=False)
        batch_op.alter_column('tijd',
                              existing_type=sa.VARCHAR(length=50),
                              type_=sa.Time(),
                              nullable=False)
        batch_op.alter_column('vergoeding',
                              existing_type=sa.NUMERIC(precision=10, scale=2),
                              nullable=False)
        batch_op.alter_column('verwachte_duur',
                              existing_type=sa.VARCHAR(length=255),
                              type_=sa.Integer(),
                              nullable=False)
        batch_op.alter_column('status',
                              existing_type=sa.VARCHAR(length=20),
                              nullable=False)
        batch_op.drop_constraint('klus_gebruiker_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('klus_categorie_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'persoon', ['idnummer'], ['idnummer'])
        batch_op.drop_column('aanbieder_id')
        batch_op.drop_column('gebruiker_id')
        batch_op.drop_column('zoeker_id')
        batch_op.drop_column('rol')

    with op.batch_alter_table('persoon', schema=None) as batch_op:
        batch_op.drop_column('rol')


def downgrade():
    # Voeg kolommen terug zoals ze oorspronkelijk waren
    with op.batch_alter_table('persoon', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rol', sa.VARCHAR(length=50), autoincrement=False, nullable=True))

    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rol', sa.VARCHAR(length=20), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('zoeker_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('gebruiker_id', sa.VARCHAR(), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('aanbieder_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('klus_categorie_fkey', 'categorie', ['categorie'], ['categorie'], ondelete='SET NULL')
        batch_op.create_foreign_key('klus_gebruiker_id_fkey', 'persoon', ['gebruiker_id'], ['idnummer'])
        batch_op.alter_column('status',
                              existing_type=sa.VARCHAR(length=20),
                              nullable=True)
        batch_op.alter_column('verwachte_duur',
                              existing_type=sa.Integer(),
                              type_=sa.VARCHAR(length=255),
                              nullable=True)
        batch_op.alter_column('vergoeding',
                              existing_type=sa.NUMERIC(precision=10, scale=2),
                              nullable=True)
        batch_op.alter_column('tijd',
                              existing_type=sa.Time(),
                              type_=sa.VARCHAR(length=50),
                              nullable=True)
        batch_op.alter_column('locatie',
                              existing_type=sa.VARCHAR(length=100),
                              nullable=True)
        batch_op.alter_column('categorie',
                              existing_type=sa.VARCHAR(length=50),
                              nullable=True)
        batch_op.alter_column('beschrijving',
                              existing_type=sa.TEXT(),
                              nullable=True)
        batch_op.drop_column('idnummer')
