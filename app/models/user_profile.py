from uuid import UUID as PyUUID
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.user import Base

class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Ensure this matches the ID type in your User model (usually UUID)
    user_id: Mapped[PyUUID] = mapped_column(ForeignKey("user.id"), unique=True)
    headline: Mapped[str | None] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(String(1000))
    skills: Mapped[str | None] = mapped_column(String(1000))
    # Relationships
    # Note: "user" must be defined in your User model for back_populates to work
    interviews: Mapped[list["MockInterview"]] = relationship(
        "MockInterview", back_populates="profile"
    )