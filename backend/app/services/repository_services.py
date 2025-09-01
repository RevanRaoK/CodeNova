from sqlalchemy.orm import Session
from app.db import models
from app.schemas import repository as repo_schema

class RepositoryService:
    def get_repository(self, db:Session, repo_id: int):
        return db.query(models.Repository).filter(models.Repository.id==repo_id).first()

    def create_repository(self, db: Session, repo_in: repo_schema.RepositoryCreate):
        db_repo=models.Repository(
            name=repo_in.name,
            url=str(repo_in.url),
            description=repo_in.description,
            user_id=repo_in.user_id
        )
        db.add(db_repo)
        db.commit()
        db.refresh(db_repo)
        return db_repo
        
    def list_repositories(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Repository).offset(skip).limit(limit).all()

    def update_repository(self, db: Session, repo: models.Repository, repo_update: repo_schema.RepositoryUpdate):
        if repo_update.description is not None:
            repo.description = repo_update.description
        db.add(repo)
        db.commit()
        db.refresh(repo)
        return repo

    def delete_repository(self, db: Session, repo_id: int) -> bool:
        repo = self.get_repository(db, repo_id)
        if not repo:
            return False
        db.delete(repo)
        db.commit()
        return True
        
repository_service=RepositoryService()
