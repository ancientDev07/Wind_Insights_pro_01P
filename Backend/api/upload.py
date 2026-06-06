from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File

from sqlalchemy.orm import Session
from core.database import get_db

from schemas.uploaded_file import (UploadedFileResponse)
from services.upload_service import (UploadService)

router = APIRouter()

upload_service = UploadService(upload_directory=Path("uploads"))


@router.post("/upload",response_model=UploadedFileResponse)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await upload_service.save_file(db=db,uploaded_file=file)