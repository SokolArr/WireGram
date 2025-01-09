from sqlalchemy.orm import declarative_base
from sqlalchemy.engine import Engine
from sqlalchemy import Column, Text, TIMESTAMP
from sqlalchemy.sql import text

import logging
BASE = declarative_base()
class BaseTable(BASE):
    '''
        __abstract__
        __tablename__
        __table_args__
        __mapper_args__
        __init_subclass__()
        __repr__()
    '''
    __abstract__        = True
    DEFAULT_SCHEMA_NAME = 'main'
    sys_processed_by    = Column(Text)
    sys_processed_dttm  = Column(TIMESTAMP)
    
    @classmethod
    async def create_view(cls, engine: Engine, schema_name: str=None, view_name:str =None):
        if await cls.check_table(cls, engine):
            if view_name is None:
                view_name = cls.__tablename__
            if schema_name is None:
                schema_name = cls.DEFAULT_SCHEMA_NAME
            table_name = cls.__tablename__
            
            sql = f'''
            CREATE OR REPLACE VIEW {schema_name}."v_{table_name}" AS
            SELECT * FROM {schema_name}."{table_name}";
            '''
            
            async with engine.connect() as connection:
                await connection.execute(text(sql))
                print(f"View 'v_{view_name}' created successfully.")
        else:
            logging.error(f'NO {cls.__table_args__["schema"]}."{cls.__tablename__}')
            
    @classmethod
    async def create(cls, engine: Engine, schema_name: str=None, view_name:str =None):
        if await cls.check_table(cls, engine):
            logging.error(f'{cls.__table_args__["schema"]}."{cls.__tablename__} ALREADY EXISTS')
        else:
            async with engine.begin() as connection:
                await connection.run_sync(cls.__table__.create)
            logging.info(f'SUCCESFULL CREATED {cls.__table_args__["schema"]}."{cls.__tablename__}"')
            
            
    @classmethod        
    async def check_logs_schema(engine: Engine):
        async with engine.connect() as connection:
            result = await connection.execute(text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.schemata 
                    WHERE schema_name = 'logs'
                ) AS schema_exists;
            """))
            return result.scalar()
        
    
    async def check_table(cls, engine: Engine):
        async with engine.connect() as connection:
            result = await connection.execute(text(f"""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    where table_name = '{cls.__tablename__}'
                ) AS schema_exists;
            """))
            return result.scalar()
            
    async def create_log_table(cls, engine, schema_name=None):
        column_names = [column.name for column in cls.__table__.columns]
        table_name = cls.__tablename__
        if await cls.check_logs_schema(engine=engine):
            if schema_name is None:
                schema_name = cls.DEFAULT_SCHEMA_NAME
        
            insert_function_sql = f"""
                CREATE OR REPLACE FUNCTION log_{table_name}_insert() RETURNS TRIGGER AS $$
                BEGIN
                    INSERT INTO logs.{table_name} ({', '.join(column_names)}, process_type, process_dttm)
                    VALUES ({', '.join(['NEW.' + name for name in column_names])}, 'INSERT', current_timestamp);
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
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

            delete_function_sql = f"""
                CREATE OR REPLACE FUNCTION log_{table_name}_delete() RETURNS TRIGGER AS $$
                BEGIN
                    INSERT INTO logs.{table_name} ({', '.join(column_names)}, process_type, process_dttm)
                    VALUES ({', '.join(['OLD.' + name for name in column_names])}, 'DELETE', current_timestamp);
                    RETURN OLD;
                END;
                $$ LANGUAGE plpgsql;
            """
            print(insert_function_sql, update_function_sql, delete_function_sql)
            
        else:
            logging.error("NO logs SCHEMA")
            
        
            
        # connection.execute(text(insert_function_sql))
        # connection.execute(text(update_function_sql))
        # connection.execute(text(delete_function_sql))