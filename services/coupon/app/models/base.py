from datetime import datetime

from sqlalchemy import DateTime, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    type_annotation_map = {datetime: DateTime(timezone=True), str: Text}
