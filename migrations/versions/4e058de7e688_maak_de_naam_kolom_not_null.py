"""Maak de 'naam' kolom NOT NULL

Revision ID: 4e058de7e688
Revises: f656bfba3181
Create Date: 2024-11-27 14:26:44.834359

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e058de7e688'
down_revision = 'f656bfba3181'
branch_labels = None
depends_on = None


def upgrade():
    # Eerst, update de rijen die een NULL waarde hebben in de naam kolom naar een standaardnaam
    op.execute("UPDATE klus SET naam = 'Default Naam' WHERE naam IS NULL")

    # Daarna de kolom wijzigen naar NOT NULL
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.alter_column('naam',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)


def downgrade():
    # Als je de wijziging wilt terugdraaien, maak de kolom weer nullable
    with op.batch_alter_table('klus', schema=None) as batch_op:
        batch_op.alter_column('naam',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
