"""Fix existing database schema

Revision ID: 68c772525458
Revises: 2151d91a04e4
Create Date: 2024-12-08

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Revision identifiers, used by Alembic.
revision = '68c772525458'
down_revision = '2151d91a04e4'
branch_labels = None
depends_on = None


from sqlalchemy import text

def upgrade():
    # Voeg een standaardpersoon toe aan de tabel 'persoon'
    op.execute("""
        INSERT INTO persoon (idnummer, voornaam, achternaam, email, username, created_at)
        VALUES ('0000000000', 'Onbekend', 'Persoon', 'onbekend@example.com', 'onbekend', NOW())
    """)

    # Voeg de categorie 'onbekend' toe aan de tabel 'categorie'
    op.execute("""
        INSERT INTO categorie (categorie, naam)
        VALUES ('onbekend', 'Onbekende categorie')
        ON CONFLICT (categorie) DO NOTHING
    """)

    # Werk bestaande rijen in de tabel 'klus' bij
    op.execute("""
        UPDATE klus
        SET categorie = 'onbekend'
        WHERE categorie IS NULL
    """)

    # Controleer of de foreign key constraint al bestaat
    conn = op.get_bind()
    result = conn.execute(text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name='klus' AND constraint_name='klus_categorie_fkey'
    """)).fetchone()

    if not result:
        # Stel de foreign key constraint in op 'klus.categorie'
        with op.batch_alter_table('klus', schema=None) as batch_op:
            batch_op.create_foreign_key('klus_categorie_fkey', 'categorie', ['categorie'], ['categorie'])

    # Voeg de kolom 'idnummer' toe aan 'klus' zonder de NOT NULL-beperking
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.add_column(sa.Column('idnummer', sa.String(length=10), nullable=True))

    # Werk bestaande rijen bij met een standaardwaarde voor 'idnummer'
    op.execute("""
        UPDATE klus
        SET idnummer = '0000000000'
        WHERE idnummer IS NULL
    """)

    # Maak de kolom 'idnummer' NOT NULL en stel de foreign key constraint in
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.alter_column('idnummer', nullable=False)
        batch_op.create_foreign_key('klus_idnummer_fkey', 'persoon', ['idnummer'], ['idnummer'])

    # Voer type- en NOT NULL-aanpassingen door op de rest van de kolommen
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.alter_column('beschrijving', existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column('locatie', existing_type=sa.VARCHAR(length=100), nullable=False)
        batch_op.alter_column('tijd', existing_type=sa.VARCHAR(length=50),
                              type_=sa.Time(), existing_nullable=True, nullable=False, postgresql_using="tijd::time")
        batch_op.alter_column('vergoeding', existing_type=sa.NUMERIC(precision=10, scale=2), nullable=False)
        batch_op.alter_column('verwachte_duur', existing_type=sa.VARCHAR(length=255),
                              type_=sa.Integer(), existing_nullable=True, nullable=False,
                              postgresql_using="verwachte_duur::integer")
        batch_op.alter_column('status', existing_type=sa.VARCHAR(length=20), nullable=False)

    # Verwijder ongebruikte kolommen
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.drop_column('aanbieder_id')
        batch_op.drop_column('gebruiker_id')
        batch_op.drop_column('zoeker_id')
        batch_op.drop_column('rol')

    # Pas de tabel 'persoon' aan
    with op.batch_alter_table('persoon', schema=None) as batch_op:
        batch_op.drop_column('rol')

def downgrade():
    # Voeg kolommen terug in 'persoon'
    with op.batch_alter_table('persoon', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rol', sa.VARCHAR(length=50), autoincrement=False, nullable=True))

    # Voeg verwijderde kolommen terug in 'klus'
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rol', sa.VARCHAR(length=20), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('zoeker_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('gebruiker_id', sa.VARCHAR(), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('aanbieder_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.drop_constraint('klus_idnummer_fkey', type_='foreignkey')
        batch_op.drop_constraint('klus_categorie_fkey', type_='foreignkey')
        batch_op.alter_column('status', existing_type=sa.VARCHAR(length=20), nullable=True)
        batch_op.alter_column('verwachte_duur', existing_type=sa.Integer(),
                              type_=sa.VARCHAR(length=255), nullable=True)
        batch_op.alter_column('vergoeding', existing_type=sa.NUMERIC(precision=10, scale=2), nullable=True)
        batch_op.alter_column('tijd', existing_type=sa.Time(),
                              type_=sa.VARCHAR(length=50), nullable=True)
        batch_op.alter_column('locatie', existing_type=sa.VARCHAR(length=100), nullable=True)
        batch_op.alter_column('categorie', existing_type=sa.VARCHAR(length=50), nullable=True)
        batch_op.alter_column('beschrijving', existing_type=sa.TEXT(), nullable=True)
        batch_op.drop_column('idnummer')
