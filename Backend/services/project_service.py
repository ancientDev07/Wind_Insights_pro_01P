from sqlalchemy.orm import Session
from models.project import Project
from schemas.project import ProjectCreate

class ProjectService:

    def create_project(self, db: Session,payload: ProjectCreate) -> Project:
        project = Project(name=payload.name,description=payload.description)
        
        db.add(project)
        db.commit()
        db.refresh(project)

        return project

    def get_projects(self, db: Session) -> list[Project]:
        return (db.query(Project).order_by(Project.updated_at.desc()).all())

    def get_project_by_id(self, db: Session,project_id: int) -> Project | None:
        return (db.query(Project).filter(Project.id == project_id).first())

    def delete_project(self, db: Session, project_id: int) -> bool:
        project = (db.query(Project).filter(Project.id == project_id).first())

        if not project:
            return False

        db.delete(project)

        db.commit()

        return True