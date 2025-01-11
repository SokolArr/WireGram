import uuid
import logging

from sqlalchemy import select, insert, update, delete, and_, text, Sequence
from sqlalchemy.orm import aliased, MappedColumn

from .db_instance import Base, sync_engine, async_engine, session_factory, async_session_factory, WRITE_LOGS, MAIN_SCHEMA_NAME
from .models import UserStruct, UserAccessStruct, UserReqAccessStruct, UserOrderStruct

logger = logging.getLogger(name=__name__+'.py')

class DbManager():
    def create_db(self):
        sync_engine.echo = False
        Base.metadata.drop_all(sync_engine)
        Base.metadata.create_all(sync_engine)
        if WRITE_LOGS: self.__create_logs_triggers([UserStruct, UserAccessStruct, UserReqAccessStruct])
        sync_engine.echo = True

    def check_db_available(self):
        with session_factory() as session:
            q = (
                text("SELECT 1")
            )
            res = session.execute(q)
            return res.scalar()
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
                    logging.info("Triggers ok!")
                
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            return False
        
    @staticmethod
    async def init_admins(admins: list[str]):
        # for admin in admins:
        #     # user_tg_code 
            
        #     user = UserStruct(
        #         user_id = uuid.uuid5(uuid.NAMESPACE_DNS, )
                
        #     )
        #     async with async_session_factory() as session:
        #         session.add(UserStruct)
        #         await session.commit()
        pass #TODO rework list admins = lis[UserStruct]
        
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
        async with async_session_factory() as session:
            new_order_id = order.order_id
            session.add(order)
            await session.commit()
        return new_order_id
    
    @staticmethod
    async def add_request(request_access: UserReqAccessStruct):  
        async with async_session_factory() as session:
            req_access_name = request_access.req_access_name
            session.add(request_access)
            await session.commit()
        return req_access_name
    
    @staticmethod
    async def add_access(access: UserAccessStruct):  
        async with async_session_factory() as session:
            access_name = access.access_name
            session.add(access)
            await session.commit()
        return access_name

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
        
    @staticmethod
    async def delete_request_by_user_id_request_name(user_id: uuid.UUID, request_name: str) -> UserReqAccessStruct: 
        async with async_session_factory() as session:
            q = (
                delete(UserReqAccessStruct)
                .where( and_(UserReqAccessStruct.user_id == user_id, 
                             UserReqAccessStruct.req_access_name == request_name
                ))
            )
            res = await session.execute(q)
            res_obj = res.one_or_none()
            return res_obj[0] if res_obj is not None else res_obj
    
    
    
    
