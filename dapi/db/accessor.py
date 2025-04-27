from typing import Dict, Optional
from .config import db_config
from .db import DSDatabase


class DatabaseAccessor:
    """
    Provides access to different DesignSafe database connections via properties.
    Manages lazy initialization of DSDatabase instances and connection pools.
    """

    def __init__(self):
        self._connections: Dict[str, Optional[DSDatabase]] = {
            key: None for key in db_config.keys()
        }
        print(
            "DatabaseAccessor initialized. Connections will be created on first access."
        )

    def _get_db(self, dbname: str) -> DSDatabase:
        """Gets or creates a DSDatabase instance (with its engine/pool)."""
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
        """Access the NGL database connection manager."""
        return self._get_db("ngl")

    @property
    def vp(self) -> DSDatabase:
        """Access the VP database connection manager."""
        return self._get_db("vp")

    @property
    def eq(self) -> DSDatabase:
        """Access the EQ database connection manager."""
        return self._get_db("eq")

    def close_all(self):
        """Closes all active database engines and their connection pools."""
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
