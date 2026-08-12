from datetime import datetime, timezone

from app.extensions import db


class Repository(db.Model):
    """A GitHub repository a maintainer has added to OpenPulse for tracking.

    Populated from GitHub's `GET /repos/{owner}/{repo}` on sync. Contributor,
    PR, issue, review, and commit data are separate tables that get built out
    as we implement the data-collection feature — this table only holds
    repo-level metadata for now.
    """

    __tablename__ = "repositories"
    __table_args__ = (
        db.UniqueConstraint("owner", "name", name="uq_repositories_owner_name"),
    )

    id = db.Column(db.Integer, primary_key=True)

    github_id = db.Column(db.BigInteger, unique=True, nullable=False, index=True)
    owner = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(511), nullable=False)
    description = db.Column(db.Text)

    stars = db.Column(db.Integer, default=0)
    forks = db.Column(db.Integer, default=0)
    github_created_at = db.Column(db.DateTime)

    added_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    added_by = db.relationship("User", back_populates="repositories")

    synced_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "github_id": self.github_id,
            "owner": self.owner,
            "name": self.name,
            "full_name": self.full_name,
            "description": self.description,
            "stars": self.stars,
            "forks": self.forks,
            "github_created_at": self.github_created_at.isoformat()
            if self.github_created_at
            else None,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
        }

    def __repr__(self) -> str:
        return f"<Repository {self.full_name}>"
