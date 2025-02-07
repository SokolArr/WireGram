from sqlalchemy import text, ForeignKey, func
from sqlalchemy.types import Uuid
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime

from .base import BaseStruct
from ..settings import DBSettings

dbs = DBSettings()


class UserStruct(BaseStruct):
    # Prefs
    __tablename__ = "user"
    __table_args__ = BaseStruct.default_table_args

    # Fields
    user_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_tg_id: Mapped[int] = mapped_column(nullable=False, unique=True)
    user_name: Mapped[str] = mapped_column(
        server_default=text("'NO_USER_NAME'")
    )
    user_tag: Mapped[str] = mapped_column(server_default=text("'NO_USER_TAG'"))
    admin_flg: Mapped[bool] = mapped_column(nullable=False, default=False)
    lang_code: Mapped[str] = mapped_column(
        nullable=False, server_default=text("'RU'")
    )


class UserAccReqStruct(BaseStruct):
    # Prefs
    __tablename__ = "user_access_request"
    __table_args__ = BaseStruct.default_table_args

    # Fields
    request_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey(f"{dbs.DEFAULT_SCHEMA_NAME}.user.user_id")
    )
    access_name: Mapped[str] = mapped_column(primary_key=True)


class UserAccStruct(BaseStruct):
    # Prefs
    __tablename__ = "user_access"
    __table_args__ = BaseStruct.default_table_args

    # Fields
    access_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey(f"{dbs.DEFAULT_SCHEMA_NAME}.user.user_id")
    )
    access_name: Mapped[str] = mapped_column(primary_key=True)
    valid_from_dttm: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )
    valid_to_dttm: Mapped[datetime] = mapped_column(nullable=False)
