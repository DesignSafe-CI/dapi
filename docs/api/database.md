# Database

Database connections and query execution for DesignSafe research databases.

## Database Accessor

### `DatabaseAccessor`

```python
class dapi.db.accessor.DatabaseAccessor
```

Provides lazy access to different DesignSafe database connections via properties.

This class manages multiple database connections and provides convenient property-based access to different DesignSafe databases. Each database connection is created only when first accessed (lazy initialization) and reused for subsequent calls.

**Constructor:**

```python
DatabaseAccessor()
```

Initializes the accessor with empty connection slots. No database connections are established until a property is first accessed.

**Properties:**

#### `ngl`

```python
DatabaseAccessor.ngl -> DSDatabase
```

Access the NGL (Natural Hazards Engineering) database connection manager. Provides access to the `sjbrande_ngl_db` database containing natural hazards engineering research data. The connection is created on first access.

#### `vp`

```python
DatabaseAccessor.vp -> DSDatabase
```

Access the VP (Vulnerability and Performance) database connection manager. Provides access to the `sjbrande_vpdb` database containing vulnerability and performance analysis data. The connection is created on first access.

#### `eq`

```python
DatabaseAccessor.eq -> DSDatabase
```

Access the EQ (Post-Earthquake Recovery) database connection manager. Provides access to the `post_earthquake_recovery` database containing post-earthquake recovery research data. The connection is created on first access.

**Methods:**

#### `close_all`

```python
DatabaseAccessor.close_all() -> None
```

Close all active database engines and their connection pools. This should be called when the `DatabaseAccessor` is no longer needed to prevent connection leaks.

After calling `close_all()`, accessing any database property will create new connections since the instances are reset to `None`.

**Example:**

```python
accessor = DatabaseAccessor()

# Access NGL database (created on first access)
ngl_db = accessor.ngl

# Query the database
results = ngl_db.read_sql("SELECT COUNT(*) as total FROM users")

# Close all connections when done
accessor.close_all()
```

---

## Database Engine

### `DSDatabase`

```python
class dapi.db.db.DSDatabase(dbname: str = "ngl")
```

Manages connection and querying for a specific DesignSafe database.

Provides a high-level interface for connecting to preconfigured DesignSafe databases using SQLAlchemy with connection pooling. It supports environment-based configuration and provides query results in multiple formats.

**Constructor Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `dbname` | `str` | `"ngl"` | Shorthand name for the database to connect to. Must be one of `"ngl"`, `"vp"`, or `"eq"`. |

**Raises:**

- `ValueError` -- If `dbname` is not a valid configured database name.
- `SQLAlchemyError` -- If database engine creation or connection fails.

**Attributes:**

| Name | Type | Description |
|------|------|-------------|
| `user` | `str` | Database username for authentication. |
| `password` | `str` | Database password for authentication. |
| `host` | `str` | Database host address. |
| `port` | `int` | Database port number. |
| `db` | `str` | Name of the connected database. |
| `dbname_short` | `str` | Shorthand name for the database. |
| `engine` | `sqlalchemy.Engine` | SQLAlchemy engine for database connections. |
| `Session` | `sqlalchemy.orm.sessionmaker` | Session factory for database operations. |

**Methods:**

#### `read_sql`

```python
DSDatabase.read_sql(sql: str, output_type: str = "DataFrame") -> pd.DataFrame | list[dict]
```

Execute a SQL query using a dedicated session and return the results.

Obtains a session from the connection pool, executes the provided SQL query, and returns results in the specified format. The session is automatically closed after execution, returning the connection to the pool.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `sql` | `str` | *(required)* | The SQL query string to execute. |
| `output_type` | `str` | `"DataFrame"` | Format for query results. Must be `"DataFrame"` for a `pandas.DataFrame` or `"dict"` for a list of dictionaries. |

**Returns:**

- `pandas.DataFrame` when `output_type="DataFrame"` -- a DataFrame with column names as headers.
- `list[dict]` when `output_type="dict"` -- a list of dictionaries where each dict represents a row.

**Raises:**

- `ValueError` -- If `sql` is empty/`None` or `output_type` is not `"DataFrame"` or `"dict"`.
- `SQLAlchemyError` -- If a database error occurs during query execution.

#### `close`

```python
DSDatabase.close() -> None
```

Dispose of the SQLAlchemy engine and close all database connections.

Properly shuts down the database engine and its connection pool. Call this when the database instance is no longer needed to prevent connection leaks and free up database resources.

After calling `close()`, this `DSDatabase` instance should not be used for further database operations as the engine will be disposed.

**Example:**

```python
db = DSDatabase("ngl")
df = db.read_sql("SELECT * FROM table_name LIMIT 5")

# Get dictionary results
results = db.read_sql("SELECT COUNT(*) as total FROM users", output_type="dict")

db.close()
```

---

## Database Configuration

### `db_config`

```python
dapi.db.config.db_config: dict
```

A dictionary mapping shorthand database names to their configuration details.

| Key | Database Name | Env Prefix | Description |
|-----|---------------|------------|-------------|
| `"ngl"` | `sjbrande_ngl_db` | `NGL_` | Natural hazards engineering research database |
| `"vp"` | `sjbrande_vpdb` | `VP_` | Vulnerability and performance database |
| `"eq"` | `post_earthquake_recovery` | `EQ_` | Post-earthquake recovery database |

For each database, the following environment variables are checked (using the env prefix):

- `{PREFIX}DB_USER` -- Database username (default: `"dspublic"`)
- `{PREFIX}DB_PASSWORD` -- Database password (default: `"R3ad0nlY"`)
- `{PREFIX}DB_HOST` -- Database host (default: `"129.114.52.174"`)
- `{PREFIX}DB_PORT` -- Database port (default: `3306`)
