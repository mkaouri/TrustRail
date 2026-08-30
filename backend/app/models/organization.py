import uuid
from enum import StrEnum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class OrganizationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    # Stored as VARCHAR + CHECK constraint (native_enum=False) for clean migrations.
    status: Mapped[OrganizationStatus] = mapped_column(
        SAEnum(OrganizationStatus, native_enum=False, length=20, name="organization_status"),
        nullable=False,
        default=OrganizationStatus.ACTIVE,
    )
