from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.helpers import utc_to_plus_one, format_datetime

# Maak één instantie van SQLAlchemy en Migrate aan
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Laad de configuratie
    app.config.from_object('app.config.Config')

    # Register het filter
    app.jinja_env.filters['utc_to_plus_one'] = utc_to_plus_one
    app.jinja_env.filters['strftime'] = format_datetime
    # Initialiseer de extensies met de app
    db.init_app(app)
    migrate.init_app(app, db)

    # Registreer de blueprints
    from .routes import main  # Importeer de routes-Blueprint
    from .chat import chat   # Zorg dat chat expliciet wordt geïmporteerd
    app.register_blueprint(main)
    app.register_blueprint(chat, url_prefix='/chat')  # Registreer de chat-Blueprint

    # Stel de geheime sleutel in (gebruik een veilige waarde in productie)
    app.secret_key = 'SECRET_KEY'

    # Controleer en maak de tabellen aan indien ze niet bestaan
    with app.app_context():
        db.create_all()  # Hiermee worden alle ontbrekende tabellen aangemaakt

    return app



