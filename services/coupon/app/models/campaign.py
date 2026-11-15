from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"
    __table_args__ = (CheckConstraint("total_quantity > 0", name="total_quantity_positive"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str]
    total_quantity: Mapped[int]
    starts_at: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
