from functools import wraps

from flask import session, jsonify

from app.models import User


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "authentication required"}), 401

        user = User.query.get(user_id)
        if not user:
            session.clear()
            return jsonify({"error": "authentication required"}), 401

        return view(user, *args, **kwargs)

    return wrapped
