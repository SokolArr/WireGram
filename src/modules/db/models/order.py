from sqlalchemy import ForeignKey
from sqlalchemy.types import Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from enum import Enum

from .base import BaseStruct
from ..settings import DBSettings

dbs = DBSettings()


class OrderStatus(Enum):
    NEW = "NEW"
    PAYED = "PAYED"
    CLOSED = "CLOSED"


class OrderStruct(BaseStruct):
    # Prefs
    __tablename__ = "user_order"
    __table_args__ = BaseStruct.default_table_args

    # Fields
    order_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    order_status: Mapped[str] = mapped_column(nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey(f"{dbs.DEFAULT_SCHEMA_NAME}.user.user_id")
    )
    service_config_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(
            f"{dbs.DEFAULT_SCHEMA_NAME}.user_service_config.service_config_id"
        ),
    )
    order_data: Mapped[dict] = mapped_column(JSON, nullable=False)
