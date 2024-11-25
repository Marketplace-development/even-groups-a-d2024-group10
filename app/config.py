from dotenv import load_dotenv
import os

# Laad omgevingsvariabelen uit .env bestand
load_dotenv()

class Config:
    # Geheime sleutel
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY moet worden ingesteld in .env bestand!")

    # Database URI
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL moet worden ingesteld in .env bestand!")

    # Schakel database wijzigingen tracken uit
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Supabase instellingen
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    # Debug mode (optioneel)
    DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 't']
