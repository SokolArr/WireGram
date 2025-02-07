from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

from ..settings import DBSettings


class Base(DeclarativeBase):
    # Base repr:
    repr_cols_num = 10
    repr_cols = tuple()

    def __repr__(self):
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")
        return f"<{self.__class__.__name__} {', '.join(cols)}>"

    pass


class BaseStruct(Base):
    __abstract__ = True

    # Default params:
    write_logs_flg = DBSettings().WRITE_LOGS_FLG
    default_table_args = {"schema": DBSettings().DEFAULT_SCHEMA_NAME}

    # Fields:
    sys_inserted_dttm: Mapped[datetime] = mapped_column(
        server_default=func.current_timestamp()
    )
    sys_updated_dttm: Mapped[datetime] = mapped_column(
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
