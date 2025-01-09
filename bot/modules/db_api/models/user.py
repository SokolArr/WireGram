import logging

from modules.db_api.models.base_models.pg_table import BasePgTable
from modules.db_api.models.base_models.pg_type import UuidPgType, TextPgType, BooleanPgType, TimestampPgType

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class UserPgTable(BasePgTable):
    '''
    Args struct:
        (attr, BasePgType, is_primary_key, is_not_null, default_value)
    
    Returns:
        CREATE TABLE IF NOT EXISTS main."user" (
            user_id uuid NOT NULL PRIMARY KEY,
            user_name text DEFAULT 'NO_USER_NAME',
            user_tg_code text NOT NULL,
            admin_flg boolean DEFAULT false,
            sys_inserted_process text NOT NULL DEFAULT 'MANUAL',
            sys_inserted_dttm timestamp NOT NULL DEFAULT current_timestamp
        );
    '''
    __columns = [
        ("user_id", UuidPgType(), False, True),
        ("user_name", TextPgType(), False, False, "'NO_USER_NAME'"),
        ("user_tg_code", TextPgType(), False, True),
        ("admin_flg", BooleanPgType(), False, False, "false"),
    ]
    __tech_columns = [
        ("sys_inserted_process", TextPgType(), False, True, "'MANUAL'"),
        ("sys_inserted_dttm", TimestampPgType(), False, True, "current_timestamp"),
    ]
    __constraints = [
        {
            'name': 'user_pk',
            'type': 'PRIMARY KEY',
            'columns': ['user_id', 'user_tg_code']
        }
    ]
    
    def __init__(self, schema_name: str = BasePgTable.DEFAULT_SCHEMA_NAME, table_name: str = 'user'):
        super().__init__(schema_name=schema_name, 
                        table_name=table_name,
                        columns=self.__columns, 
                        tech_columns=self.__tech_columns,
                        constraints=self.__constraints)