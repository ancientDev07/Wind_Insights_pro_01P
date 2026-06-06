from pathlib import Path
from sqlalchemy.orm import Session
from models.uploaded_file import UploadedFile

class UploadService:

    def __init__(self, upload_directory: Path):

        self.upload_directory = upload_directory

        self.upload_directory.mkdir(
            parents=True,
            exist_ok=True
        )

    async def save_file(self,db: Session,uploaded_file):

        filepath = (self.upload_directory/ uploaded_file.filename)

        content = await uploaded_file.read()

        with open(filepath,"wb") as file:

            file.write(content)

        db_file = UploadedFile(
            filename=uploaded_file.filename,
            filepath=str(filepath))

        db.add(db_file)

        db.commit()

        db.refresh(db_file)

        return db_file