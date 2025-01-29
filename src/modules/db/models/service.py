from sqlalchemy import ForeignKey, func, null, text
from sqlalchemy.types import Uuid, ARRAY, JSON, TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID
from datetime import datetime

from .base import BaseStruct
from ..settings import DBSettings

dbs = DBSettings()
    
class UserServConfStruct(BaseStruct):
    # Prefs
    __tablename__       = 'user_service_config'
    __table_args__      = BaseStruct.default_table_args

    # Fields
    service_config_id:  Mapped[UUID] =  mapped_column(Uuid, primary_key=True) 
    user_id:            Mapped[UUID] =  mapped_column(Uuid, ForeignKey(f"{dbs.DEFAULT_SCHEMA_NAME}.user.user_id"))
    config_name:        Mapped[str] =   mapped_column(nullable=False)
    config_price:       Mapped[float] = mapped_column(nullable=False)
    max_config_traffic: Mapped[float] = mapped_column(nullable=False)
    user_service_id:    Mapped[UUID] =  mapped_column(Uuid)
    cached_data:        Mapped[dict] =  mapped_column(JSON, nullable=True)
    valid_from_dttm:    Mapped[datetime] = mapped_column(nullable=False, server_default=func.current_timestamp())
    valid_to_dttm:      Mapped[datetime] = mapped_column(nullable=False)
    
    orders = relationship('OrderStruct', backref='UserServConfStruct', cascade='all, delete')