from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from core.database import get_db
from schemas.project import (ProjectCreate, ProjectResponse)
from services.project_service import ( ProjectService)

router = APIRouter()

service = ProjectService()


@router.post("/projects", response_model=ProjectResponse)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    return service.create_project(db,payload)


@router.get("/projects", response_model=list[ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    return service.get_projects(db)