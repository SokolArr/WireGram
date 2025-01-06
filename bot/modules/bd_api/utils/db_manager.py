import logging
import asyncpg

# init Logger
logger = logging.getLogger(name=__name__+'.py')

class DbManager():
    """
    docs
    """
    
    __default_db_conn_params = {
        'db_name': 'db',
        'db_user': 'admin',
        'db_password': '12345678',
        'db_host': 'localhost',
        'db_port': '2345'
    }
    
    __main_schema_name = 'main'
    
    def __init__(self, db_conn_params: dict = __default_db_conn_params, schema_name: str = __main_schema_name):
        # get db conn params and log this if debug mode on
        self.db_conn_params = db_conn_params
        self.schema_name = schema_name
        logger.debug(f'init user; db_conn_params:{self.db_conn_params}')
    
    @staticmethod
    async def select_query_builder(columns: list = ['1'], 
                            table: str = None, 
                            schema: str = __main_schema_name, 
                            condition: str= None, 
                            limit: int = None) -> str:
        q = f'select {",".join(columns)} ' \
            f'{"from " + schema + "." + table + " " if table else ""}' \
            f'{"where " + condition + " " if condition else ""}' \
            f'{"limit " + str(abs(limit)) + " " if limit else ""}'.strip() + ';'
        return q
    
    @staticmethod
    async def gen_table_triggers(tables:list[dict]) -> str:
        '''tables = [
            {
                'table_name': 'user',
                'cols': ['user_id', 'user_name', 'user_tg_code', 'admin_flg', 'sys_inserted_process', 'sys_inserted_dttm']
            },
            {
                'table_name': 'user_bot_access',
                'cols': ['user_id', 'access_from_dttm', 'access_to_dttm', 'sys_inserted_process', 'sys_inserted_dttm']
            }
        ]'''
        
        out_arr = []
        for el_data in tables:
            table_name = el_data['table_name']
            cols = el_data['cols']
            columns = ', '.join(el_data['cols'])
            
            new_prfx_columns = ', '.join(['new.' + el for el in cols])
            old_prfx_columns = ', '.join(['old.' + el for el in cols])

            out_arr.append(f'''        
--table_name:= {table_name}
drop table if exists logs."{table_name}" cascade;
create table logs."{table_name}" as select "{table_name}".*, '' as oper_code, '1970-01-01 00:00:00'::timestamp oper_dttm from main."{table_name}";                       

drop function if exists main.fn_trg_{table_name}_insert() cascade;
create or replace function main.fn_trg_{table_name}_insert()
returns trigger as $$
begin

    insert into logs."{table_name}" ({columns}, oper_code, oper_dttm)
    values ({new_prfx_columns}, 'I', current_timestamp);
    return new;

end;
$$
language plpgsql;

create trigger after_{table_name}_insert
after insert on main."{table_name}"
for each row
execute function main.fn_trg_{table_name}_insert();

drop function if exists main.fn_trg_{table_name}_update() cascade;
create or replace function main.fn_trg_{table_name}_update()
returns trigger as $$
begin

    insert into logs."{table_name}" ({columns}, oper_code, oper_dttm)
    values ({new_prfx_columns}, 'U', current_timestamp);
    return new;

end;
$$
language plpgsql;

create trigger after_{table_name}_update
after update on main."{table_name}"
for each row
execute function main.fn_trg_{table_name}_update();

drop function if exists main.fn_trg_{table_name}_delete() cascade;
create or replace function main.fn_trg_{table_name}_delete()
returns trigger as $$
begin

    insert into logs."{table_name}" ({columns}, oper_code, oper_dttm)
    values ({old_prfx_columns}, 'D', current_timestamp);
    return new;

end;
$$
language plpgsql;

create trigger after_{table_name}_delete
after delete on main."{table_name}"
for each row
execute function main.fn_trg_{table_name}_delete();'''.strip())
        out_str = '\n\n'.join(out_arr)
        return out_str
    
    async def insert_query_builder(self, 
                            table:str,
                            vals: list[tuple] = None,
                            insert_type: str = 'values',
                            columns: list = None,
                            schema: str = __main_schema_name,
                            **kwargs) -> str:
        '''
        insert_type= values || select
        '''
        if insert_type == 'select':
            sel_columns = kwargs.get('sel_columns')
            sel_table = kwargs.get('sel_table')
            sel_schema = kwargs.get('sel_schema')
            sel_condition = kwargs.get('sel_condition')
            sel_limit = kwargs.get('sel_limit')
            try:
                select_q = await self.select_query_builder(columns=sel_columns, 
                                                           table=sel_table, 
                                                           schema=sel_schema, 
                                                           condition=sel_condition, 
                                                           limit=sel_limit)
                q = f'insert into ' + f'{schema + "." + table + " "}'\
                f'{"(" + (",".join(columns)) + ") " if columns else ""}'\
                f'{select_q}'
                return q
            except Exception as e:
                logger.error(e)
                return ''
            
        elif insert_type == 'values':
            if vals:
                q = f'insert into ' + f'{schema + "." + table + " "}'\
                    f'{"(" + (",".join(columns)) + ") " if columns else ""}'\
                    f'values {",".join(str(val) for val in vals)}'.strip() + ';'
                return q
            else:
                logger.error(f'no values to insert')
                return ''
        else:
            logger.error(f'no such insert_type: {insert_type}')
            return ''
        
    async def _get_conn(self) -> asyncpg.Connection:
        conn: asyncpg.Connection = await asyncpg.connect(
            database    = self.db_conn_params['db_name'],
            user        = self.db_conn_params['db_user'],
            password    = self.db_conn_params['db_password'],
            host        = self.db_conn_params['db_host'],
            port        = self.db_conn_params['db_port']
        )
        return conn
    
    async def _init_db(self, 
                       load_example:bool = False, 
                       db_logging:bool = True):
        
        try:
            with open('./bot/modules/bd_api/utils/sql/main.sql', 'r') as file:
                main_sql = file.read()
            main_sql=main_sql

            #main
            try:
                conn = await self._get_conn()
                await conn.execute(main_sql)
                await conn.close()
                logger.debug(f'successful execute: main.sql')
            except Exception as e:
                logger.error(f'bad try to execute: {e}, with query: {main_sql}')
                raise e
            
            #triggers
            if db_logging:
                tables_info = []
                tables_to_log = ['user', 'user_bot_access', 'user_vpn_access', 'user_req_access', 'user_vpn_price']
            
                for table in tables_to_log:
                    col = [el['column_name'] for el in await self.fetch_data(['distinct column_name'], 
                                                                            'information_schema', 
                                                                            'columns', 
                                                                            "table_schema = 'main' and table_name = '"+table+"'")]
                    if col:
                        tables_info.append({
                            'table_name': table,
                            'cols': col 
                        })
            
                triggers_sql = await self.gen_table_triggers(tables_info)
                try:
                    conn = await self._get_conn()
                    await conn.execute(triggers_sql)
                    await conn.close()
                    logger.debug(f'successful execute: triggers_sql')
                except Exception as e:
                    logger.error(f'bad try to execute: {e}, with query: {triggers_sql}')
                    raise e
                
            #example
            with open('./bot/modules/bd_api/utils/sql/example.sql', 'r') as file:
                example_sql = file.read()  
            example_sql = example_sql
            if load_example & (example_sql != ''):
                try:
                    conn = await self._get_conn()
                    await conn.execute(example_sql)
                    await conn.close()
                    logger.debug(f'successful execute: example.sql')
                except Exception as e:
                    logger.error(f'bad try to execute: {e}, with query: {example_sql}')
                    raise e
            
            #save to db_init.sql
            query = main_sql + triggers_sql + example_sql
            with open('./bot/modules/bd_api/utils/sql/db_init.sql', 'w') as f:
                    f.truncate(0)
                    f.write(query)
            logger.debug(f'successful execute init db. Save file to sql/db_init.sql')
        
        except Exception as e:
                    logger.error(f'bad try to execute bd_init: {e}')
                    raise e
        
        return None

    async def fetch_data(self,
                    columns: list = ['1'],
                    schema: str = __main_schema_name, 
                    table: str = None,
                    condition: str= None, 
                    limit: int = None) -> list[asyncpg.Record]:
        query = await self.select_query_builder(columns=columns, schema=schema, table=table, condition=condition, limit=limit)    
        try:
            conn = await self._get_conn()
            rows = []
            try:
                async with conn.transaction():
                    rows:list[asyncpg.Record] = await conn.fetch(query)
                logger.debug(f'successful fetch data with query: {query}')

            except Exception as e:
                logger.error(f'{e}')
                raise e
            
            finally:
                await conn.close()
            
            return rows
        
        except Exception as e:
            logger.error(f'bad try to fetch data: {e}, with query: {query}')
            raise e
    
    async def ins_data(self, 
                    table: str,
                    vals: list[tuple]= None,
                    insert_type: str = 'values',
                    columns: list = None,
                    schema: str = __main_schema_name,
                    sel_columns: list = None,
                    sel_table: str = None,
                    sel_schema:  str = None,
                    sel_condition: str= None,
                    sel_limit: int = None) -> int:
        query = await self.insert_query_builder(insert_type=insert_type, 
                                                    schema=schema, 
                                                    table=table, 
                                                    columns=columns, 
                                                    vals=vals, 
                                                    sel_columns=sel_columns,
                                                    sel_table=sel_table,
                                                    sel_schema=sel_schema,
                                                    sel_condition=sel_condition,
                                                    sel_limit=sel_limit)
        try:
            conn = await self._get_conn()
            try:
                async with conn.transaction():
                    await conn.execute(query)
                logger.debug(f'successful insert data with query: {query}')
                
            except Exception as e:
                logger.error(f'{e}')
                raise e
            
            finally:
                await conn.close()
            return 0
        
        except Exception as e:
            logger.error(f'bad try to insert data: {e}, with query: {query}')
            raise e