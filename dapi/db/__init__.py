"""DesignSafe database package initialization.

This package provides database connectivity and utilities for accessing
DesignSafe-specific SQL databases. It includes the main DSDatabase class
for database connections and query execution.

Attributes:
    name (str): Package name identifier for the DesignSafe database module.

Example:
    >>> from dapi.db import DSDatabase
    >>> db = DSDatabase("ngl")
    >>> results = db.read_sql("SELECT * FROM table_name LIMIT 5")
"""

from .db import DSDatabase as DSDatabase

name = "designsafe_db"
