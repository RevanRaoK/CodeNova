from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.schemas import repository as repo_schema
from app.services.repository_services import repository_service

router=APIRouter()

@router.post("/", response_model=repo_schema.RepositoryRead, status_code=201)
def create_repository(*, repo_in: repo_schema.RepositoryCreate, db: Session = Depends(get_db)):
  return repository_service.create_repository(db=db, repo_in=repo_in)

@router.get("/{repo_id}", response_model=repo_schema.RepositoryRead)
def get_repository(repo_id: int = Path(gt=0), db: Session = Depends(get_db)):
  db_repo = repository_service.get_repository(db=db, repo_id=repo_id)
  if not db_repo:
    raise HTTPException(status_code=404, detail="Repository not found")
  return db_repo

@router.get("/", response_model=List[repo_schema.RepositoryRead])
def list_repositories(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db)
):
  return repository_service.list_repositories(db=db, skip=skip, limit=limit)

@router.patch("/{repo_id}", response_model=repo_schema.RepositoryRead)
def update_repository(
    repo_id: int = Path(gt=0),
    repo_update: repo_schema.RepositoryUpdate = None,
    db: Session = Depends(get_db)
):
  db_repo = repository_service.get_repository(db=db, repo_id=repo_id)
  if not db_repo:
    raise HTTPException(status_code=404, detail="Repository not found")
  updated = repository_service.update_repository(db=db, repo=db_repo, repo_update=repo_update)
  return updated

@router.delete("/{repo_id}", status_code=204)
def delete_repository(repo_id: int = Path(gt=0), db: Session = Depends(get_db)):
  ok = repository_service.delete_repository(db=db, repo_id=repo_id)
  if not ok:
    raise HTTPException(status_code=404, detail="Repository not found")
  return None