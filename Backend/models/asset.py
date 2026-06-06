from datetime import datetime, timezone
from sqlalchemy import DateTime,ForeignKey,String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Asset(Base):

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)

    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))

    asset_category: Mapped[str] = mapped_column(String(100))

    asset_subtype: Mapped[str] = mapped_column(String(100))

    asset_name: Mapped[str] = mapped_column(String(255))

    storage_type: Mapped[str] = mapped_column(String(50),default="database")

    table_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc), nullable=False)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    dataset = relationship("Dataset", back_populates="assets")