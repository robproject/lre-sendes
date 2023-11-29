from flask import Flask
from config import Config
from app.extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    from app.main import bp

    app.register_blueprint(bp)



    with app.app_context():
        db.create_all()
        from app.services import dbService
        dbService.start()
    return app
