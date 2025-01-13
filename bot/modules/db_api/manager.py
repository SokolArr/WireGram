import uuid
import logging
from enum import Enum
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, insert, update, delete, and_, text, Sequence
from sqlalchemy.orm import aliased, MappedColumn
from sqlalchemy.exc import IntegrityError

from .db_instance import Base, sync_engine, async_engine, session_factory, async_session_factory, exceptions
from .db_instance import WRITE_LOGS, MAIN_SCHEMA_NAME
from .models import UserStruct, UserAccessStruct, UserReqAccessStruct, UserOrderStruct

logger = logging.getLogger(name=__name__+'.py')

class ReturnCodes(Enum):
    SUCCESS                 = 0
    UNIQUE_VIOLATION        = -1
    FOREIGN_KEY_VIOLATION   = -2
    NOT_FOUND               = -3
    NOT_MET_CONDITION       = -4
    DATABASE_ERROR          = -99
    
class OrderStatus(Enum):
    NEW = 'NEW'
    PAYED = 'PAYED'
    CLOSED = 'CLOSED'
    
    
class OrderResponse(Enum):
    NEW_ORDER_EXIST = 'NEW_ORDER_EXIST'
    NEW_ORDER_NF = 'NEW_ORDER_NF'
    PAYED_ORDER_EXIST = 'PAYED_ORDER_EXIST'
    PAYED_ORDER_NF = 'PAYED_ORDER_NF'
    SUCCESS = 'SUCCESS'
    BAD_TRY = 'BAD_TRY'

class DBErrorHandler:
    @staticmethod
    def handle_exception(e: Exception) -> int:
        if isinstance(e, IntegrityError):
            err_message = ''
            if e.orig:
                err_message = str(e.orig.args[0])
            if 'UniqueViolationError' in err_message:
                return ReturnCodes.UNIQUE_VIOLATION
            elif 'ForeignKeyViolationError' in err_message:
                return ReturnCodes.FOREIGN_KEY_VIOLATION
            else:
                print(f"Ошибка: {err_message}")
                return ReturnCodes.DATABASE_ERROR
        else:
            return ReturnCodes.DATABASE_ERROR
         
def now_dttm():
    return datetime.now(timezone.utc).replace(tzinfo=None)
        
