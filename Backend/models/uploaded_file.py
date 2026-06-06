from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from models.base import Base

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    filename: Mapped[str] = mapped_column(String(255))

    filepath: Mapped[str] = mapped_column(String(500))