import uuid
import logging

from sqlalchemy import select, insert, update, delete, and_, text

from .db_instance import Base, sync_engine, async_engine, session_factory, async_session_factory, WRITE_LOGS, MAIN_SCHEMA_NAME
from .models import UserOrm, UserAccessOrm

class DbManager():
    def create_db(self):
        sync_engine.echo = True
        Base.metadata.drop_all(sync_engine)
        Base.metadata.create_all(sync_engine)
        if WRITE_LOGS: self.__create_logs_triggers([UserOrm, UserAccessOrm(WRITE_LOGS = True)])
        sync_engine.echo = True

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
                        column_names = [column.name for column in cls.__table__.columns if column.name not in ['sys_processed_by', 'sys_processed_dttm']]
                        table_name = cls.__tablename__
                        if schema_name is None:
                            schema_name = MAIN_SCHEMA_NAME
                            
                        create_sql = f'''
                            DROP TABLE IF EXISTS logs."{table_name}" CASCADE;
                            CREATE TABLE logs."{table_name}" 
                            AS SELECT "{table_name}".*, '' as process_type, '1970-01-01 00:00:00'::timestamp as process_dttm 
                            FROM {schema_name}."{table_name}";
                        '''

                        insert_function_sql = f"""
                            CREATE OR REPLACE FUNCTION log_{table_name}_insert() RETURNS TRIGGER AS $$
                            BEGIN
                                INSERT INTO logs.{table_name} ({', '.join(column_names)}, process_type, process_dttm)
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
                                INSERT INTO logs.{table_name} ({', '.join(column_names)}, process_type, process_dttm)
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
                                INSERT INTO logs.{table_name} ({', '.join(column_names)}, process_type, process_dttm)
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
                    
                    session.execute(text(insert_function_sql))
                    session.execute(text(insert_trigger_sql))
                    
                    session.execute(text(update_function_sql))
                    session.execute(text(update_trigger_sql))
                    
                    session.execute(text(delete_function_sql))
                    session.execute(text(delete_trigger_sql))
                    
                    session.execute(text(create_sql))
                    session.commit()
                    logging.info("Triggers ok!")
                
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            return False
        
    @staticmethod
    async def init_admins(admins: list[dict]):
        """[{
                'user_tg_code': '12345', 
                'user_name': 'your_name'
            },]
        """
        admins = [
            {
                'user_id': uuid.uuid5(uuid.NAMESPACE_DNS, user['user_tg_code']),
                **user
            }
            for user in admins
        ]
        async with async_session_factory() as session:
            result = await session.execute(
                insert(UserOrm),
                admins
            )
            await session.commit()
            return result

    @staticmethod
    async def upgrade_user(user_tg_code: str):
        async with async_session_factory() as session:
            q = (
                update(UserOrm)
                .values(admin_flg = True)
                .where(UserOrm.user_tg_code == user_tg_code)
            )
            res = await session.execute(q)
            await session.commit()
            return res

    @staticmethod
    async def downgrade_user(user_tg_code: str):
        async with async_session_factory() as session:
            q = (
                update(UserOrm)
                .values(admin_flg = False)
                .where(UserOrm.user_tg_code == user_tg_code)
            )
            res = await session.execute(q)
            await session.commit()
            return res

    @staticmethod
    async def add_new_user(user: UserOrm):  
        async with async_session_factory() as session:
            new_user_tg_code = user.user_tg_code
            session.add(user)
            await session.commit()
        return new_user_tg_code

    @staticmethod
    async def get_user_by_tg_code(user_tg_code: str) -> UserOrm: 
        async with async_session_factory() as session:
            q = (
                select(UserOrm)
                .select_from(UserOrm)
                .where(UserOrm.user_tg_code == user_tg_code)
            )
            res = await session.execute(q)
            user = res.all()
            return user
    
    
    
    
