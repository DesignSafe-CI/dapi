"""DesignSafe database connection and query management.

This module provides the DSDatabase class for connecting to and querying
specific DesignSafe databases using SQLAlchemy with connection pooling.
It supports multiple preconfigured databases and provides both DataFrame
and dictionary output formats for query results.

Dependencies:
    - SQLAlchemy: For database engine and ORM functionality
    - PyMySQL: MySQL database driver
    - pandas: For DataFrame output format

Example:
    >>> db = DSDatabase("ngl")
    Creating SQLAlchemy engine for database 'sjbrande_ngl_db' (ngl)...
    Engine for 'ngl' created.
    
    >>> df = db.read_sql("SELECT * FROM table_name LIMIT 5")
    >>> db.close()
"""

import os
import pandas as pd
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from .config import db_config


class DSDatabase:
    """Manages connection and querying for a specific DesignSafe database.

    This class provides a high-level interface for connecting to preconfigured
    DesignSafe databases using SQLAlchemy with connection pooling. It supports
    environment-based configuration and provides query results in multiple formats.

    Attributes:
        user (str): Database username for authentication.
        password (str): Database password for authentication.
        host (str): Database host address.
        port (int): Database port number.
        db (str): Name of the connected database.
        dbname_short (str): Shorthand name for the database.
        engine (sqlalchemy.Engine): SQLAlchemy engine for database connections.
        Session (sqlalchemy.orm.sessionmaker): Session factory for database operations.

    Example:
        >>> db = DSDatabase("ngl")
        >>> df = db.read_sql("SELECT COUNT(*) as total FROM users")
        >>> print(df.iloc[0]['total'])
        >>> db.close()
    """

    def __init__(self, dbname="ngl"):
        """Initialize the DSDatabase instance and create the SQLAlchemy engine.

        Sets up database connection parameters from environment variables or defaults,
        creates a SQLAlchemy engine with connection pooling, and prepares the session factory.

        Args:
            dbname (str, optional): Shorthand name for the database to connect to.
                Must be a key in db_config. Defaults to "ngl".
                Available options: "ngl", "vp", "eq".

        Raises:
            ValueError: If dbname is not a valid configured database name.
            SQLAlchemyError: If database engine creation or connection fails.

        Example:
            >>> db = DSDatabase("ngl")  # Connect to NGL database
            >>> db = DSDatabase("vp")   # Connect to VP database
        """
        if dbname not in db_config:
            raise ValueError(
                f"Invalid db shorthand '{dbname}'. Allowed: {', '.join(db_config.keys())}"
            )

        config = db_config[dbname]
        env_prefix = config["env_prefix"]

        self.user = os.getenv(f"{env_prefix}DB_USER", "dspublic")
        self.password = os.getenv(f"{env_prefix}DB_PASSWORD", "R3ad0nlY")
        self.host = os.getenv(f"{env_prefix}DB_HOST", "129.114.52.174")
        self.port = os.getenv(f"{env_prefix}DB_PORT", 3306)
        self.db = config["dbname"]
        self.dbname_short = dbname  # Store shorthand name for reference

        print(
            f"Creating SQLAlchemy engine for database '{self.db}' ({self.dbname_short})..."
        )
        # Setup the database connection engine with pooling
        self.engine = create_engine(
            f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}",
            pool_recycle=3600,  # Recycle connections older than 1 hour
            pool_pre_ping=True,  # Check connection validity before use
        )
        # Create a configured "Session" class
        self.Session = sessionmaker(bind=self.engine)
        print(f"Engine for '{self.dbname_short}' created.")

    def read_sql(self, sql, output_type="DataFrame"):
        """Execute a SQL query using a dedicated session and return the results.

        This method obtains a session from the connection pool, executes the provided
        SQL query, and returns results in the specified format. The session is
        automatically closed after execution, returning the connection to the pool.

        Args:
            sql (str): The SQL query string to execute. Can be any valid SQL
                statement including SELECT, INSERT, UPDATE, DELETE, etc.
            output_type (str, optional): Format for query results. Must be either
                'DataFrame' for pandas.DataFrame or 'dict' for list of dictionaries.
                Defaults to "DataFrame".

        Returns:
            pandas.DataFrame or List[Dict]: Query results in the requested format.
                - 'DataFrame': Returns a pandas DataFrame with column names as headers
                - 'dict': Returns a list of dictionaries where each dict represents a row

        Raises:
            ValueError: If sql is empty/None or output_type is not 'DataFrame' or 'dict'.
            SQLAlchemyError: If database error occurs during query execution.
            Exception: If unexpected errors occur during query processing.

        Example:
            >>> # Get DataFrame result
            >>> df = db.read_sql("SELECT name, age FROM users WHERE age > 25")
            >>> print(df.columns.tolist())  # ['name', 'age']

            >>> # Get dictionary result
            >>> results = db.read_sql("SELECT COUNT(*) as total FROM users", output_type="dict")
            >>> print(results[0]['total'])  # 150
        """
        if not sql:
            raise ValueError("SQL query string is required")
        if output_type not in ["DataFrame", "dict"]:
            raise ValueError('Output type must be either "DataFrame" or "dict"')

        # Obtain a new session for this query
        session = self.Session()
        print(f"Executing query on '{self.dbname_short}'...")
        try:
            if output_type == "DataFrame":
                # pandas read_sql_query handles connection/session management implicitly sometimes,
                # but using the session explicitly ensures consistency.
                # Pass the engine bound to the session.
                return pd.read_sql_query(
                    sql, session.bind.connect()
                )  # Get connection from engine
            else:
                sql_text = text(sql)
                # Execute within the session context
                result = session.execute(sql_text)
                # Fetch results before closing session
                data = [
                    dict(row._mapping) for row in result
                ]  # Use ._mapping for modern SQLAlchemy
                return data
        except exc.SQLAlchemyError as e:
            print(f"SQLAlchemyError executing query on '{self.dbname_short}': {e}")
            raise  # Re-raise the exception
        except Exception as e:
            print(f"Unexpected error executing query on '{self.dbname_short}': {e}")
            raise
        finally:
            # Ensure the session is closed, returning the connection to the pool
            session.close()
            # print(f"Session for '{self.dbname_short}' query closed.") # Can be noisy

    def close(self):
        """Dispose of the SQLAlchemy engine and close all database connections.

        This method properly shuts down the database engine and its connection pool.
        It should be called when the database instance is no longer needed to
        prevent connection leaks and free up database resources.

        Note:
            After calling close(), this DSDatabase instance should not be used
            for further database operations as the engine will be disposed.

        Example:
            >>> db = DSDatabase("ngl")
            >>> # ... perform database operations ...
            >>> db.close()
            Disposing engine and closing pool for 'ngl'...
            Engine for 'ngl' disposed.
        """
        if self.engine:
            print(f"Disposing engine and closing pool for '{self.dbname_short}'...")
            self.engine.dispose()
            self.engine = None  # Mark as disposed
            print(f"Engine for '{self.dbname_short}' disposed.")
        else:
            print(f"Engine for '{self.dbname_short}' already disposed.")
