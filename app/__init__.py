from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Maak één instantie van SQLAlchemy aan
db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    
    # Laad de configuratie
    app.config.from_object('app.config.Config')
    
    # Initialiseer de extensies met de app
    db.init_app(app)
    migrate.init_app(app, db)

    # Registreer de blueprints
    from .routes import main
    app.register_blueprint(main)

    # Stel de geheime sleutel in (gebruik een veilige waarde in productie)
    app.secret_key = 'SECRET_KEY'

    # Controleer en maak de tabellen aan indien ze niet bestaan
    with app.app_context():
        db.create_all()  # Hiermee worden alle ontbrekende tabellen aangemaakt

    return app
