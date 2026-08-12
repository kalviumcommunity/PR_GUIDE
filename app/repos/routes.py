from datetime import datetime

from flask import Blueprint, jsonify, request

from app.crypto import decrypt_token
from app.extensions import db
from app.models import Repository
from app.auth.decorators import login_required
from app.auth.github_client import GitHubAPIError, fetch_github_repo

repos_bp = Blueprint("repos", __name__, url_prefix="/api/repos")


@repos_bp.route("", methods=["GET"])
@login_required
def list_repos(current_user):
    repos = Repository.query.filter_by(added_by_user_id=current_user.id).order_by(
        Repository.full_name
    )
    return jsonify([r.to_dict() for r in repos])


@repos_bp.route("/sync", methods=["POST"])
@login_required
def sync_repo(current_user):
    """Add (or refresh) a repository by owner/name, e.g. {"owner": "facebook", "name": "react"}."""
    body = request.get_json(silent=True) or {}
    owner = (body.get("owner") or "").strip()
    name = (body.get("name") or "").strip()
    if not owner or not name:
        return jsonify({"error": "owner and name are required"}), 400

    access_token = decrypt_token(current_user.github_access_token)

    try:
        gh_repo = fetch_github_repo(owner, name, access_token)
    except GitHubAPIError as exc:
        status = exc.status_code if exc.status_code and exc.status_code < 500 else 502
        return jsonify({"error": str(exc)}), status

    repo = Repository.query.filter_by(github_id=gh_repo["id"]).first()
    if repo is None:
        repo = Repository(github_id=gh_repo["id"], added_by_user_id=current_user.id)
        db.session.add(repo)

    repo.owner = gh_repo["owner"]["login"]
    repo.name = gh_repo["name"]
    repo.full_name = gh_repo["full_name"]
    repo.description = gh_repo.get("description")
    repo.stars = gh_repo.get("stargazers_count", 0)
    repo.forks = gh_repo.get("forks_count", 0)
    repo.github_created_at = _parse_github_datetime(gh_repo.get("created_at"))
    repo.synced_at = datetime.utcnow()

    db.session.commit()

    return jsonify(repo.to_dict()), 200


def _parse_github_datetime(value: str | None):
    if not value:
        return None
    # GitHub returns ISO 8601 with a trailing "Z"
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
