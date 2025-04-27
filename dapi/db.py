import pandas as pd
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
    """
    A database utility class for connecting to a specific DesignSafe SQL database.
    Instantiated by the DSClient with connection details.
    """

    def __init__(self, user, password, host, port, db_name, pool_recycle=3600):
        """
        Initializes the DSDatabase instance with connection details.

        Args:
            user (str): Database username.
            password (str): Database password.
            host (str): Database host address.
            port (int): Database port.
            db_name (str): Specific database name to connect to.
            pool_recycle (int): SQLAlchemy pool recycle time in seconds.
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
        """
        Executes a SQL query and returns the results.

        Args:
            sql (str): The SQL query string to be executed.
            output_type (str, optional): The format for the query results.
                Defaults to 'DataFrame'. Possible values are 'DataFrame' or 'dict'.

        Returns:
            pandas.DataFrame or list[dict]: The result of the SQL query.

        Raises:
            ValueError: If the SQL query string is empty or output type is invalid.
            DapiException: If a database error occurs during query execution.
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
        """Dispose of the SQLAlchemy engine connection pool."""
        if hasattr(self, "engine") and self.engine:
            print(f"Closing connection pool for database '{self.db_name}'.")
            self.engine.dispose()

    def __repr__(self):
        return f"<DSDatabase(db='{self.db_name}')>"
