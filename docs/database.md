# Database Access

dapi connects to three DesignSafe research databases:

| Database | Code | Domain |
|----------|------|--------|
| NGL | `ngl` | Geotechnical / Liquefaction |
| Earthquake Recovery | `eq` | Social / Economic impacts |
| VP | `vp` | Model validation |

## Quick Start

```python
from dapi import DSClient

ds = DSClient()

df = ds.db.ngl.read_sql("SELECT * FROM SITE LIMIT 5")
print(df)

# Parameterized query
site_data = ds.db.ngl.read_sql(
 "SELECT * FROM SITE WHERE SITE_NAME = %s",
 params=["Amagasaki"]
)
```

## Authentication

Database connections use built-in public read-only credentials by default -- no setup required.

To override (e.g., for a private database instance), set environment variables:

```bash
# NGL Database
export NGL_DB_USER="dspublic"
export NGL_DB_PASSWORD="your_password"
export NGL_DB_HOST="database_host"
export NGL_DB_PORT="3306"
```

Same pattern for VP (`VP_DB_*`) and Earthquake Recovery (`EQ_DB_*`).

## Querying

### Basic Queries

```python
count_df = ds.db.ngl.read_sql("SELECT COUNT(*) as total_sites FROM SITE")
print(f"Total sites: {count_df['total_sites'].iloc[0]}")

sites_df = ds.db.ngl.read_sql("SELECT * FROM SITE LIMIT 10")

site_info = ds.db.ngl.read_sql("""
 SELECT SITE_NAME, SITE_LAT, SITE_LON, SITE_GEOL
 FROM SITE
 WHERE SITE_LAT > 35
 ORDER BY SITE_NAME
""")
```

### Parameterized Queries

```python
# Single parameter
site_data = ds.db.ngl.read_sql(
 "SELECT * FROM SITE WHERE SITE_NAME = %s",
 params=[site_name]
)

# Multiple parameters
california_sites = ds.db.ngl.read_sql(
 "SELECT * FROM SITE WHERE SITE_LAT BETWEEN %s AND %s",
 params=[32.0, 38.0]
)

# Named parameters
region_sites = ds.db.ngl.read_sql(
 "SELECT * FROM SITE WHERE SITE_LAT > %(min_lat)s AND SITE_LON < %(max_lon)s",
 params={"min_lat": 35.0, "max_lon": -115.0}
)
```

## NGL Database (Next Generation Liquefaction)

### Exploring Tables

```python
tables_info = ds.db.ngl.read_sql("SHOW TABLES")
print(tables_info)

site_structure = ds.db.ngl.read_sql("DESCRIBE SITE")
print(site_structure)
```

### Example Queries

```python
# Active sites
sites = ds.db.ngl.read_sql("""
 SELECT SITE_ID, SITE_NAME, SITE_LAT, SITE_LON, SITE_GEOL
 FROM SITE
 WHERE SITE_STAT = 1
 ORDER BY SITE_NAME
""")

# Sites with liquefaction data
liquefaction_sites = ds.db.ngl.read_sql("""
 SELECT DISTINCT s.SITE_NAME, s.SITE_LAT, s.SITE_LON
 FROM SITE s
 JOIN RECORD r ON s.SITE_ID = r.SITE_ID
 WHERE r.RECORD_STAT = 1
 ORDER BY s.SITE_NAME
""")

# Recent earthquakes
earthquakes = ds.db.ngl.read_sql("""
 SELECT DISTINCT EVENT_NAME, EVENT_DATE, EVENT_MAG
 FROM EVENT
 WHERE EVENT_STAT = 1
 ORDER BY EVENT_DATE DESC
 LIMIT 20
""")

# CPT data summary
cpt_summary = ds.db.ngl.read_sql("""
 SELECT
 COUNT(*) as total_cpts,
 AVG(CPT_DEPTH) as avg_depth,
 MIN(CPT_DEPTH) as min_depth,
 MAX(CPT_DEPTH) as max_depth
 FROM CPT
 WHERE CPT_STAT = 1
""")
```

### Joins

