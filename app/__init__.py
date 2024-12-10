from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Maak één instantie van SQLAlchemy en LoginManager aan
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # Laad de configuratie
    app.config.from_object('app.config.Config')

    # Initialiseer de extensies met de app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)  # Voeg LoginManager toe

    # Stel de login_view in zonder models te importeren
    login_manager.login_view = 'main.login'

    # Registreer de blueprints
    from .routes import main
    app.register_blueprint(main)

    # Registreer de chat blueprint
    from .chat import chat
    app.register_blueprint(chat, url_prefix='/chat')

    # Stel de geheime sleutel in (gebruik een veilige waarde in productie)
    app.secret_key = 'SECRET_KEY'

    return app
