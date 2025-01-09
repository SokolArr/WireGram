from asyncpg import Connection
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class BasePgTable():
    DEFAULT_SCHEMA_NAME = 'main'
    DEFAULT_TABLE_NAME = 'default_table'
    
    def __init__(self, schema_name: str = DEFAULT_SCHEMA_NAME, 
                 table_name: str = DEFAULT_TABLE_NAME, 
                 columns:list = None, 
                 tech_columns:list = None,
                 constraints: list = None):
        self.schema_name = schema_name
        self.table_name = table_name
        self.columns = columns
        self.tech_columns = tech_columns
        self.constraints = constraints if constraints is not None else []
        
    def generate_create_table_sql(self):
        """
        Docs
        """
        sql = f'CREATE TABLE IF NOT EXISTS {self.schema_name}."{self.table_name}" (\n'
        for attr in self.columns:
            name, pg_base_type, is_primary_key, is_not_null = attr[:4]
            default_value = attr[4] if len(attr) > 4 else None
            sql += f" {name} {pg_base_type.sql_definition(is_primary_key, is_not_null, default_value)},\n"

        for attr in self.tech_columns:
            name, pg_base_type, is_primary_key, is_not_null = attr[:4]
            default_value = attr[4] if len(attr) > 4 else None
            sql += f" {name} {pg_base_type.sql_definition(is_primary_key, is_not_null, default_value)},\n"
            
        for constraint in self.constraints:
            sql += f" CONSTRAINT {constraint['name']} {constraint['type']} ({', '.join(constraint['columns'])}),\n"

        sql = sql.rstrip(",\n") + "\n);"
        return sql
    
    async def get_single_row_data(self, conn: Connection, condition: str):
        """
        Retrieves a single row from the table based on the specified condition.

        Args:
            conn (asyncpg.Connection): The connection object to the PostgreSQL database.
            condition (str): The condition to filter the row (e.g., "user_id='some-uuid'").

        Returns:
            dict: A dictionary representing the row data or None if no row matches.
        """
        query = f'SELECT * FROM {self.schema_name}."{self.table_name}" WHERE {condition} LIMIT 1;'
        
        logger.debug(f'Executing query: {query}')
        
        row = await conn.fetchrow(query)
        return dict(row) if row else None

    async def get_multi_rows_data(self, conn: Connection, condition: str):
        """
        Retrieves multiple rows from the table based on the specified condition.

        Args:
            conn (asyncpg.Connection): The connection object to the PostgreSQL database.
            condition (str): The condition to filter rows (e.g., "admin_flg=true").

        Returns:
            list: A list of dictionaries representing the rows data.
        """
        query = f'SELECT * FROM {self.schema_name}."{self.table_name}" WHERE {condition};'
        
        logger.debug(f'Executing query: {query}')
        
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]

    async def insert_data(self, conn: Connection, values: dict):
        """
        Inserts a new row into the table.

        Args:
            conn (asyncpg.Connection): The connection object to the PostgreSQL database.
            values (dict): A dictionary containing column names and their corresponding values.

        Returns:
            int: The ID of the inserted row or None if insertion failed.
        """
        columns_str = ', '.join(values.keys())
        placeholders_str = ', '.join([f'${i+1}' for i in range(len(values))])
        
        query = f'INSERT INTO {self.schema_name}."{self.table_name}" ({columns_str}) VALUES ({placeholders_str}) RETURNING id;'
        
        logger.debug(f'Executing query: {query}')
        logger.debug(f'With values: {values}')
        
        result = await conn.fetchrow(query, *values.values())
        return result['id'] if result else None

    async def delete_data(self, conn: Connection, condition: str):
        """
        Deletes rows from the table based on the specified condition.

        Args:
            conn (asyncpg.Connection): The connection object to the PostgreSQL database.
            condition (str): The condition to filter which rows to delete.

        Returns:
            int: The number of rows deleted.
        """
        query = f'DELETE FROM {self.schema_name}."{self.table_name}" WHERE {condition};'
        
        logger.debug(f'Executing query: {query}')
        
        result = await conn.execute(query)
        return int(result.split()[1])
    
    async def join_with(self, conn: Connection, other_table: str, join_type: str, on_condition: str):
        """
        Performs a join operation with another table.

        Args:
            conn (asyncpg.Connection): The connection object to the PostgreSQL database.
            other_table (str): The name of the other table to join with.
            join_type (str): The type of join ('LEFT', 'RIGHT', 'INNER', 'FULL').
            on_condition (str): The condition for the join (e.g., "table1.id = table2.id").

        Returns:
            list: A list of dictionaries representing the joined rows.
        """
        query = f'''
            SELECT *
            FROM {self.schema_name}."{self.table_name}" AS t1
            {join_type} JOIN {self.schema_name}."{other_table}" AS t2
            ON {on_condition};
        '''
        
        logger.debug(f'Executing join query: {query}')

        rows = await conn.fetch(query)
        return [dict(row) for row in rows]