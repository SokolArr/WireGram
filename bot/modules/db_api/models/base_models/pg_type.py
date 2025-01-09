from uuid import UUID
from datetime import date, datetime

class BasePgType:
    def __init__(self, pg_type: str, py_type: type):
        self.pg_type = pg_type
        self.py_type = py_type
        
    def sql_definition(self, is_primary_key=False, is_not_null=False, default_value=None):
        definition = f"{self.pg_type}"
        if is_not_null:
            definition += " NOT NULL"
        if default_value is not None:
            definition += f" DEFAULT {default_value}"
        if is_primary_key:
            definition += " PRIMARY KEY"
        return definition

class UuidPgType(BasePgType):
    def __init__(self):
        super().__init__('uuid', UUID)

class IntegerPgType(BasePgType):
    def __init__(self):
        super().__init__('integer', int)

class TextPgType(BasePgType):
    def __init__(self):
        super().__init__('text', str)

class BooleanPgType(BasePgType):
    def __init__(self):
        super().__init__('boolean', bool)

class DatePgType(BasePgType):
    def __init__(self):
        super().__init__('date', date)

class TimestampPgType(BasePgType):
    def __init__(self):
        super().__init__('timestamp', datetime)