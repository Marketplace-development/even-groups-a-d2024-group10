from dotenv import load_dotenv
import os

# Laad omgevingsvariabelen uit .env bestand
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))  # Laadt sleutel uit .env of genereert een tijdelijke
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')  # Haalt de URI uit .env
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Vermijd onnodige waarschuwingen

    # Voeg hier de Supabase instellingen toe
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
