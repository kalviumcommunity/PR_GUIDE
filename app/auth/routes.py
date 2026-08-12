import secrets

from flask import Blueprint, current_app, jsonify, redirect, request, session

from app.crypto import encrypt_token
from app.extensions import db
from app.models import User
from app.auth.decorators import login_required
from app.auth.github_client import (
    GitHubAPIError,
    build_authorize_url,
    exchange_code_for_token,
    fetch_github_user,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/github/login")
def github_login():
    """Step 1: send the browser to GitHub's consent screen.

    We generate a random `state` value and stash it in the session so the
    callback can verify the response actually came from the redirect we
    issued (CSRF protection for the OAuth flow).
    """
    state = secrets.token_urlsafe(24)
    session["oauth_state"] = state
    return redirect(build_authorize_url(state))


@auth_bp.route("/github/callback")
def github_callback():
    """Step 2: GitHub redirects here with `code` + `state`."""
    error = request.args.get("error")
    if error:
        return redirect(f"{current_app.config['FRONTEND_URL']}/login?error={error}")

    state = request.args.get("state")
    expected_state = session.pop("oauth_state", None)
    if not state or not expected_state or state != expected_state:
        return jsonify({"error": "invalid OAuth state"}), 400

    code = request.args.get("code")
    if not code:
        return jsonify({"error": "missing code"}), 400

    try:
        access_token = exchange_code_for_token(code)
        github_profile = fetch_github_user(access_token)
    except GitHubAPIError as exc:
        return jsonify({"error": str(exc)}), 502

    user = User.query.filter_by(github_id=github_profile["id"]).first()
    if user is None:
        user = User(
            github_id=github_profile["id"],
            username=github_profile["login"],
            avatar_url=github_profile.get("avatar_url"),
            github_access_token=encrypt_token(access_token),
        )
        db.session.add(user)
    else:
        user.username = github_profile["login"]
        user.avatar_url = github_profile.get("avatar_url")
        user.github_access_token = encrypt_token(access_token)

    db.session.commit()

    session.clear()
    session["user_id"] = user.id

    return redirect(f"{current_app.config['FRONTEND_URL']}/dashboard")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@auth_bp.route("/me")
@login_required
def me(current_user):
    return jsonify(current_user.to_public_dict())
