import logging
import asyncpg

# init Logger
logger = logging.getLogger(name=__name__+'.py')

class DbManager():
    """
    Module: db_manager.py

    This module provides the DbManager class for interacting with a PostgreSQL database using asyncpg.
    It includes methods for building and executing SQL queries asynchronously.

    Class: DbManager

    Attributes:
    - __default_db_conn_params: A dictionary containing default database connection parameters.
    - __main_schema_name: The default schema name used in queries.

    Methods:xn
    1. __init__(self, db_conn_params: dict = __default_db_conn_params, schema_name: str = __main_schema_name)
    Initializes a new instance of the DbManager class with the provided database connection parameters and schema name.

    2. async select_query_builder(columns: list = ['1'], table: str = None, schema: str = __main_schema_name, condition: str= None, limit: int = None) -> str
    Builds a SQL SELECT query based on the provided parameters.
    - Parameters:
        - columns: A list of columns to select. Defaults to ['1'].
        - table: The name of the table to select from.
        - schema: The schema name. Defaults to the main schema.
        - condition: Optional SQL condition for the WHERE clause.
        - limit: Optional limit on the number of results returned.
    - Returns: A string containing the constructed SQL SELECT query.

    3. async insert_query_builder(self, table:str, vals: list[tuple] = None, insert_type: str = 'values', columns: list = None, schema: str = __main_schema_name, **kwargs) -> str
    Builds a SQL INSERT query based on provided parameters.
    - Parameters:
        - table: The name of the table to insert into.
        - vals: A list of tuples containing values to insert.
        - insert_type: Type of insert operation ('values' or 'select'). Defaults to 'values'.
        - columns: Optional list of columns for the insert operation.
        - schema: The schema name. Defaults to the main schema.
        - kwargs: Additional keyword arguments for select-based inserts (sel_columns, sel_table, etc.).
    - Returns: A string containing the constructed SQL INSERT query or an empty string if an error occurs.

    4. async _get_conn(self) -> asyncpg.Connection
    Establishes a connection to the PostgreSQL database using the provided connection parameters.
    - Returns: An instance of asyncpg.Connection.

    5. async fetch_data(self, columns: list = ['1'], schema: str = __main_schema_name, table: str = None, condition: str= None, limit: int = None) -> list[asyncpg.Record]
    Fetches data from the specified table and returns it as a list of records.
    - Parameters:
        - columns: A list of columns to select. Defaults to ['1'].
        - schema: The schema name. Defaults to the main schema.
        - table: The name of the table to fetch from.
        - condition: Optional SQL condition for the WHERE clause.
        - limit: Optional limit on the number of results returned.
    - Returns: A list of records fetched from the database or an empty list if an error occurs.

    6. async ins_data(self, table: str, vals: list[tuple]= None, insert_type: str = 'values', columns: list = None, schema: str = __main_schema_name, sel_columns: list = None, sel_table: str = None, sel_schema: str = None, sel_condition: str= None, sel_limit: int = None) -> int
    Inserts data into the specified table based on provided parameters.
    - Parameters:
        - Same as those in the insert query builder method with additional parameters for select-based inserts.
    - Returns: An integer indicating success (0) or failure (-1).
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
    

    async def fetch_data(self,
                    columns: list = ['1'],
                    schema: str = __main_schema_name, 
                    table: str = None,
                    condition: str= None, 
                    limit: int = None) -> list[asyncpg.Record]:
        query = await self.select_query_builder(columns=columns, schema=schema, table=table, condition=condition, limit=limit)    
        try:
            conn = await self._get_conn()
            rows:list[asyncpg.Record] = await conn.fetch(query)
            logger.debug(f'successful fetch data with query: {query}')
            await conn.close()
            
            return rows
        
        except Exception as e:
            logger.error(f'bad try to fetch data: {e}, with query: {query}')
            return ['']
    
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
            await conn.execute(query)
            logger.debug(f'successful insert data with query: {query}')
            await conn.close()
            
            return 0
        
        except Exception as e:
            logger.error(f'bad try to insert data: {e}, with query: {query}')
            return -1