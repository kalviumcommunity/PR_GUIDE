"""All direct HTTP calls to GitHub live here, kept separate from the Flask
routes so the OAuth/API logic can be unit tested (and reused) without
spinning up a request context.
"""
import requests
from flask import current_app


class GitHubAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def build_authorize_url(state: str) -> str:
    cfg = current_app.config
    params = {
        "client_id": cfg["GITHUB_CLIENT_ID"],
        "redirect_uri": cfg["GITHUB_OAUTH_REDIRECT_URI"],
        "scope": cfg["GITHUB_OAUTH_SCOPES"],
        "state": state,
        "allow_signup": "true",
    }
    query = "&".join(f"{k}={requests.utils.quote(v)}" for k, v in params.items())
    return f"{cfg['GITHUB_AUTHORIZE_URL']}?{query}"


def exchange_code_for_token(code: str) -> str:
    """Exchange the OAuth `code` for an access token. Raises GitHubAPIError
    on any failure (bad code, revoked app, network error, etc.)."""
    cfg = current_app.config
    try:
        resp = requests.post(
            cfg["GITHUB_TOKEN_URL"],
            headers={"Accept": "application/json"},
            data={
                "client_id": cfg["GITHUB_CLIENT_ID"],
                "client_secret": cfg["GITHUB_CLIENT_SECRET"],
                "code": code,
                "redirect_uri": cfg["GITHUB_OAUTH_REDIRECT_URI"],
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        raise GitHubAPIError(f"Could not reach GitHub: {exc}") from exc

    payload = resp.json() if resp.content else {}
    if resp.status_code != 200 or "access_token" not in payload:
        raise GitHubAPIError(
            payload.get("error_description", "GitHub token exchange failed"),
            status_code=resp.status_code,
        )
    return payload["access_token"]


def fetch_github_user(access_token: str) -> dict:
    return _get("/user", access_token)


def fetch_github_repo(owner: str, name: str, access_token: str) -> dict:
    return _get(f"/repos/{owner}/{name}", access_token)


def _get(path: str, access_token: str) -> dict:
    cfg = current_app.config
    try:
        resp = requests.get(
            f"{cfg['GITHUB_API_BASE']}{path}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        raise GitHubAPIError(f"Could not reach GitHub: {exc}") from exc

    if resp.status_code == 404:
        raise GitHubAPIError("Not found on GitHub", status_code=404)
    if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
        raise GitHubAPIError("GitHub rate limit exceeded, try again later", status_code=429)
    if resp.status_code != 200:
        raise GitHubAPIError(f"GitHub API error: {resp.text}", status_code=resp.status_code)

    return resp.json()
