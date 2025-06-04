"""Database accessor for managing multiple DesignSafe database connections.

This module provides the DatabaseAccessor class which manages lazy initialization
and access to multiple DesignSafe database connections through property-based
interfaces. It handles connection pooling and provides convenient access to
different database instances.

Example:
    >>> accessor = DatabaseAccessor()
    >>> ngl_db = accessor.ngl
    >>> df = ngl_db.read_sql("SELECT * FROM table_name LIMIT 5")
    >>> accessor.close_all()
"""

from typing import Dict, Optional
from .config import db_config
from .db import DSDatabase


class DatabaseAccessor:
    """Provides lazy access to different DesignSafe database connections via properties.

    This class manages multiple database connections and provides convenient property-based
    access to different DesignSafe databases. Each database connection is created only when
    first accessed (lazy initialization) and reused for subsequent calls.

    The accessor supports the following databases through properties:
    - ngl: Natural hazards engineering research database
    - vp: Vulnerability and performance database
    - eq: Post-earthquake recovery database

    Attributes:
        _connections (Dict[str, Optional[DSDatabase]]): Internal storage for database instances.

    Example:
        >>> accessor = DatabaseAccessor()
        DatabaseAccessor initialized. Connections will be created on first access.

        >>> # Access NGL database (created on first access)
        >>> ngl_db = accessor.ngl
        First access to 'ngl', initializing DSDatabase...
        Successfully connected to database 'sjbrande_ngl_db' on 129.114.52.174.

        >>> # Query the database
        >>> results = ngl_db.read_sql("SELECT COUNT(*) as total FROM users")

        >>> # Close all connections when done
        >>> accessor.close_all()
        Closing all active database engines/pools...
        Closed 1 database engine(s).
    """

    def __init__(self):
        """Initialize the DatabaseAccessor with empty connection slots.

        Creates a dictionary to hold database connections for each configured
        database, but does not establish any connections until they are first accessed.
        """
        self._connections: Dict[str, Optional[DSDatabase]] = {
            key: None for key in db_config.keys()
        }
        print(
            "DatabaseAccessor initialized. Connections will be created on first access."
        )

    def _get_db(self, dbname: str) -> DSDatabase:
        """Get or create a DSDatabase instance with lazy initialization.

        This internal method handles the lazy initialization of database connections.
        If a connection for the specified database doesn't exist, it creates a new
        DSDatabase instance. If creation fails, the connection slot remains None.

        Args:
            dbname (str): Shorthand database name (must be a key in db_config).

        Returns:
            DSDatabase: An initialized and connected DSDatabase instance.

        Raises:
            ValueError: If dbname is not a valid configured database name.
            Exception: Re-raises any exception that occurs during database initialization.
        """
        if dbname not in self._connections:
            raise ValueError(
                f"Invalid db shorthand '{dbname}'. Allowed: {', '.join(self._connections.keys())}"
            )

        if self._connections[dbname] is None:
            print(f"First access to '{dbname}', initializing DSDatabase...")
            try:
                self._connections[dbname] = DSDatabase(dbname=dbname)
            except Exception as e:
                self._connections[dbname] = None
                print(f"Error initializing database '{dbname}': {e}")
                raise
        # Type hint assertion
        return self._connections[dbname]  # type: ignore

    @property
    def ngl(self) -> DSDatabase:
        """Access the NGL (Natural Hazards Engineering) database connection manager.

        Provides access to the sjbrande_ngl_db database containing natural hazards
        engineering research data. The connection is created on first access.

        Returns:
            DSDatabase: Connected database instance for the NGL database.

        Raises:
            Exception: If database connection fails during initialization.

        Example:
            >>> ngl_db = accessor.ngl
            >>> df = ngl_db.read_sql("SELECT * FROM earthquake_data LIMIT 10")
        """
        return self._get_db("ngl")

    @property
    def vp(self) -> DSDatabase:
        """Access the VP (Vulnerability and Performance) database connection manager.

        Provides access to the sjbrande_vpdb database containing vulnerability
        and performance analysis data. The connection is created on first access.

        Returns:
            DSDatabase: Connected database instance for the VP database.

        Raises:
            Exception: If database connection fails during initialization.

        Example:
            >>> vp_db = accessor.vp
            >>> df = vp_db.read_sql("SELECT * FROM vulnerability_models LIMIT 10")
        """
        return self._get_db("vp")

    @property
    def eq(self) -> DSDatabase:
        """Access the EQ (Post-Earthquake Recovery) database connection manager.

        Provides access to the post_earthquake_recovery database containing
        post-earthquake recovery research data. The connection is created on first access.

        Returns:
            DSDatabase: Connected database instance for the EQ database.

        Raises:
            Exception: If database connection fails during initialization.

        Example:
            >>> eq_db = accessor.eq
            >>> df = eq_db.read_sql("SELECT * FROM recovery_metrics LIMIT 10")
        """
        return self._get_db("eq")

    def close_all(self):
        """Close all active database engines and their connection pools.

        This method iterates through all database connections and properly closes
        their SQLAlchemy engines and connection pools. This should be called when
        the DatabaseAccessor is no longer needed to prevent connection leaks.

        Note:
            After calling close_all(), accessing any database property will create
            new connections since the instances are reset to None.

        Example:
            >>> accessor = DatabaseAccessor()
            >>> ngl_db = accessor.ngl  # Creates connection
            >>> vp_db = accessor.vp    # Creates connection
            >>> accessor.close_all()   # Closes both connections
            Closing all active database engines/pools...
            Closing connection pool for database 'sjbrande_ngl_db'.
            Closing connection pool for database 'sjbrande_vpdb'.
            Closed 2 database engine(s).
        """
        print("Closing all active database engines/pools...")
        closed_count = 0
        for dbname, db_instance in self._connections.items():
            if db_instance is not None:
                try:
                    # Call the close method on the DSDatabase instance
                    db_instance.close()
                    self._connections[
                        dbname
                    ] = None  # Clear instance after closing engine
                    closed_count += 1
                except Exception as e:
                    print(f"Error closing engine for '{dbname}': {e}")
        if closed_count == 0:
            print("No active database engines to close.")
        else:
            print(f"Closed {closed_count} database engine(s).")
