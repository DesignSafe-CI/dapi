import os
import pandas as pd
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from .config import db_config


class DSDatabase:
    """A database utility class for connecting to a DesignSafe SQL database.

    This class provides functionality to connect to a MySQL database using
    SQLAlchemy and PyMySQL. It supports executing SQL queries and returning
    results in different formats.

    Attributes:
        user (str): Database username, defaults to 'dspublic'.
        password (str): Database password, defaults to 'R3ad0nlY'.
        host (str): Database host address, defaults to '129.114.52.174'.
        port (int): Database port, defaults to 3306.
        db (str): Database name, can be 'sjbrande_ngl_db', 'sjbrande_vpdb', or 'post_earthquake_recovery'.
        recycle_time (int): Time in seconds to recycle database connections.
        engine (Engine): SQLAlchemy engine for database connection.
        Session (sessionmaker): SQLAlchemy session maker bound to the engine.
    """

    def __init__(self, dbname="ngl"):
        """Initializes the DSDatabase instance with environment variables and creates the database engine.

        Args:
            dbname (str): Shorthand for the database name. Must be one of 'ngl', 'vp', or 'eq'.
        """

        if dbname not in db_config:
            raise ValueError(
                f"Invalid database shorthand '{dbname}'. Allowed shorthands are: {', '.join(db_config.keys())}"
            )

        config = db_config[dbname]
        env_prefix = config["env_prefix"]

        self.user = os.getenv(f"{env_prefix}DB_USER", "dspublic")
        self.password = os.getenv(f"{env_prefix}DB_PASSWORD", "R3ad0nlY")
        self.host = os.getenv(f"{env_prefix}DB_HOST", "129.114.52.174")
        self.port = os.getenv(f"{env_prefix}DB_PORT", 3306)
        self.db = config["dbname"]

        # Setup the database connection
        self.engine = create_engine(
            f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}",
            pool_recycle=3600,  # 1 hour in seconds
        )
        self.Session = sessionmaker(bind=self.engine)

    def read_sql(self, sql, output_type="DataFrame"):
        """Executes a SQL query and returns the results.

        Args:
            sql (str): The SQL query string to be executed.
            output_type (str, optional): The format for the query results. Defaults to 'DataFrame'.
                Possible values are 'DataFrame' for a pandas DataFrame, or 'dict' for a list of dictionaries.

        Returns:
            pandas.DataFrame or list of dict: The result of the SQL query.

        Raises:
            ValueError: If the SQL query string is empty or if the output type is not valid.
            SQLAlchemyError: If an error occurs during query execution.
        """
        if not sql:
            raise ValueError("SQL query string is required")

        if output_type not in ["DataFrame", "dict"]:
            raise ValueError('Output type must be either "DataFrame" or "dict"')

        session = self.Session()

        try:
            if output_type == "DataFrame":
                return pd.read_sql_query(sql, session.bind)
            else:
                # Convert SQL string to a text object
                sql_text = text(sql)
                result = session.execute(sql_text)
                return [dict(row) for row in result]
        except exc.SQLAlchemyError as e:
            raise Exception(f"SQLAlchemyError: {e}")
        finally:
            session.close()

    def close(self):
        """Close the database connection."""
        self.engine.dispose()
