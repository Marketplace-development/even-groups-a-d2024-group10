from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.helpers import utc_to_plus_one, format_datetime


db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    
    app.config.from_object('app.config.Config')

    
    app.jinja_env.filters['utc_to_plus_one'] = utc_to_plus_one
    app.jinja_env.filters['strftime'] = format_datetime
    
    db.init_app(app)
    migrate.init_app(app, db)

    
    from .routes import main  
    from .chat import chat   
    app.register_blueprint(main)
    app.register_blueprint(chat, url_prefix='/chat')  

    
    app.secret_key = 'SECRET_KEY'

    
    with app.app_context():
        db.create_all()  

    return app



