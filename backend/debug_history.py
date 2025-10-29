"""Debug script to mimic analysis history endpoint."""

from app.core.database import SessionLocal
from app.models.users import User
from app.models.analysis import DirectAnalysis
from app.models.file_batch import BatchFile, FileBatch, FileStatus
from app.models.github_integration import PRAnalysis, GitHubRepository


def main(user_id: int) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).get(user_id)
        print("user", user)
        direct_query = db.query(DirectAnalysis).filter(DirectAnalysis.user_id == user.id)
        direct = direct_query.order_by(DirectAnalysis.created_at.desc()).all()
        repo_query = db.query(PRAnalysis).join(
            GitHubRepository, PRAnalysis.repository_id == GitHubRepository.id
        ).filter(GitHubRepository.user_id == user.id)
        repo = repo_query.order_by(PRAnalysis.created_at.desc()).all()
        batch_query = db.query(BatchFile).join(
            FileBatch, BatchFile.batch_id == FileBatch.id
        ).filter(
            FileBatch.user_id == user.id,
            BatchFile.status == FileStatus.COMPLETED,
        )
        batch = batch_query.order_by(BatchFile.completed_at.desc()).all()
        print("counts", len(direct), len(repo), len(batch))
        for analysis in repo:
            print("repo analysis id", analysis.id)
            print("analysis_results", analysis.analysis_results)
    finally:
        db.close()


if __name__ == "__main__":
    main(2)