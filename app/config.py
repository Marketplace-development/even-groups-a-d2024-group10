from dotenv import load_dotenv
import os


load_dotenv()

class Config:
    
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY moet worden ingesteld in .env bestand!")

    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL moet worden ingesteld in .env bestand!")

    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    
    DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 't']
