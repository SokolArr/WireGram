from sqlalchemy import Table, Integer, Text, Boolean, TIMESTAMP, func, text, types, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import MetaData
from datetime import datetime, timezone
import uuid

from .db_instance import Base, MAIN_SCHEMA_NAME, WRITE_LOGS

class BaseObj():
    __abstract__ = True
    WRITE_LOGS   = WRITE_LOGS
    
    sys_processed_by:   Mapped[str]      = mapped_column(server_default=text("'INS_DB_API'"), 
                                                         onupdate=text("'UPD_DB_API_" + datetime.now(timezone.utc).strftime('%Y-%m-%d_%H:%M:%S')+"'"))
    sys_processed_dttm: Mapped[datetime] = mapped_column(server_default=func.current_timestamp(), onupdate=func.current_timestamp())

class UserStruct(Base, BaseObj):
    __tablename__       = 'user'
    __table_args__      = {'schema': MAIN_SCHEMA_NAME}
    
    user_id:        Mapped[uuid.UUID]  = mapped_column(types.Uuid)
    user_tg_code:   Mapped[str]   = mapped_column(primary_key=True)
    user_name:      Mapped[str]   = mapped_column(server_default=text("'NO_USER_NAME'"))
    user_tag:       Mapped[str]   = mapped_column(server_default=text("'NO_USER_TAG'"))
    admin_flg:      Mapped[bool]  = mapped_column(default=False)
    
    
class UserAccessStruct(Base, BaseObj):
    __tablename__       = 'user_access'
    __table_args__      = {'schema': MAIN_SCHEMA_NAME}
    
    user_id:            Mapped[uuid.UUID]  = mapped_column(types.Uuid, primary_key=True)
    access_name:        Mapped[str]    = mapped_column(primary_key=True)
    access_from_dttm:   Mapped[datetime]    = mapped_column()
    access_to_dttm:     Mapped[datetime]   = mapped_column()

class UserReqAccessStruct(Base, BaseObj):
    __tablename__       = 'user_req_access'
    __table_args__      = {'schema': MAIN_SCHEMA_NAME}
    
    user_id:            Mapped[uuid.UUID]  = mapped_column(types.Uuid, primary_key=True)
    req_access_name:    Mapped[str]        = mapped_column(primary_key=True)

class UserOrderStruct(Base, BaseObj):
    __tablename__       = 'user_order'
    __table_args__      = {'schema': MAIN_SCHEMA_NAME}
    
    order_id:        Mapped[uuid.UUID]  = mapped_column(types.Uuid, primary_key=True)
    order_status:    Mapped[str]        = mapped_column(primary_key=True)
    user_id:         Mapped[uuid.UUID]  = mapped_column(types.Uuid)
    order_payload:   Mapped[str]        = mapped_column()