class DbManager():
    MONTH_TIME_DELTA = 30
    
    def create_db(self):
        sync_engine.echo = False
        if self.check_db_available():
            logging.info("DB ALREADY EXISTS!")
        else:
            self.__create_schemas()
            Base.metadata.drop_all(sync_engine)
            Base.metadata.create_all(sync_engine)
            if WRITE_LOGS: self.__create_logs_triggers([UserStruct, UserAccessStruct, UserReqAccessStruct])
            sync_engine.echo = True

    def check_db_available(self):
        try:
            with session_factory() as session:
                q = (
                    text("SELECT 1 FROM main.user")
                )
                res = session.execute(q)
                return res.scalar()
        except:
            return False

    @staticmethod
    def __create_logs_triggers(classes:list[Base], schema_name:str =None):
        try:
            with session_factory() as session:
                create_sql = f"""
                    DROP SCHEMA IF EXISTS logs CASCADE;
                    CREATE SCHEMA IF NOT EXISTS logs;
                """
                session.execute(text(create_sql))
                session.commit()
                
            for cls in classes:
                if cls.WRITE_LOGS:
                    with session_factory() as session:
                        column_names = [column.name for column in cls.__table__.columns]
                        table_name = cls.__tablename__
                        if schema_name is None:
                            schema_name = MAIN_SCHEMA_NAME
                            
                        create_sql = f'''
                            DROP TABLE IF EXISTS logs."{table_name}" CASCADE;
                            CREATE TABLE logs."{table_name}" 
                            AS SELECT "{table_name}".*
                            FROM {schema_name}."{table_name}";
                        '''
                        
                        alter_sql = f'''
                            ALTER TABLE logs."{table_name}"
                            ADD COLUMN log_id SERIAL PRIMARY KEY,
                            ADD COLUMN log_processed_type TEXT,
                            ADD COLUMN log_processed_dttm TIMESTAMP;
                        '''
                        

                        insert_function_sql = f"""
                            CREATE OR REPLACE FUNCTION log_{table_name}_insert() RETURNS TRIGGER AS $$
                            BEGIN
                                INSERT INTO logs.{table_name} ({', '.join(column_names)}, log_processed_type, log_processed_dttm)
                                VALUES ({', '.join(['NEW.' + name for name in column_names])}, 'INSERT', current_timestamp);
                                RETURN NEW;
                            END;
                            $$ LANGUAGE plpgsql;
                        """
                        insert_trigger_sql = f"""
                            CREATE TRIGGER after_{table_name}_insert
                            AFTER INSERT ON {schema_name}.{table_name}
                            FOR EACH ROW EXECUTE FUNCTION log_{table_name}_insert();
                        """

                        update_function_sql = f"""
                            CREATE OR REPLACE FUNCTION log_{table_name}_update() RETURNS TRIGGER AS $$
                            BEGIN
                                INSERT INTO logs.{table_name} ({', '.join(column_names)}, log_processed_type, log_processed_dttm)
                                VALUES ({', '.join(['NEW.' + name for name in column_names])}, 'UPDATE', current_timestamp);
                                RETURN NEW;
                            END;
                            $$ LANGUAGE plpgsql;
                        """
                        update_trigger_sql = f"""
                            CREATE TRIGGER after_{table_name}_update
                            AFTER UPDATE ON {schema_name}.{table_name}
                            FOR EACH ROW EXECUTE FUNCTION log_{table_name}_update();
                        """

                        delete_function_sql = f"""
                            CREATE OR REPLACE FUNCTION log_{table_name}_delete() RETURNS TRIGGER AS $$
                            BEGIN
                                INSERT INTO logs.{table_name} ({', '.join(column_names)}, log_processed_type, log_processed_dttm)
                                VALUES ({', '.join(['OLD.' + name for name in column_names])}, 'DELETE', current_timestamp);
                                RETURN OLD;
                            END;
                            $$ LANGUAGE plpgsql;
                        """
                        delete_trigger_sql =f"""
                            CREATE TRIGGER after_{table_name}_delete
                            AFTER DELETE ON {schema_name}.{table_name}
                            FOR EACH ROW EXECUTE FUNCTION log_{table_name}_delete();
                        """           
                    session.execute(text(create_sql))
                    session.execute(text(alter_sql))
                    
                    session.execute(text(insert_function_sql))
                    session.execute(text(insert_trigger_sql))
                    
                    session.execute(text(update_function_sql))
                    session.execute(text(update_trigger_sql))
                    
                    session.execute(text(delete_function_sql))
                    session.execute(text(delete_trigger_sql))
                    
                    session.commit()
            logging.info("TRIGGERS OK!")
                
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            return False
        
    @staticmethod
    def __create_schemas():
        try:
            with session_factory() as session:
                create_sql = f"""
                    DROP SCHEMA IF EXISTS main CASCADE;
                    CREATE SCHEMA IF NOT EXISTS main;

                    DROP SCHEMA IF EXISTS logs CASCADE;
                    CREATE SCHEMA IF NOT EXISTS logs;
                """
                session.execute(text(create_sql))
                session.commit()
                logging.info("SCHEMAS OK!")
                
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            return False
        
    @staticmethod
    async def get_admins() -> tuple[UserStruct]: 
        async with async_session_factory() as session:
            q = (
                select(UserStruct.user_tg_code)
                .select_from(UserStruct)
                .where(UserStruct.admin_flg == True)
            )
            res = await session.execute(q)
            return res.all()

    @staticmethod
    async def upgrade_user(user_tg_code: str):
        user_tg_code = str(user_tg_code)
        async with async_session_factory() as session:
            q = (
                update(UserStruct)
                .values(admin_flg = True)
                .where(UserStruct.user_tg_code == user_tg_code)
            )
            res = await session.execute(q)
            await session.commit()
            return res

    @staticmethod
    async def downgrade_user(user_tg_code: str):
        user_tg_code = str(user_tg_code)
        async with async_session_factory() as session:
            q = (
                update(UserStruct)
                .values(admin_flg = False)
                .where(UserStruct.user_tg_code == user_tg_code)
            )
            res = await session.execute(q)
            await session.commit()
            return res

    @staticmethod
    async def add_user(user: UserStruct) -> str:  
        async with async_session_factory() as session:
            new_user_tg_code = user.user_tg_code
            session.add(user)
            logger.debug(f'SUCCESSFUL ADD NEW USER: {user.user_tg_code}')
            await session.commit()
        return new_user_tg_code
    
    @staticmethod
    async def add_order(order: UserOrderStruct):
        try:
            async with async_session_factory() as session:
                session.add(order)
                await session.commit()
                return ReturnCodes.SUCCESS
        except Exception as e:
            return DBErrorHandler.handle_exception(e)
        
    @staticmethod
    async def update_order(order: UserOrderStruct):
        try:
            async with async_session_factory() as session:
                q = (
                    update(UserOrderStruct)
                    .values(order_status = order.order_status)
                    .where(and_(UserOrderStruct.order_id == order.order_id))
                )
                res = await session.execute(q)

                await session.commit()
                if res.rowcount > 0:
                    logger.debug(ReturnCodes.SUCCESS)
                    return ReturnCodes.SUCCESS
                else:
                    logger.debug(ReturnCodes.NOT_FOUND)
                    return ReturnCodes.NOT_FOUND
        except Exception as e:
            logger.debug(f'{e}{DBErrorHandler.handle_exception(e)}')
            return DBErrorHandler.handle_exception(e)
        
    @staticmethod
    async def get_new_order_by_user_id(user_id: uuid.UUID):
        try:
            async with async_session_factory() as session:
                q = (
                    select(UserOrderStruct)
                    .select_from(UserOrderStruct)
                    .where(and_(UserOrderStruct.user_id == user_id,
                                UserOrderStruct.order_status == 'NEW'))
                )
                res = await session.execute(q)
                res_obj = res.one()
                return res_obj[0] if res_obj is not None else res_obj
        except Exception:
            pass

    @staticmethod
    async def get_payed_order_by_user_id(user_id: uuid.UUID):
        try:
            async with async_session_factory() as session:
                q = (
                    select(UserOrderStruct)
                    .select_from(UserOrderStruct)
                    .where(and_(UserOrderStruct.user_id == user_id,
                                UserOrderStruct.order_status == 'PAYED'))
                )
                res = await session.execute(q)
                res_obj = res.one()
                return res_obj[0] if res_obj is not None else res_obj
        except Exception:
            pass
    
    @staticmethod
    async def get_last_order_by_user_id(user_id: uuid.UUID):
        try:
            async with async_session_factory() as session:
                q = (
                    select(UserOrderStruct)
                    .select_from(UserOrderStruct)
                    .where(UserOrderStruct.user_id == user_id)
                    .order_by(UserOrderStruct.sys_processed_dttm.desc())
                    .limit(1)
                )
                res = await session.execute(q)
                res_obj = res.one()
                print(res_obj)
                return res_obj[0] if res_obj is not None else res_obj
        except Exception:
            pass
    
    @staticmethod
    async def add_request(request_access: UserReqAccessStruct):  
        async with async_session_factory() as session:
            req_access_name = request_access.req_access_name
            session.add(request_access)
            await session.commit()
        return req_access_name
    
    @staticmethod
    async def add_access(access: UserAccessStruct) -> int:  
        try:
            async with async_session_factory() as session:
                session.add(access)
                await session.commit()
                return ReturnCodes.SUCCESS
        except Exception as e:
            return DBErrorHandler.handle_exception(e)
        
    @staticmethod
    async def update_access(access: UserAccessStruct):  
        try:
            async with async_session_factory() as session:
                q = (
                    update(UserAccessStruct)
                    .values(access_from_dttm = access.access_from_dttm,
                            access_to_dttm = access.access_to_dttm)
                    .where(and_(UserAccessStruct.user_id == access.user_id, 
                                UserAccessStruct.access_name == access.access_name
                    ))
                )
                res = await session.execute(q)

                await session.commit()
                if res.rowcount > 0:
                    logger.debug(ReturnCodes.SUCCESS)
                    return ReturnCodes.SUCCESS
                else:
                    logger.debug(ReturnCodes.NOT_FOUND)
                    return ReturnCodes.NOT_FOUND
        except Exception as e:
            logger.debug(f'{e}{DBErrorHandler.handle_exception(e)}')
            return DBErrorHandler.handle_exception(e)

    @staticmethod
    async def get_user_by_tg_code(user_tg_code: str) -> UserStruct: 
        user_tg_code = str(user_tg_code)
        async with async_session_factory() as session:
            q = (
                select(UserStruct)
                .select_from(UserStruct)
                .where(UserStruct.user_tg_code == user_tg_code)
            )
            res = await session.execute(q)
            res_obj = res.one_or_none()
            return res_obj[0] if res_obj is not None else res_obj
        
    @staticmethod
    async def get_access_by_user_id_access_name(user_id: uuid.UUID, access_name: str) -> UserAccessStruct: 
        async with async_session_factory() as session:
            q = (
                select(UserAccessStruct)
                .select_from(UserAccessStruct)
                .where( and_(UserAccessStruct.user_id == user_id, 
                             UserAccessStruct.access_name == access_name
                ))
            )
            res = await session.execute(q)
            res_obj = res.one_or_none()
            return res_obj[0] if res_obj is not None else res_obj
        
    @staticmethod
    async def get_requests_by_request_name(request_name: str) -> Sequence: 
        async with async_session_factory() as session:
            r = aliased(UserReqAccessStruct)
            u = aliased(UserStruct)
            q = (
                select(
                    u.user_tg_code,
                    u.user_tag,
                    r.req_access_name,
                    r.sys_processed_dttm)
                .select_from(r)
                .join(u, (r.user_id == u.user_id), isouter=True)
                .where(r.req_access_name==request_name)
            )
            res = await session.execute(q)
            return res.all()
      
    @staticmethod
    async def get_request_by_user_id_request_name(user_id: uuid.UUID, request_name: str) -> UserReqAccessStruct: 
        async with async_session_factory() as session:
            q = (
                select(UserReqAccessStruct)
                .select_from(UserReqAccessStruct)
                .where( and_(UserReqAccessStruct.user_id == user_id, 
                             UserReqAccessStruct.req_access_name == request_name
                ))
            )
            res = await session.execute(q)
            res_obj = res.one_or_none()
            return res_obj[0] if res_obj is not None else res_obj
        
    async def accept_request_by_user_id_request_name(self, user_id: str, access_name: str):
        access = UserAccessStruct(
                user_id = user_id,
                access_name = access_name,
                access_from_dttm = now_dttm(),
                access_to_dttm = now_dttm() + timedelta(self.MONTH_TIME_DELTA)
        )
        if await self.get_access_by_user_id_access_name(user_id, access_name) == None:
            async with async_session_factory() as session:
                q_del = (
                        delete(UserReqAccessStruct)
                        .where(and_(UserReqAccessStruct.user_id == user_id, 
                                    UserReqAccessStruct.req_access_name == access_name
                        ))
                    )
                res_del = await session.execute(q_del)
                rows_del_count = res_del.rowcount
                if await self.add_access(access):
                    await session.commit()
                return (rows_del_count, -1)
        else:
            async with async_session_factory() as session:
                q_del = (
                    delete(UserReqAccessStruct)
                    .where(and_(UserReqAccessStruct.user_id == user_id, 
                                UserReqAccessStruct.req_access_name == access_name
                    ))
                )
                q_upd = (
                    update(UserAccessStruct)
                    .values(access_from_dttm = access.access_from_dttm,
                            access_to_dttm = access.access_to_dttm)
                    .where(and_(UserAccessStruct.user_id == user_id, 
                                UserAccessStruct.access_name == access_name
                    ))
                )
                res_del = await session.execute(q_del)
                await session.flush()
                res_upd = await session.execute(q_upd)
                rows_del_count = res_del.rowcount
                rows_upd_ount = res_upd.rowcount
                await session.commit()
                return (rows_del_count, rows_upd_ount)
   
    @staticmethod
    async def delete_access_request_by_user_id_request_name(user_id: uuid.UUID, request_name: str): 
        async with async_session_factory() as session:
            q = (
                delete(UserReqAccessStruct)
                .where(and_(UserReqAccessStruct.user_id == user_id, 
                             UserReqAccessStruct.req_access_name == request_name
                ))
            )
            res = await session.execute(q)
            await session.commit()
            return res
        
    @staticmethod
    async def update_request_by_user_id_request_name(user_id: uuid.UUID, access_name: str, new_user_access_struct: UserAccessStruct): 
        async with async_session_factory() as session:
            q = (
                update(UserAccessStruct)
                .values(access_from_dttm = new_user_access_struct.access_from_dttm,
                        access_to_dttm = new_user_access_struct.access_to_dttm)
                .where(and_(UserAccessStruct.user_id == user_id, 
                             UserAccessStruct.access_name == access_name
                ))
            )
            res = await session.execute(q)
            await session.commit()
            return res
    
    
    
    
