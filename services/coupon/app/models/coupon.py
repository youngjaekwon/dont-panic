from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

SEQ_UNIQUE = "uq_coupons_campaign_id_seq"


class Coupon(Base):
    __tablename__ = "coupons"
    __table_args__ = (
        UniqueConstraint("campaign_id", "seq", name=SEQ_UNIQUE),
        CheckConstraint("seq > 0", name="seq_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("campaigns.id"))
    seq: Mapped[int]
    code: Mapped[str] = mapped_column(unique=True)
    issued_at: Mapped[datetime] = mapped_column(server_default=func.now())
