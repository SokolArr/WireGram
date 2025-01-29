import uuid
import logging
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy import select, insert, update, delete, and_, or_, text, cast, String
from sqlalchemy.orm import aliased
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import JSONB

from .settings import DBSettings
from .models import Base, BaseStruct
from .models import UserStruct, UserAccReqStruct, UserAccStruct
from .models import UserServConfStruct
from .models import OrderStruct

logger = logging.getLogger(__name__)
dbs = DBSettings()
model_log_list = [UserStruct, UserAccReqStruct, UserAccStruct,
                  UserServConfStruct,
                  OrderStruct]   

def now_dttm():
    return datetime.now()

class ReturnCode(Enum):
    SUCCESS                 = 0
    UNIQUE_VIOLATION        = -1
    FOREIGN_KEY_VIOLATION   = -2
    NOT_FOUND               = -3
    NO_ROWS_INSERTED        = -4
    DATABASE_ERROR          = -99

class DBErrorHandler:
    @staticmethod
    def handle_exception(e: Exception) -> ReturnCode:
        logger.error(f"ERROR: {e}")
        if isinstance(e, IntegrityError):
            err_message = ''
            if e.orig:
                err_message = str(e.orig.args[0])
                if 'UniqueViolationError' in err_message:
                    logger.error(f"UniqueViolationError: {err_message}")
                    return ReturnCode.UNIQUE_VIOLATION
                
                elif 'ForeignKeyViolationError' in err_message:
                    logger.error(f"ForeignKeyViolationError: {err_message}")
                    return ReturnCode.FOREIGN_KEY_VIOLATION
                
                else:
                    logger.error(f"DB ERROR: {err_message}")
                    return ReturnCode.DATABASE_ERROR
        else:
            return ReturnCode.DATABASE_ERROR
          
    def ins_row_cnt_handler(row_count) -> ReturnCode:
        if row_count > 0:
            logger.debug(ReturnCode.SUCCESS)
            return ReturnCode.SUCCESS
        else:
            logger.debug(ReturnCode.NO_ROWS_INSERTED)
            return ReturnCode.NO_ROWS_INSERTED
        
    def upd_row_cnt_handler(row_count) -> ReturnCode:
        if row_count > 0:
            logger.debug(ReturnCode.SUCCESS)
            return ReturnCode.SUCCESS
        else:
            logger.debug(ReturnCode.NOT_FOUND)
            return ReturnCode.NOT_FOUND
        
    def del_row_cnt_handler(row_count) -> ReturnCode:
        if row_count > 0:
            logger.debug(ReturnCode.SUCCESS)
            return ReturnCode.SUCCESS
        else:
            logger.debug(ReturnCode.NOT_FOUND)
            return ReturnCode.NOT_FOUND
          
