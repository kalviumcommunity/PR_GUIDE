from datetime import datetime, timezone

from app.extensions import db


class User(db.Model):
    """A maintainer who has logged into OpenPulse via GitHub OAuth.

    This is the *app* user (the person using the dashboard) — not to be
    confused with a `Contributor` (a person who opened a PR/issue on a
    tracked repo), which we'll add when we build repo data sync.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    github_id = db.Column(db.BigInteger, unique=True, nullable=False, index=True)
    username = db.Column(db.String(255), nullable=False)
    avatar_url = db.Column(db.String(512))

    # Encrypted at rest — see app/crypto.py. Never serialize this field.
    github_access_token = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    repositories = db.relationship(
        "Repository", back_populates="added_by", cascade="all, delete-orphan"
    )

    def to_public_dict(self) -> dict:
        """Serialization safe to send to the client — no tokens, ever."""
        return {
            "id": self.id,
            "github_id": self.github_id,
            "username": self.username,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.username}>"