```python
# Sites with multiple liquefaction events
high_risk_sites = ds.db.ngl.read_sql("""
 SELECT
 s.SITE_NAME,
 s.SITE_LAT,
 s.SITE_LON,
 COUNT(l.LIQ_ID) as liquefaction_events,
 AVG(e.EVENT_MAG) as avg_magnitude
 FROM SITE s
 JOIN RECORD r ON s.SITE_ID = r.SITE_ID
 JOIN LIQUEFACTION l ON r.RECORD_ID = l.RECORD_ID
 JOIN EVENT e ON r.EVENT_ID = e.EVENT_ID
 WHERE s.SITE_STAT = 1 AND r.RECORD_STAT = 1
 GROUP BY s.SITE_ID
 HAVING liquefaction_events > 2
 ORDER BY liquefaction_events DESC, avg_magnitude DESC
""")
```

## Earthquake Recovery Database

```python
recovery_data = ds.db.eq.read_sql("""
 SELECT
 event_name,
 recovery_metric,
 recovery_time_days,
 affected_population
 FROM recovery_metrics
 WHERE recovery_time_days IS NOT NULL
 ORDER BY event_name, recovery_time_days
""")
```

## VP Database (Validation Portal)

```python
model_performance = ds.db.vp.read_sql("""
 SELECT
 model_name,
 benchmark_case,
 rmse_error,
 correlation_coefficient,
 validation_score
 FROM model_validation
 WHERE validation_score IS NOT NULL
 ORDER BY validation_score DESC
""")
```

## Export

```python
df = ds.db.ngl.read_sql("""
 SELECT s.SITE_NAME, s.SITE_LAT, s.SITE_LON, e.EVENT_NAME, e.EVENT_MAG
 FROM SITE s
 JOIN RECORD r ON s.SITE_ID = r.SITE_ID
 JOIN EVENT e ON r.EVENT_ID = e.EVENT_ID
 WHERE s.SITE_STAT = 1 AND r.RECORD_STAT = 1
""")

df.to_csv("ngl_data.csv", index=False)
df.to_excel("ngl_data.xlsx", index=False)
df.to_json("ngl_data.json", orient="records")

# GeoJSON (requires geopandas)
import geopandas as gpd
from shapely.geometry import Point

geometry = [Point(xy) for xy in zip(df['SITE_LON'], df['SITE_LAT'])]
gdf = gpd.GeoDataFrame(df, geometry=geometry)
gdf.to_file("ngl_sites.geojson", driver="GeoJSON")
```

## Connection Management

```python
ngl_db = ds.db.ngl

# Check connection
try:
 test_query = ngl_db.read_sql("SELECT 1 as test")
 print("Connection active")
except Exception as e:
 print(f"Connection failed: {e}")

# Close (optional -- handled automatically)
ngl_db.close()
```

## Best Practices

### Use Parameterized Queries
```python
# Safe
ds.db.ngl.read_sql("SELECT * FROM SITE WHERE SITE_NAME = %s", params=[user_input])

# Unsafe -- SQL injection risk
ds.db.ngl.read_sql(f"SELECT * FROM SITE WHERE SITE_NAME = '{user_input}'")
```

### Limit Result Sets
```python
# Use LIMIT for large tables
ds.db.ngl.read_sql("SELECT * FROM LARGE_TABLE LIMIT 1000")

# Pagination for very large datasets
offset = 0
batch_size = 1000
while True:
 batch = ds.db.ngl.read_sql(
 "SELECT * FROM LARGE_TABLE LIMIT %s OFFSET %s",
 params=[batch_size, offset]
 )
 if batch.empty:
 break
 offset += batch_size
```

## Error Handling

```python
try:
 df = ds.db.ngl.read_sql("SELECT * FROM SITE LIMIT 5")
except Exception as e:
 print(f"Database error: {e}")

 import os
 required_vars = ['NGL_DB_USER', 'NGL_DB_PASSWORD', 'NGL_DB_HOST', 'NGL_DB_PORT']
 missing_vars = [var for var in required_vars if not os.getenv(var)]

 if missing_vars:
 print(f"Missing environment variables: {missing_vars}")
```
