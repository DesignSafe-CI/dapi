"""Database utilities for connecting to DesignSafe SQL databases.

This module provides the DSDatabase class for connecting to and querying
DesignSafe-specific SQL databases. It handles optional dependencies gracefully
and provides a pandas-friendly interface for data analysis.

Dependencies:
    - SQLAlchemy: Required for database connections
    - PyMySQL: Required for MySQL database driver
    - pandas: Required for DataFrame output format

Example:
    >>> db = DSDatabase("dspublic", "password", "host", 3306, "database_name")
    >>> df = db.read_sql("SELECT * FROM table_name LIMIT 10")
    >>> db.close()
"""

import pandas as pd
from typing import Any
from .exceptions import DapiException  # Use base dapi exception

# --- Database Dependencies Check ---
try:
    from sqlalchemy import create_engine, exc, text
    from sqlalchemy.orm import sessionmaker

    _SQLALCHEMY_FOUND = True
except ImportError:
    _SQLALCHEMY_FOUND = False

    # Define dummy classes/functions if sqlalchemy is missing,
    # so the client can still load but DB access will fail clearly.
    class exc:  # Dummy class
        class SQLAlchemyError(Exception):
            pass

    def create_engine(*args, **kwargs):
        raise ImportError(
            "SQLAlchemy not found. Install with 'pip install SQLAlchemy PyMySQL pandas'"
        )

    def sessionmaker(*args, **kwargs):
        raise ImportError(
            "SQLAlchemy not found. Install with 'pip install SQLAlchemy PyMySQL pandas'"
        )

    def text(s):
        return s  # Return string if no text object


