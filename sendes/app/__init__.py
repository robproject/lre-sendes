from flask import Flask
from config import Config
from app.extensions import db, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from app.main import bp
        app.register_blueprint(bp)

        from app.services import dbService
        dbService.start()

    return app
