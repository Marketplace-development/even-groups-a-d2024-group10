from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialiseer extensies
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Laad configuratie
    app.config.from_object('app.config.Config')
    
    # Initialiseer extensies
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Registreer de blueprint voor de routes
    from .routes import main  # Zorg dat 'main' in routes correct is gedefinieerd
    app.register_blueprint(main)

    # Stel een geheim sleutel in voor sessiebeheer
    app.secret_key = '1bc29dd9e466f92dccd7382212eaaaba8f79a81929ba83bb'  # random string

    return app
