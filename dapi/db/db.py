import os
import pandas as pd
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from .config import db_config


class DSDatabase:
    """
    Manages connection and querying for a specific DesignSafe database.
    Uses SQLAlchemy engine for connection pooling and session-per-query pattern.
    """

    def __init__(self, dbname="ngl"):
        """Initializes the DSDatabase instance and creates the engine."""
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
        """
        Executes a SQL query using a dedicated session and returns the results.

        Each call obtains a session (and underlying connection from the pool),
        executes the query, and closes the session (returning the connection
        to the pool).
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
        """Dispose of the engine and its connection pool for this database."""
        if self.engine:
            print(f"Disposing engine and closing pool for '{self.dbname_short}'...")
            self.engine.dispose()
            self.engine = None  # Mark as disposed
            print(f"Engine for '{self.dbname_short}' disposed.")
        else:
            print(f"Engine for '{self.dbname_short}' already disposed.")
