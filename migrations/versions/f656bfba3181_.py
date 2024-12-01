from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f656bfba3181'
down_revision = '5c8808223305'
branch_labels = None
depends_on = None


def upgrade():
    # Voeg de nieuwe kolom 'naam' toe als nullable (tijdelijk)
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.add_column(sa.Column('naam', sa.String(length=100), nullable=True))  # kolom is tijdelijk nullable

    # Hier kun je extra stappen toevoegen om de bestaande rijen bij te werken,
    # bijvoorbeeld door een default waarde in te stellen:
    # op.execute("UPDATE klus SET naam = 'Default Naam' WHERE naam IS NULL")

    # Na het bijwerken van de rijen, kan de kolom worden ingesteld als NOT NULL
    # Voor nu doen we dit in de volgende migratie

def downgrade():
    # Verwijder de kolom 'naam' als we terug willen naar de vorige staat
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.drop_column('naam')

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f656bfba3181'
down_revision = '5c8808223305'
branch_labels = None
depends_on = None


def upgrade():
    # Voeg de nieuwe kolom 'naam' toe als nullable (tijdelijk)
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.add_column(sa.Column('naam', sa.String(length=100), nullable=True))  # kolom is tijdelijk nullable

    # Update bestaande rijen met een default naam (bijvoorbeeld 'Default Naam')
    op.execute("UPDATE klus SET naam = 'Default Naam' WHERE naam IS NULL")


def downgrade():
    # Verwijder de kolom 'naam' als we terug willen naar de vorige staat
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.drop_column('naam')
