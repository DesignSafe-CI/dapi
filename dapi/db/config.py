"""Database configuration mapping for DesignSafe database connections.

This module defines the mapping between shorthand database names and their
actual database names along with environment variable prefixes used for
connection configuration.

The db_config dictionary maps user-friendly shorthand names to database
configuration details including the actual database name and the prefix
used for environment variables that contain connection credentials.

Example:
    To access the NGL database configuration:
    
    >>> from .config import db_config
    >>> ngl_config = db_config["ngl"]
    >>> print(ngl_config["dbname"])  # "sjbrande_ngl_db"
    >>> print(ngl_config["env_prefix"])  # "NGL_"
    
    Environment variables would be:
    - NGL_DB_USER
    - NGL_DB_PASSWORD  
    - NGL_DB_HOST
    - NGL_DB_PORT
"""

# Mapping of shorthand names to actual database names and environment prefixes
db_config = {
    "ngl": {"dbname": "sjbrande_ngl_db", "env_prefix": "NGL_"},
    "vp": {"dbname": "sjbrande_vpdb", "env_prefix": "VP_"},
    "eq": {"dbname": "post_earthquake_recovery", "env_prefix": "EQ_"},
}
"""dict: Database configuration mapping.

Maps shorthand database names to their configuration details.

Keys:
    - "ngl": Natural hazards engineering research database
    - "vp": Vulnerability and performance database  
    - "eq": Post-earthquake recovery database

Each value contains:
    - "dbname" (str): Actual database name in the MySQL server
    - "env_prefix" (str): Prefix for environment variables containing credentials
    
Environment Variable Pattern:
    For each database, the following environment variables are checked:
    - {env_prefix}DB_USER: Database username (default: "dspublic")
    - {env_prefix}DB_PASSWORD: Database password (default: "R3ad0nlY")
    - {env_prefix}DB_HOST: Database host (default: "129.114.52.174")
    - {env_prefix}DB_PORT: Database port (default: 3306)
"""
