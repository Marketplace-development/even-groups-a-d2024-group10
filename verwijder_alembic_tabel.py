from sqlalchemy import create_engine

# Verbind met je database (vervang de juiste gegevens)
engine = create_engine('postgresql://postgres:GROUP10group10@aws-0-eu-central-1.pooler.supabase.com:6543/postgres')

# Verwijder de alembic_version tabel
with engine.connect() as connection:
    connection.execute("DROP TABLE IF EXISTS alembic_version;")

print("alembic_version tabel verwijderd!")
