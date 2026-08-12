"""Extension instances, created here (not in __init__.py) so models and
blueprints can import `db` without triggering circular imports.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
