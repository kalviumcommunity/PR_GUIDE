from flask import Flask, jsonify
from flask_cors import CORS

from app.config import Config
from app.extensions import db, migrate


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    # Allow the React frontend (running on a different origin) to send the
    # session cookie along with requests.
    CORS(app, supports_credentials=True, origins=[app.config["FRONTEND_URL"]])

    from app.auth.routes import auth_bp
    from app.repos.routes import repos_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(repos_bp)

    from app import models  # noqa: F401  (ensures models are registered with SQLAlchemy)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    return app