class DbManager():
    '''
    CONTRACTS:
        SELECT:
            GOOD: value
            BAD:  None
        
        INSERT:
            GOOD: rows_inserted > 0 => ReturnCode.SUCCESS
            BAD:                       ReturnCode.UNIQUE_VIOLATION
            BAD:                       ReturnCode.FOREIGN_KEY_VIOLATION
            BAD:                       ReturnCode.DATABASE_ERROR
            
        UPDATE:
            GOOD: rows_updated > 0 => ReturnCode.SUCCESS
            BAD:  rows_updated = 0 => ReturnCode.NOT_FOUND
            BAD:                      ReturnCode.DATABASE_ERROR
    
        DELETE:
            GOOD: rows_deleted > 0 => ReturnCode.SUCCESS
            BAD:  rows_deleted = 0 => ReturnCode.NOT_FOUND
            BAD:                      ReturnCode.DATABASE_ERROR
    '''  
    
    # Database init:
    @staticmethod
    def check_db_available():
        try:
            with dbs.admin_session_factory() as session:
                q = (
                    text("SELECT 1")
                )
                res = session.execute(q)
                return res.scalar()
            
        except Exception as e:
            logger.error(f'\n\n!BAD TRY TO CHECK DB AVAILABLE!\n\n{e}')
    #
    @staticmethod    
    def check_existed_db():
        try:
            with dbs.admin_session_factory() as session:
                q = (
                    text(f"SELECT 1 FROM information_schema.tables WHERE table_schema = '{dbs.DEFAULT_SCHEMA_NAME}'")
                )
                res = session.execute(q)
                if res.rowcount > 0:
                    return True
                else:
                    return False
        except Exception as e:
            raise e
    #    
    @staticmethod
    def _db_init():
        try:
            with dbs.admin_session_factory() as session:
                logger.info(f'CONTINUE WITH DB ADMIN...')
                logger.info(f"WRITE LOGS: {dbs.WRITE_LOGS_FLG}")
                tz_create_sql = f"""
                    ALTER DATABASE db SET timezone TO '{dbs.DEFAULT_TIMEZONE}';
                """
                
                if dbs.WRITE_LOGS_FLG: sch_create_sql = f"""
                    DROP SCHEMA IF EXISTS {dbs.DEFAULT_SCHEMA_NAME} CASCADE;
                    CREATE SCHEMA {dbs.DEFAULT_SCHEMA_NAME};

                    DROP SCHEMA IF EXISTS {dbs.DEFAULT_SCHEMA_NAME}_logs CASCADE;
                    CREATE SCHEMA {dbs.DEFAULT_SCHEMA_NAME}_logs;
                """
                else: sch_create_sql = f"""
                    DROP SCHEMA IF EXISTS {dbs.DEFAULT_SCHEMA_NAME} CASCADE;
                    CREATE SCHEMA {dbs.DEFAULT_SCHEMA_NAME};
                """

                session.execute(text(tz_create_sql))
                session.execute(text(sch_create_sql))
                session.commit()
                
                logger.info(f"DB TIMEZONE SET TO: {dbs.DEFAULT_TIMEZONE}")
                logger.info(f"DB SCHEMA: {dbs.DEFAULT_SCHEMA_NAME}" + (f", {dbs.DEFAULT_SCHEMA_NAME}_logs" if dbs.WRITE_LOGS_FLG else "") + " SUCCESSFULLY CREATED")
                
        except Exception as e:
            logger.error(f"DB ERROR: {e}")
            return False
    #    
    @staticmethod
    def _db_add_wg_user():
        try:
            with dbs.admin_session_factory() as session:
                add_wg_user_sql = f"""
                    DROP USER IF EXISTS {dbs.WG_USER};
                    CREATE USER {dbs.WG_USER} WITH PASSWORD '{dbs.WG_PASS}';
                    
                    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {dbs.DEFAULT_SCHEMA_NAME} TO {dbs.WG_USER};
                    GRANT ALL PRIVILEGES ON SCHEMA {dbs.DEFAULT_SCHEMA_NAME} TO {dbs.WG_USER};
                    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {dbs.DEFAULT_SCHEMA_NAME} TO {dbs.WG_USER};
                    ALTER DEFAULT PRIVILEGES IN SCHEMA {dbs.DEFAULT_SCHEMA_NAME} GRANT ALL PRIVILEGES ON TABLES TO {dbs.WG_USER};
                """
                add_wg_user_sql += f"""
                    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {dbs.DEFAULT_SCHEMA_NAME}_logs TO {dbs.WG_USER};
                    GRANT ALL PRIVILEGES ON SCHEMA {dbs.DEFAULT_SCHEMA_NAME}_logs TO {dbs.WG_USER};
                    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {dbs.DEFAULT_SCHEMA_NAME}_logs TO {dbs.WG_USER};
                    ALTER DEFAULT PRIVILEGES IN SCHEMA {dbs.DEFAULT_SCHEMA_NAME}_logs GRANT ALL PRIVILEGES ON TABLES TO {dbs.WG_USER};
                """ if dbs.WRITE_LOGS_FLG else ""

                session.execute(text(add_wg_user_sql))
                session.commit()
                logger.info(f"USER: {dbs.WG_USER} SUCCESSFULLY ADDED")
                logger.info(f'CONTINUE WITH {dbs.WG_USER} USER...')
                
        except Exception as e:
            logger.error(f"DB ERROR: {e}")
            return False
    #    
    @staticmethod
    def _create_log_triggers(classes: list[Base], schema_name: str = None):
        try:
            cls: BaseStruct
            logger.info(f"TRY TO CREATE LOG-TRIGGER FOR {', '.join([f'{dbs.DEFAULT_SCHEMA_NAME}.{cls.__tablename__}' for cls in classes])}")
            for cls in classes:
                if cls.write_logs_flg:
                    with dbs.admin_session_factory() as session:
                        column_names = [column.name for column in cls.__table__.columns]
                        table_name = cls.__tablename__
                        
                        if schema_name is None:
                            schema_name = dbs.DEFAULT_SCHEMA_NAME
                            
                        create_sql = f'''
                            DROP TABLE IF EXISTS {dbs.DEFAULT_SCHEMA_NAME}_logs."{table_name}" CASCADE;
                            CREATE TABLE {dbs.DEFAULT_SCHEMA_NAME}_logs."{table_name}" 
                            AS SELECT "{table_name}".*
                            FROM {schema_name}."{table_name}";
                        '''
                        
                        alter_sql = f'''
                            ALTER TABLE {dbs.DEFAULT_SCHEMA_NAME}_logs."{table_name}"
                            ADD COLUMN log_processed_type TEXT,
                            ADD COLUMN log_processed_dttm TIMESTAMP;
                        '''
                    
                        insert_function_sql = f"""
                            CREATE OR REPLACE FUNCTION {schema_name}.log_{table_name}_insert() RETURNS TRIGGER AS $$
                            BEGIN
                                INSERT INTO {dbs.DEFAULT_SCHEMA_NAME}_logs.{table_name} ({', '.join(column_names)}, log_processed_type, log_processed_dttm)
                                VALUES ({', '.join(['NEW.' + name for name in column_names])}, 'INSERT', current_timestamp);
                                RETURN NEW;
                            END;
                            $$ LANGUAGE plpgsql;
                        """
                        insert_trigger_sql = f"""
                            CREATE TRIGGER after_{table_name}_insert
                            AFTER INSERT ON {schema_name}.{table_name}
                            FOR EACH ROW EXECUTE FUNCTION {schema_name}.log_{table_name}_insert();
                        """

                        update_function_sql = f"""
                            CREATE OR REPLACE FUNCTION {schema_name}.log_{table_name}_update() RETURNS TRIGGER AS $$
                            BEGIN
                                INSERT INTO {dbs.DEFAULT_SCHEMA_NAME}_logs.{table_name} ({', '.join(column_names)}, log_processed_type, log_processed_dttm)
                                VALUES ({', '.join(['NEW.' + name for name in column_names])}, 'UPDATE', current_timestamp);
                                RETURN NEW;
                            END;
                            $$ LANGUAGE plpgsql;
                        """
                        update_trigger_sql = f"""
                            CREATE TRIGGER after_{table_name}_update
                            AFTER UPDATE ON {schema_name}.{table_name}
                            FOR EACH ROW EXECUTE FUNCTION {schema_name}.log_{table_name}_update();
                        """

                        delete_function_sql = f"""
                            CREATE OR REPLACE FUNCTION {schema_name}.log_{table_name}_delete() RETURNS TRIGGER AS $$
                            BEGIN
                                INSERT INTO {dbs.DEFAULT_SCHEMA_NAME}_logs.{table_name} ({', '.join(column_names)}, log_processed_type, log_processed_dttm)
                                VALUES ({', '.join(['OLD.' + name for name in column_names])}, 'DELETE', current_timestamp);
                                RETURN OLD;
                            END;
                            $$ LANGUAGE plpgsql;
                        """
                        delete_trigger_sql =f"""
                            CREATE TRIGGER after_{table_name}_delete
                            AFTER DELETE ON {schema_name}.{table_name}
                            FOR EACH ROW EXECUTE FUNCTION {schema_name}.log_{table_name}_delete();
                        """   
                        
                    logger.info(f"CREATING LOG-TRIGGER FOR {schema_name}.{table_name}...")        
                    session.execute(text(create_sql))
                    session.execute(text(alter_sql))
                    
                    session.execute(text(insert_function_sql))
                    session.execute(text(insert_trigger_sql))
                    
                    session.execute(text(update_function_sql))
                    session.execute(text(update_trigger_sql))
                    
                    session.execute(text(delete_function_sql))
                    session.execute(text(delete_trigger_sql))
                    
                    session.commit()
            logger.info("ALL TRIGGERS SUCCESSFULLY CREATED!")
                
        except Exception as e:
            logger.error(f"DB ERROR: {e}")
            return False
    #    
    def create_db(self, reinit: bool = False):
        logger.info(f"v--------START_DB_INIT--------v")
        dbs.admin_sync_engine.echo = False
        def init():
            self._db_init()
            Base.metadata.drop_all(dbs.admin_sync_engine)
            Base.metadata.create_all(dbs.admin_sync_engine)
            if dbs.WRITE_LOGS_FLG: self._create_log_triggers(model_log_list)
            self._db_add_wg_user()
            dbs.admin_sync_engine.echo = True 
        if reinit:
            init()
        else:
            if self.check_existed_db():
                logger.warning(f"SCHEMA {dbs.DEFAULT_SCHEMA_NAME} ALREADY EXIST! SKIP DB INIT...")
            else:
                init()
                
        logger.info(f"^--------END_DB_INIT--------^")

    # Admins methods:
    @staticmethod
    async def get_admins() -> list[int]:
        try:
            async with dbs.async_session_factory() as session:
                q = (
                    select(UserStruct.user_tg_id)
                    .select_from(UserStruct)
                    .where(UserStruct.admin_flg == True)
                )
                res = await session.scalars(q)
                res_all = res.all()
                return res_all
        except Exception as e:
            raise e
    #
    @staticmethod
    async def upgrade_user(user_tg_id: int) -> ReturnCode:
        try:
            async with dbs.async_session_factory() as session:
                q = (
                    update(UserStruct)
                    .values(admin_flg = True)
                    .where(UserStruct.user_tg_id == user_tg_id)
                )
                res = await session.execute(q)
                await session.commit()
                return DBErrorHandler.upd_row_cnt_handler(res.rowcount)
        except Exception as e:
            return DBErrorHandler.handle_exception(e)
    #
    @staticmethod
    async def downgrade_user(user_tg_id: int) -> ReturnCode:
        try:
            async with dbs.async_session_factory() as session:
                q = (
                    update(UserStruct)
                    .values(admin_flg = False)
                    .where(UserStruct.user_tg_id == user_tg_id)
                )
                res = await session.execute(q)
                await session.commit()
                return DBErrorHandler.upd_row_cnt_handler(res.rowcount)
        except Exception as e:
            return DBErrorHandler.handle_exception(e)

    # User methods:
    @staticmethod
    async def add_user(user: UserStruct) -> ReturnCode:  
        try:
            async with dbs.async_session_factory() as session:
                new_user = user
                new_user.user_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(user.user_tg_id))
                session.add(new_user)
                await session.commit()
                return DBErrorHandler.ins_row_cnt_handler(1)
        except Exception as e:
            return DBErrorHandler.handle_exception(e) 
    #
    @staticmethod
    async def get_user(user_tg_id: int) -> UserStruct:
        try:
            async with dbs.async_session_factory() as session:
                q = (
                    select(UserStruct)
                    .where(UserStruct.user_tg_id == user_tg_id)
                )
                res = await session.scalars(q)
                res_fst = res.first()
                return res_fst
        except Exception as e:
            raise e
    
    # Access request methods:
    @staticmethod
    async def add_access_request(user_tg_id: int, access_name: str) -> ReturnCode:  
        try:
            async with dbs.async_session_factory() as session:
                q = (
                    select(UserStruct.user_id)
                    .where(UserStruct.user_tg_id == user_tg_id)
                )
                res = await session.scalars(q)
                user_id = res.first()
                access_request = UserAccReqStruct(
                    request_id = uuid.uuid5(uuid.NAMESPACE_DNS, access_name + str(user_id)),
                    access_name = access_name,
                    user_id = user_id
                )
                session.add(access_request)
                await session.commit()
                return DBErrorHandler.ins_row_cnt_handler(1)
        except Exception as e:
            return DBErrorHandler.handle_exception(e)
    #
    @staticmethod
    async def get_access_request(user_tg_id: int, access_name: str) -> UserAccReqStruct:
        try:
            async with dbs.async_session_factory() as session:
                u = aliased(UserStruct)
                ura = aliased(UserAccReqStruct)
                q = (
                    select(ura)
                    .join(u, and_(u.user_id == ura.user_id,
                                   u.user_tg_id == user_tg_id,
                                   ura.access_name == access_name))
                )
                res = await session.scalars(q)
                res_fst = res.first()
                return res_fst
        except Exception as e:
            raise e
        
    @staticmethod
    async def get_access_requests(access_name: str, limit: int = 3) -> UserAccReqStruct:
        try:
            async with dbs.async_session_factory() as session:
                q = (
                    select(UserAccReqStruct)
                    .where(UserAccReqStruct.access_name == access_name)
                    .limit(limit)
                )
                res = await session.scalars(q)
                res_fst = res.all()
                return res_fst
        except Exception as e:
            raise e
        
    # Access methods:
    @staticmethod
    async def add_access(user_tg_id: int, access_name: str, access_delta_days: int = 30) -> ReturnCode:  
        try:
            async with dbs.async_session_factory() as session:
                q = (
                    select(UserStruct.user_id)
                    .where(UserStruct.user_tg_id == user_tg_id)
                )
                res = await session.scalars(q)
                user_id = res.first()
                
                q_del_req_acc = (
                    delete(UserAccReqStruct)
                    .where(and_(UserAccReqStruct.access_name == access_name,
                                UserAccReqStruct.user_id == user_id))
                )
                res_1 = await session.execute(q_del_req_acc)
                if res_1.rowcount > 0:
                    access = UserAccStruct(
                        access_id = uuid.uuid5(uuid.NAMESPACE_DNS, access_name + str(user_id)),
                        access_name = access_name,
                        user_id = user_id,
                        valid_from_dttm = now_dttm(),
                        valid_to_dttm = now_dttm() + timedelta(access_delta_days)
                    )
                    session.add(access)
                    await session.commit()
                    return DBErrorHandler.ins_row_cnt_handler(1)
                else:
                    return ReturnCode.NOT_FOUND
        except Exception as e:
            return DBErrorHandler.handle_exception(e)
    #
    @staticmethod
    async def get_access(user_tg_id: int, access_name: str) -> UserAccStruct:
        try:
            async with dbs.async_session_factory() as session:
                u = aliased(UserStruct)
                ua = aliased(UserAccStruct)
                q = (
                    select(ua)
                    .join(u, and_(u.user_id == ua.user_id,
                                   u.user_tg_id == user_tg_id,
                                   ua.access_name == access_name))
                )
                res = await session.scalars(q)
                res_fst = res.first()
                return res_fst
        except Exception as e:
            raise e
    #       
    @staticmethod
    async def update_access(user_tg_id: int, access_name: str, access_delta_days: int = None) -> ReturnCode:  
        try:
            async with dbs.async_session_factory() as session:
                q_sel_user = (
                    select(UserStruct.user_id)
                    .where(UserStruct.user_tg_id == user_tg_id)
                )
                res = await session.scalars(q_sel_user)
                user_id = res.first()
                
                q_del_req_acc = (
                    delete(UserAccReqStruct)
                    .where(and_(UserAccReqStruct.access_name == access_name,
                                UserAccReqStruct.user_id == user_id))
                )
                res_1 = await session.execute(q_del_req_acc)
                
                if res_1.rowcount > 0:
                    q_upd_acc = (
                        update(UserAccStruct)
                        .values(valid_from_dttm = now_dttm(), 
                                valid_to_dttm = now_dttm() + timedelta(30 if access_delta_days == None else access_delta_days))
                        .where(and_(UserAccStruct.access_name == access_name,
                                    UserAccStruct.user_id == user_id))
                    )
                    res_2 = await session.execute(q_upd_acc)
                    await session.commit()
                    return DBErrorHandler.upd_row_cnt_handler(res_2.rowcount)
                else:
                    return ReturnCode.NOT_FOUND
        except Exception as e:
            return DBErrorHandler.handle_exception(e)
    #    
    @staticmethod
    async def block_access(user_tg_id: int, access_name: str) -> ReturnCode:  
        try:
            async with dbs.async_session_factory() as session:
                q_sel_user = (
                    select(UserStruct.user_id)
                    .where(UserStruct.user_tg_id == user_tg_id)
                )
                res = await session.scalars(q_sel_user)
                user_id = res.first()
                
                q_upd_acc = (
                    update(UserAccStruct)
                    .values(valid_from_dttm = datetime(1970, 1, 1), 
                            valid_to_dttm = datetime(1970, 1, 2))
                    .where(and_(UserAccStruct.access_name == access_name,
                                UserAccStruct.user_id == user_id))
                )
                res_2 = await session.execute(q_upd_acc)
                await session.commit()
                return DBErrorHandler.upd_row_cnt_handler(res_2.rowcount)
        except Exception as e:
            return DBErrorHandler.handle_exception(e)
    #   
    @staticmethod
    async def delete_access(user_tg_id: int, access_name: str) -> ReturnCode:  
        try:
            async with dbs.async_session_factory() as session:
                q_sel_user = (
                    select(UserStruct.user_id)
                    .where(UserStruct.user_tg_id == user_tg_id)
                )
                res = await session.scalars(q_sel_user)
                user_id = res.first()
                
                q_upd_acc = (
                    delete(UserAccStruct)
                    .where(and_(UserAccStruct.access_name == access_name,
                                UserAccStruct.user_id == user_id))
                )
                res_2 = await session.execute(q_upd_acc)
                await session.commit()
                return DBErrorHandler.del_row_cnt_handler(res_2.rowcount)
        except Exception as e:
            return DBErrorHandler.handle_exception(e)
    
    # Service methods:
    @staticmethod
    async def add_service_config(user_tg_id: int, user_service_id: uuid.UUID, config_name: str, config_price: float = 100, max_config_traffic: float = 100,  expired_delta_days: int = 30) -> ReturnCode:          
        try:
            async with dbs.async_session_factory() as session:
                q_sel_usr = (
                    select(UserStruct.user_id)
                    .where(UserStruct.user_tg_id == user_tg_id)
                )
                res = await session.scalars(q_sel_usr)
                user_id = res.first()
                
                # Init dates:                
                valid_from_dttm = now_dttm()
                valid_to_dttm = now_dttm() + timedelta(expired_delta_days)
                
                # Init hash-keys:
                service_config_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(user_id) + str(config_name))

                # Make new service config:
                user_service_config = UserServConfStruct(
                    service_config_id = service_config_id,
                    user_id = user_id,
                    config_name = config_name,
                    config_price = config_price,
                    max_config_traffic = max_config_traffic,
                    user_service_id = user_service_id,
                    valid_from_dttm = valid_from_dttm,
                    valid_to_dttm = valid_to_dttm
                )
                session.add(user_service_config)
                await session.commit()
                return DBErrorHandler.ins_row_cnt_handler(1)

        except Exception as e:
            return DBErrorHandler.handle_exception(e)
    #
    @staticmethod
    async def get_service_config(user_tg_id: int, config_name: str) -> UserServConfStruct:
        try:
            async with dbs.async_session_factory() as session:
                u = aliased(UserStruct)
                ua = aliased(UserServConfStruct)
                q = (
                    select(ua)
                    .join(u, and_(u.user_id == ua.user_id,
                                   u.user_tg_id == user_tg_id,
                                   ua.config_name == config_name))
                )
                res = await session.scalars(q)
                res_fst = res.first()
                return res_fst
        except Exception as e:
            raise e
    #
    @staticmethod
    async def delete_service_config(user_tg_id: int, config_name: str) -> UserServConfStruct:
        try:
            async with dbs.async_session_factory() as session:
                u = aliased(UserStruct)
                ua = aliased(UserServConfStruct)
                q = (
                    select(ua)
                    .join(u, and_(u.user_id == ua.user_id,
                                   u.user_tg_id == user_tg_id,
                                   ua.config_name == config_name))
                )
                res = await session.scalars(q)
                user_service_config = res.first()
                
                await session.delete(user_service_config)
                await session.commit()
                return DBErrorHandler.del_row_cnt_handler(1)
        except Exception as e:
            raise e
    #
    @staticmethod
    async def get_service_configs(user_tg_id: int) -> list[UserServConfStruct]:
        try:
            async with dbs.async_session_factory() as session:
                u = aliased(UserStruct)
                ua = aliased(UserServConfStruct)
                q = (
                    select(ua)
                    .join(u, and_(u.user_id == ua.user_id,
                                   u.user_tg_id == user_tg_id))
                    .order_by(ua.config_name)
                )
                res = await session.scalars(q)
                res_fst = res.all()
                return res_fst
        except Exception as e:
            raise e
    #    
    @staticmethod
    async def update_service_config(user_tg_id: int, config_name: str, config_price: float = None, cached_data: dict = None, max_config_traffic: float = None, user_service_id: uuid.UUID = None, expired_delta_days: int = None) -> UserServConfStruct:
        try:
            async with dbs.async_session_factory() as session:
                q_sel_usr = (
                    select(UserStruct.user_id)
                    .where(UserStruct.user_tg_id == user_tg_id)
                )
                res = await session.scalars(q_sel_usr)
                user_id = res.first()
                
                update_values = {}
                if config_price is not None:
                    update_values["config_price"] = config_price
                if max_config_traffic is not None:
                    update_values["max_config_traffic"] = max_config_traffic
                if user_service_id is not None:
                    update_values["user_service_id"] = user_service_id
                if expired_delta_days is not None:
                    update_values["valid_to_dttm"] = now_dttm() + timedelta(expired_delta_days)
                if cached_data is not None:
                    update_values["cached_data"] = cached_data
                
                q_upd_serv_conf = (
                    update(UserServConfStruct)
                    .values(**update_values)
                    .where(and_(UserServConfStruct.user_id == user_id,
                                UserServConfStruct.config_name == config_name))
                )
                res_2 = await session.execute(q_upd_serv_conf)
                await session.commit()
                return DBErrorHandler.upd_row_cnt_handler(res_2.rowcount)
        except Exception as e:
            raise e
        
    # Order methods:
    @staticmethod
    async def add_order(user_tg_id: int, config_name: str, order_status: str = 'NEW',  expired_delta_days: int = 30) -> ReturnCode:  
        try:
            async with dbs.async_session_factory() as session:
                q_sel_usr = (
                    select(UserStruct.user_id)
                    .where(UserStruct.user_tg_id == user_tg_id)
                )
                res = await session.scalars(q_sel_usr)
                user_id = res.first()
                
                q_sel_serv_conf = (
                    select(UserServConfStruct)
                    .where(and_(UserServConfStruct.config_name == config_name,
                                UserServConfStruct.user_id == user_id))
                )
                res = await session.scalars(q_sel_serv_conf)
                user_serv_conf = res.first()
                
                q_sel_n_ords = (
                    select(OrderStruct.order_id)
                    .where(and_(OrderStruct.service_config_id == user_serv_conf.service_config_id,
                                OrderStruct.user_id == user_id,
                                or_(OrderStruct.order_status == 'NEW',
                                    OrderStruct.order_status == 'PAYED'))
                                )
                )
                res = await session.scalars(q_sel_n_ords)
                n_order_id = res.first()
                
                if n_order_id:
                    logger.error('order_status IN "NEW" OR "PAYED" STATUS WAS FOUND. CLOSE THEM FIRST')
                    return ReturnCode.UNIQUE_VIOLATION
                else:
                    order_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(user_id) + str(user_serv_conf.service_config_id) + str(now_dttm()))
                    
                    if user_serv_conf.service_config_id:
                        order = OrderStruct(
                            order_id = order_id,
                            order_status = order_status,
                            user_id = user_id,
                            service_config_id = user_serv_conf.service_config_id,
                            order_data = {
                                'config_name': user_serv_conf.config_name,
                                'config_price': user_serv_conf.config_price,
                                'max_config_traffic': user_serv_conf.max_config_traffic,
                                'expired_delta_days': expired_delta_days
                            }
                        )
                        session.add(order)
                        await session.commit()
                        return DBErrorHandler.ins_row_cnt_handler(1)
                    else:
                        return ReturnCode.NOT_FOUND
        except Exception as e:
            return DBErrorHandler.handle_exception(e)
    #
    @staticmethod
    async def get_order(user_tg_id: int, config_name: str, order_status: str = 'NEW') -> OrderStruct:
        try:
            async with dbs.async_session_factory() as session:
                u = aliased(UserStruct)
                ua = aliased(UserServConfStruct)
                q = (
                    select(ua)
                    .join(u, and_(u.user_id == ua.user_id,
                                   u.user_tg_id == user_tg_id,
                                   ua.config_name == config_name))
                )
                res = await session.scalars(q)
                user_service_config = res.first()
                
                if user_service_config:
                    q_sel_ord = (
                        select(OrderStruct)
                        .where(and_(OrderStruct.user_id == user_service_config.user_id,
                                    OrderStruct.service_config_id == user_service_config.service_config_id,
                                    OrderStruct.order_status == order_status))
                    )
                    res = await session.scalars(q_sel_ord)
                    order = res.first()
                    return order
                else:
                    return None
        except Exception as e:
            raise e
    #
    @staticmethod
    async def get_orders(user_tg_id: int) -> list[OrderStruct]:
        try:
            async with dbs.async_session_factory() as session:
                q_sel_usr = (
                    select(UserStruct.user_id)
                    .where(UserStruct.user_tg_id == user_tg_id)
                )
                res = await session.scalars(q_sel_usr)
                user_id = res.first()
                
                q_sel_ord = (
                    select(OrderStruct)
                    .where(OrderStruct.user_id == user_id)
                )
                res = await session.scalars(q_sel_ord)
                orders = res.all()
                return orders
        except Exception as e:
            raise e
    #
    @staticmethod
    async def get_payed_orders(limit: int = 3) -> list[tuple]:
        try:
            async with dbs.async_session_factory() as session:
                o = aliased(OrderStruct)
                u = aliased(UserStruct)
                q_sel_ord = (
                    select(u.user_tg_id,
                           o.order_status,
                           o.order_data,
                           o.sys_updated_dttm)
                    .join(u, and_(o.user_id == u.user_id,
                                  o.order_status == 'PAYED'))
                    .order_by(u.user_tg_id)
                    .limit(limit)
                )
                res = await session.execute(q_sel_ord)
                orders = res.all()
                return orders
        except Exception as e:
            raise e
    #       
    @staticmethod
    async def update_order_status(user_tg_id: int, config_name: str, old_order_status: str, new_order_status: str) -> ReturnCode:  
        try:
            async with dbs.async_session_factory() as session:
                u = aliased(UserStruct)
                ua = aliased(UserServConfStruct)
                q = (
                    select(ua)
                    .join(u, and_(u.user_id == ua.user_id,
                                   u.user_tg_id == user_tg_id,
                                   ua.config_name == config_name))
                )
                res = await session.scalars(q)
                user_service_config = res.first()
            
                q_upd_order = (
                    update(OrderStruct)
                    .values(order_status = new_order_status)
                    .where(and_(OrderStruct.user_id == user_service_config.user_id,
                                OrderStruct.service_config_id == user_service_config.service_config_id,
                                OrderStruct.order_status == old_order_status))
                )
                res_2 = await session.execute(q_upd_order)
                await session.commit()
                return DBErrorHandler.upd_row_cnt_handler(res_2.rowcount)
            
        except Exception as e:
            return DBErrorHandler.handle_exception(e)
        
    @staticmethod
    async def close_payed_order(user_tg_id: int, config_name: str, expired_delta_days: int = 30) -> ReturnCode:  
        '''
            1. update order status
            2. update service config
            ?3. try to update service
        '''
        try:
            async with dbs.async_session_factory() as session:
                o = aliased(OrderStruct)
                u = aliased(UserStruct)
                usc = aliased(UserServConfStruct)
                
                sel_order = (
                    select(o)
                    .join(u, and_(u.user_id == o.user_id,
                                   u.user_tg_id == user_tg_id,
                                   o.order_status == 'PAYED',
                                   cast(o.order_data['config_name'], String) == f'"{config_name}"'))
                )
                order_res = await session.scalars(sel_order)
                order = order_res.first()
                
                order_config_price = order.order_data['config_price']
                order_max_config_traffic = order.order_data['max_config_traffic']
                                
                sel_usr_conf = (
                    select(usc)
                    .join(u, and_(u.user_id == usc.user_id,
                                   u.user_tg_id == user_tg_id,
                                   usc.config_name == config_name))
                )
                usr_conf_res = await session.scalars(sel_usr_conf)
                user_service_config = usr_conf_res.first()
                
                q_upd_order = (
                    update(o)
                    .values(order_status = 'CLOSED')
                    .where(and_(o.user_id == user_service_config.user_id,
                                o.service_config_id == user_service_config.service_config_id,
                                o.order_status == 'PAYED'))
                )
                
                q_upd_serv_conf = (
                    update(usc)
                    .values(valid_from_dttm = now_dttm(),
                            valid_to_dttm = now_dttm() + timedelta(expired_delta_days),
                            config_price = order_config_price,
                            max_config_traffic = order_max_config_traffic)
                    .where(and_(usc.user_id == user_service_config.user_id,
                                usc.service_config_id == user_service_config.service_config_id))
                )
                upd_order_resp = await session.execute(q_upd_order)
                upd_serv_conf_resp = await session.execute(q_upd_serv_conf)
                
                if upd_order_resp.rowcount > 0 and upd_serv_conf_resp.rowcount > 0:
                    await session.commit()
                    return ReturnCode.SUCCESS
                else:
                    await session.rollback()
                    return ReturnCode.NOT_FOUND
            
        except Exception as e:
            return DBErrorHandler.handle_exception(e)
    #    
    @staticmethod
    async def delete_order(user_tg_id: int, config_name: str, order_status: str) -> ReturnCode:  
        try:
            async with dbs.async_session_factory() as session:
                u = aliased(UserStruct)
                ua = aliased(UserServConfStruct)
                q = (
                    select(ua)
                    .join(u, and_(u.user_id == ua.user_id,
                                   u.user_tg_id == user_tg_id,
                                   ua.config_name == config_name))
                )
                res = await session.scalars(q)
                user_service_config = res.first()
            
                q_upd_order = (
                    delete(OrderStruct)
                    .where(and_(OrderStruct.user_id == user_service_config.user_id,
                                OrderStruct.service_config_id == user_service_config.service_config_id,
                                OrderStruct.order_status == order_status))
                )
                res_2 = await session.execute(q_upd_order)
                await session.commit()
                return DBErrorHandler.del_row_cnt_handler(res_2.rowcount)
            
        except Exception as e:
            return DBErrorHandler.handle_exception(e)

    