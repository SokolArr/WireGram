# Documentation for `db_manager.py`

## Overview

The `db_manager.py` module provides a class `DbManager` that facilitates interaction with a PostgreSQL database using the `asyncpg` library. It includes methods for building SQL queries for selecting and inserting data, as well as executing those queries asynchronously.

## Class: `DbManager`

### Attributes

- **`__default_db_conn_params`**: A dictionary containing default database connection parameters.
  - `db_name`: Name of the database (default: `'db'`)
  - `db_user`: Username for database connection (default: `'admin'`)
  - `db_password`: Password for database connection (default: `'12345678'`)
  - `db_host`: Host where the database is located (default: `'localhost'`)
  - `db_port`: Port for database connection (default: `'2345'`)

- **`__main_schema_name`**: Default schema name used in queries (default: `'main'`).

### Constructor
def init(self, db_conn_params: dict = __default_db_conn_params, schema_name: str = __main_schema_name)

- **Parameters**:
  - `db_conn_params`: A dictionary of database connection parameters. If not provided, defaults will be used.
  - `schema_name`: The schema to be used in queries. Defaults to the main schema.

### Methods

#### 1. `async select_query_builder(columns: list = ['1'], table: str = None, schema: str = __main_schema_name, condition: str = None, limit: int = None) -> str`

Builds a SQL SELECT query based on provided parameters.

- **Parameters**:
  - `columns`: A list of columns to select. Defaults to `['1']`.
  - `table`: The name of the table to select from.
  - `schema`: The schema name. Defaults to the main schema.
  - `condition`: Optional SQL condition for the WHERE clause.
  - `limit`: Optional limit on the number of results returned.

- **Returns**: A string containing the constructed SQL SELECT query.

#### 2. `async insert_query_builder(self, table: str, vals: list[tuple] = None, insert_type: str = 'values', columns: list = None, schema: str = __main_schema_name, **kwargs) -> str`

Builds a SQL INSERT query based on provided parameters.

- **Parameters**:
  - `table`: The name of the table to insert into.
  - `vals`: A list of tuples containing values to insert.
  - `insert_type`: Type of insert operation (`'values'` or `'select'`). Defaults to `'values'`.
  - `columns`: Optional list of columns for the insert operation.
  - `schema`: The schema name. Defaults to the main schema.
  - Additional keyword arguments for select queries (`sel_columns`, `sel_table`, etc.).

- **Returns**: A string containing the constructed SQL INSERT query or an empty string if an error occurs.

#### 3. `async _get_conn(self) -> asyncpg.Connection`

Establishes a connection to the PostgreSQL database using the provided connection parameters.

- **Returns**: An instance of `asyncpg.Connection`.

#### 4. `async fetch_data(self, columns: list = ['1'], schema: str = __main_schema_name, table: str = None, condition: str = None, limit: int = None) -> list[asyncpg.Record]`

Fetches data from the specified table and returns it as a list of records.

- **Parameters**:
  - `columns`: A list of columns to select. Defaults to `['1']`.
  - `schema`: The schema name. Defaults to the main schema.
  - `table`: The name of the table to fetch from.
  - `condition`: Optional SQL condition for the WHERE clause.
  - `limit`: Optional limit on the number of results returned.

- **Returns**: A list of records fetched from the database or an empty list if an error occurs.

#### 5. `async ins_data(self, table: str, vals: list[tuple]= None, insert_type: str = 'values', columns: list = None, schema: str = __main_schema_name, sel_columns: list = None, sel_table: str = None, sel_schema: str = None, sel_condition: str= None, sel_limit: int = None) -> int`

Inserts data into the specified table based on provided parameters.

- **Parameters**:
  - Same as those in the insert query builder method with additional parameters for select-based inserts.

- **Returns**: An integer indicating success (0) or failure (-1).

### Logging

The module uses Python's built-in logging library to log debug and error messages throughout its methods. Ensure that logging is configured appropriately in your application to capture these logs.