# --- DSDatabase Class ---
class DSDatabase:
    """A database utility class for connecting to and querying DesignSafe SQL databases.

    This class manages database connections using SQLAlchemy with connection pooling
    and provides methods for executing SQL queries with results returned as pandas
    DataFrames or Python dictionaries.

    Attributes:
        db_name (str): Name of the connected database.
        connection_string (str): SQLAlchemy connection string.
        engine (sqlalchemy.Engine): SQLAlchemy engine for database connections.
        Session (sqlalchemy.orm.sessionmaker): Session factory for database operations.

    Example:
        >>> db = DSDatabase("user", "pass", "localhost", 3306, "mydb")
        Successfully connected to database 'mydb' on localhost.

        >>> df = db.read_sql("SELECT * FROM users LIMIT 5")
        >>> print(df.head())

        >>> results = db.read_sql("SELECT count(*) as total FROM users", output_type="dict")
        >>> print(results[0]['total'])

        >>> db.close()
        Closing connection pool for database 'mydb'.
    """

    def __init__(self, user, password, host, port, db_name, pool_recycle=3600):
        """Initialize the DSDatabase instance with connection details.

        Creates a SQLAlchemy engine with connection pooling and tests the
        connection immediately upon initialization.

        Args:
            user (str): Database username for authentication.
            password (str): Database password for authentication.
            host (str): Database host address (IP or hostname).
            port (int): Database port number (typically 3306 for MySQL).
            db_name (str): Name of the specific database to connect to.
            pool_recycle (int, optional): Time in seconds after which a connection
                is recycled to prevent timeouts. Defaults to 3600 (1 hour).

        Raises:
            ImportError: If required database dependencies (SQLAlchemy, PyMySQL) are not installed.
            DapiException: If database connection fails or if connection parameters are invalid.

        Example:
            >>> db = DSDatabase("myuser", "mypass", "db.example.com", 3306, "research_db")
            Successfully connected to database 'research_db' on db.example.com.
        """
        if not _SQLALCHEMY_FOUND:
            raise ImportError(
                "Database functionality requires SQLAlchemy, PyMySQL, and pandas. Install with 'pip install SQLAlchemy PyMySQL pandas'"
            )

        self.db_name = db_name
        self.connection_string = (
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
        )

        try:
            # Setup the database connection
            self.engine = create_engine(
                self.connection_string,
                pool_recycle=pool_recycle,
            )
            # Test connection immediately (optional but recommended)
            with self.engine.connect() as connection:
                print(f"Successfully connected to database '{db_name}' on {host}.")
            self.Session = sessionmaker(bind=self.engine)
        except exc.SQLAlchemyError as e:
            # Provide more context in case of connection errors
            raise DapiException(
                f"Failed to connect to database '{db_name}' at {host}:{port}. Error: {e}"
            ) from e
        except ImportError as e:
            # Catch potential PyMySQL import error if create_engine fails due to it
            if "pymysql" in str(e).lower():
                raise ImportError(
                    "Database functionality requires PyMySQL. Install with 'pip install PyMySQL'"
                ) from e
            raise  # Re-raise other import errors

    def read_sql(self, sql: str, output_type: str = "DataFrame") -> Any:
        """Execute a SQL query and return the results in the specified format.

        This method handles both SELECT queries for data retrieval and other SQL
        statements. It manages database sessions automatically and provides
        results in either pandas DataFrame or Python dictionary format.

        Args:
            sql (str): The SQL query string to execute. Can be any valid SQL
                statement including SELECT, INSERT, UPDATE, DELETE, etc.
            output_type (str, optional): Format for query results. Must be either
                'DataFrame' for pandas.DataFrame or 'dict' for list of dictionaries.
                Defaults to 'DataFrame'.

        Returns:
            pandas.DataFrame or List[Dict]: Query results in the requested format.
                - 'DataFrame': Returns a pandas DataFrame with column names as headers
                - 'dict': Returns a list of dictionaries where each dict represents a row

        Raises:
            ImportError: If required database dependencies are not available.
            ValueError: If sql is empty/None or output_type is not 'DataFrame' or 'dict'.
            DapiException: If database error occurs during query execution or
                if unexpected errors occur during processing.

        Example:
            >>> # Get DataFrame result
            >>> df = db.read_sql("SELECT name, age FROM users WHERE age > 25")
            >>> print(df.columns.tolist())  # ['name', 'age']

            >>> # Get dictionary result
            >>> results = db.read_sql("SELECT COUNT(*) as total FROM users", output_type="dict")
            >>> print(results[0]['total'])  # 150

            >>> # Complex query with joins
            >>> query = '''
            ... SELECT u.name, p.project_name
            ... FROM users u
            ... JOIN projects p ON u.id = p.user_id
            ... WHERE p.status = 'active'
            ... '''
            >>> df = db.read_sql(query)
        """
        if not _SQLALCHEMY_FOUND:
            raise ImportError(
                "Database functionality requires SQLAlchemy, PyMySQL, and pandas. Install with 'pip install SQLAlchemy PyMySQL pandas'"
            )
        if not sql:
            raise ValueError("SQL query string is required")
        if output_type not in ["DataFrame", "dict"]:
            raise ValueError('Output type must be either "DataFrame" or "dict"')

        session = self.Session()
        try:
            sql_text = text(sql)  # Ensure SQL is treated as literal SQL
            if output_type == "DataFrame":
                # Use pandas directly with the engine for simplicity
                return pd.read_sql_query(sql_text, self.engine)
            else:
                # Execute using session for list of dicts
                result = session.execute(sql_text)
                # Use .mappings().all() for easy conversion to list of dicts
                return result.mappings().all()
        except exc.SQLAlchemyError as e:
            raise DapiException(
                f"Error executing SQL query on database '{self.db_name}'. Error: {e}"
            ) from e
        except Exception as e:
            # Catch other potential errors (like pandas issues)
            raise DapiException(
                f"An unexpected error occurred during SQL query execution: {e}"
            ) from e
        finally:
            session.close()

    def close(self):
        """Dispose of the SQLAlchemy engine and close all database connections.

        This method should be called when the database instance is no longer needed
        to properly clean up database connections and prevent connection leaks.

        Note:
            After calling close(), this DSDatabase instance should not be used
            for further database operations as the engine will be disposed.

        Example:
            >>> db = DSDatabase(...)
            >>> # ... perform database operations ...
            >>> db.close()
            Closing connection pool for database 'mydb'.
        """
        if hasattr(self, "engine") and self.engine:
            print(f"Closing connection pool for database '{self.db_name}'.")
            self.engine.dispose()

    def __repr__(self):
        """Return a string representation of the DSDatabase instance.

        Returns:
            str: String representation showing the database name.

        Example:
            >>> db = DSDatabase("user", "pass", "host", 3306, "research_db")
            >>> print(repr(db))
            <DSDatabase(db='research_db')>
        """
        return f"<DSDatabase(db='{self.db_name}')>"
