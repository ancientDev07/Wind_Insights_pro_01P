from datetime import datetime, timezone
from sqlalchemy import String,DateTime, ForeignKey
from sqlalchemy.orm import Mapped,mapped_column, relationship

from models.base import Base

class Dataset(Base):

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))

    version: Mapped[str] = mapped_column(String(50), default="DT001")

    status: Mapped[str] = mapped_column(String(50), default="active")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),nullable=False )

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc),nullable=False)

    project = relationship("Project", back_populates="datasets")
    assets = relationship("Asset", back_populates="dataset")