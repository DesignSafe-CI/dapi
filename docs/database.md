# Database Access

This guide covers how to access and query DesignSafe research databases using dapi. DesignSafe provides access to several important research databases for earthquake engineering, geotechnical engineering, and natural hazards research.

## 🗄️ Available Databases

dapi provides access to three major research databases:

| Database | Code | Description | Domain |
|----------|------|-------------|---------|
| **NGL** | `ngl` | Next Generation Liquefaction database | Geotechnical/Liquefaction |
| **Earthquake Recovery** | `eq` | Post-earthquake recovery database | Social/Economic impacts |  
| **VP** | `vp` | Validation Portal database | Model validation |

## 🚀 Quick Start

```python
from dapi import DSClient

# Initialize client
client = DSClient()

# Query NGL database
df = client.db.ngl.read_sql("SELECT * FROM SITE LIMIT 5")
print(df)

# Query with parameters
site_data = client.db.ngl.read_sql(
    "SELECT * FROM SITE WHERE SITE_NAME = %s",
    params=["Amagasaki"]
)
print(site_data)
```

## 🔐 Database Authentication

### Environment Variables

Database access requires additional authentication. Set these environment variables:

```bash
# NGL Database
export NGL_DB_USER="dspublic"
export NGL_DB_PASSWORD="your_password"
export NGL_DB_HOST="database_host"
export NGL_DB_PORT="3306"

# VP Database  
export VP_DB_USER="dspublic"
export VP_DB_PASSWORD="your_password"
export VP_DB_HOST="database_host"
export VP_DB_PORT="3306"

# Earthquake Recovery Database
export EQ_DB_USER="dspublic"
export EQ_DB_PASSWORD="your_password"
export EQ_DB_HOST="database_host"
export EQ_DB_PORT="3306"
```

### Using .env Files

Create a `.env` file in your project:

```bash
# .env file
DESIGNSAFE_USERNAME=your_username
DESIGNSAFE_PASSWORD=your_password

# Database credentials
NGL_DB_USER=dspublic
NGL_DB_PASSWORD=your_db_password
NGL_DB_HOST=database_host
NGL_DB_PORT=3306

VP_DB_USER=dspublic
VP_DB_PASSWORD=your_db_password
VP_DB_HOST=database_host
VP_DB_PORT=3306

EQ_DB_USER=dspublic
EQ_DB_PASSWORD=your_db_password
EQ_DB_HOST=database_host
EQ_DB_PORT=3306
```

## 📊 Basic Querying

### Simple Queries

```python
from dapi import DSClient

client = DSClient()

# Count records in NGL database
count_df = client.db.ngl.read_sql("SELECT COUNT(*) as total_sites FROM SITE")
print(f"Total sites: {count_df['total_sites'].iloc[0]}")

# Get first 10 sites
sites_df = client.db.ngl.read_sql("SELECT * FROM SITE LIMIT 10")
print(sites_df)

# Get site information
site_info = client.db.ngl.read_sql("""
    SELECT SITE_NAME, SITE_LAT, SITE_LON, SITE_GEOL 
    FROM SITE 
    WHERE SITE_LAT > 35 
    ORDER BY SITE_NAME
""")
print(site_info)
```

### Parameterized Queries

```python
# Query with single parameter
site_name = "Amagasaki"
site_data = client.db.ngl.read_sql(
    "SELECT * FROM SITE WHERE SITE_NAME = %s",
    params=[site_name]
)

# Query with multiple parameters
min_lat, max_lat = 32.0, 38.0
california_sites = client.db.ngl.read_sql(
    "SELECT * FROM SITE WHERE SITE_LAT BETWEEN %s AND %s",
    params=[min_lat, max_lat]
)

# Query with named parameters (dictionary)
region_sites = client.db.ngl.read_sql(
    "SELECT * FROM SITE WHERE SITE_LAT > %(min_lat)s AND SITE_LON < %(max_lon)s",
    params={"min_lat": 35.0, "max_lon": -115.0}
)
```

## 🏗️ NGL Database (Next Generation Liquefaction)

The NGL database contains comprehensive data on soil liquefaction case histories.

### Key Tables

```python
# Explore database structure
tables_info = client.db.ngl.read_sql("SHOW TABLES")
print("Available tables:")
print(tables_info)

# Get table structure
site_structure = client.db.ngl.read_sql("DESCRIBE SITE")
print("SITE table structure:")
print(site_structure)
```

### Common NGL Queries

```python
# Site information
sites = client.db.ngl.read_sql("""
    SELECT SITE_ID, SITE_NAME, SITE_LAT, SITE_LON, SITE_GEOL
    FROM SITE
    WHERE SITE_STAT = 1  -- Active sites only
    ORDER BY SITE_NAME
""")

# Sites with liquefaction data
liquefaction_sites = client.db.ngl.read_sql("""
    SELECT DISTINCT s.SITE_NAME, s.SITE_LAT, s.SITE_LON
    FROM SITE s
    JOIN RECORD r ON s.SITE_ID = r.SITE_ID
    WHERE r.RECORD_STAT = 1
    ORDER BY s.SITE_NAME
""")

# Earthquake events
earthquakes = client.db.ngl.read_sql("""
    SELECT DISTINCT EVENT_NAME, EVENT_DATE, EVENT_MAG
    FROM EVENT
    WHERE EVENT_STAT = 1
    ORDER BY EVENT_DATE DESC
    LIMIT 20
""")

# CPT data summary
cpt_summary = client.db.ngl.read_sql("""
    SELECT 
        COUNT(*) as total_cpts,
        AVG(CPT_DEPTH) as avg_depth,
        MIN(CPT_DEPTH) as min_depth,
        MAX(CPT_DEPTH) as max_depth
    FROM CPT
    WHERE CPT_STAT = 1
""")
```

### Advanced NGL Analysis

```python
# Sites with high liquefaction potential
high_risk_sites = client.db.ngl.read_sql("""
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

# Correlation between soil properties and liquefaction
soil_correlation = client.db.ngl.read_sql("""
    SELECT 
        cpt.CPT_FC as fines_content,
        cpt.CPT_D50 as median_grain_size,
        COUNT(l.LIQ_ID) as liquefaction_cases,
        AVG(e.EVENT_MAG) as avg_magnitude
    FROM CPT cpt
    JOIN RECORD r ON cpt.RECORD_ID = r.RECORD_ID
    LEFT JOIN LIQUEFACTION l ON r.RECORD_ID = l.RECORD_ID
    JOIN EVENT e ON r.EVENT_ID = e.EVENT_ID
    WHERE cpt.CPT_STAT = 1 AND r.RECORD_STAT = 1
    AND cpt.CPT_FC IS NOT NULL AND cpt.CPT_D50 IS NOT NULL
    GROUP BY 
        ROUND(cpt.CPT_FC, 1),
        ROUND(cpt.CPT_D50, 2)
    ORDER BY fines_content, median_grain_size
""")
```

## 🌪️ Earthquake Recovery Database

The earthquake recovery database contains data on post-earthquake recovery processes.

### Common EQ Queries

```python
# Recovery milestones
recovery_data = client.db.eq.read_sql("""
    SELECT 
        event_name,
        recovery_metric,
        recovery_time_days,
        affected_population
    FROM recovery_metrics
    WHERE recovery_time_days IS NOT NULL
    ORDER BY event_name, recovery_time_days
""")

# Economic impact analysis
economic_impact = client.db.eq.read_sql("""
    SELECT 
        region,
        AVG(economic_loss_millions) as avg_loss,
        SUM(displaced_households) as total_displaced,
        COUNT(*) as num_events
    FROM economic_impacts
    GROUP BY region
    ORDER BY avg_loss DESC
""")
```

## 🔬 VP Database (Validation Portal)

The VP database contains model validation data and benchmarks.

### Common VP Queries

```python
# Model performance metrics
model_performance = client.db.vp.read_sql("""
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

# Benchmark cases
benchmarks = client.db.vp.read_sql("""
    SELECT 
        benchmark_id,
        benchmark_name,
        category,
        difficulty_level,
        num_participants
    FROM benchmarks
    ORDER BY category, difficulty_level
""")
```

## 📈 Data Analysis Patterns

### Statistical Analysis

```python
import pandas as pd
import matplotlib.pyplot as plt

# Get site data for analysis
sites_df = client.db.ngl.read_sql("""
    SELECT SITE_LAT, SITE_LON, SITE_GEOL
    FROM SITE 
    WHERE SITE_STAT = 1 AND SITE_LAT IS NOT NULL
""")

# Basic statistics
print("Site distribution by geology:")
geology_counts = sites_df['SITE_GEOL'].value_counts()
print(geology_counts)

# Geographic distribution
print(f"Latitude range: {sites_df['SITE_LAT'].min():.2f} to {sites_df['SITE_LAT'].max():.2f}")
print(f"Longitude range: {sites_df['SITE_LON'].min():.2f} to {sites_df['SITE_LON'].max():.2f}")

# Export for further analysis
sites_df.to_csv("ngl_sites.csv", index=False)
```

### Time Series Analysis

```python
# Earthquake timeline
earthquake_timeline = client.db.ngl.read_sql("""
    SELECT 
        EVENT_DATE,
        EVENT_NAME,
        EVENT_MAG,
        COUNT(r.RECORD_ID) as num_records
    FROM EVENT e
    LEFT JOIN RECORD r ON e.EVENT_ID = r.EVENT_ID
    WHERE e.EVENT_STAT = 1 AND e.EVENT_DATE IS NOT NULL
    GROUP BY e.EVENT_ID
    ORDER BY e.EVENT_DATE
""")

# Convert date column
earthquake_timeline['EVENT_DATE'] = pd.to_datetime(earthquake_timeline['EVENT_DATE'])

# Analyze earthquake frequency by decade
earthquake_timeline['decade'] = (earthquake_timeline['EVENT_DATE'].dt.year // 10) * 10
decade_summary = earthquake_timeline.groupby('decade').agg({
    'EVENT_NAME': 'count',
    'EVENT_MAG': 'mean',
    'num_records': 'sum'
}).rename(columns={'EVENT_NAME': 'earthquake_count'})

print("Earthquake data by decade:")
print(decade_summary)
```

### Geospatial Analysis

```python
# Sites by geographic region
regional_analysis = client.db.ngl.read_sql("""
    SELECT 
        CASE 
            WHEN SITE_LAT > 40 THEN 'Northern'
            WHEN SITE_LAT > 35 THEN 'Central'
            ELSE 'Southern'
        END as region,
        CASE
            WHEN SITE_LON > -100 THEN 'Eastern'
            WHEN SITE_LON > -120 THEN 'Central'
            ELSE 'Western'
        END as longitude_zone,
        COUNT(*) as site_count,
        AVG(SITE_LAT) as avg_latitude,
        AVG(SITE_LON) as avg_longitude
    FROM SITE
    WHERE SITE_STAT = 1 AND SITE_LAT IS NOT NULL AND SITE_LON IS NOT NULL
    GROUP BY region, longitude_zone
    ORDER BY region, longitude_zone
""")

print("Geographic distribution of sites:")
print(regional_analysis)
```

## 🔄 Connection Management

### Manual Connection Handling

```python
# Access database connection directly
ngl_db = client.db.ngl

# Check connection status
try:
    test_query = ngl_db.read_sql("SELECT 1 as test")
    print("✅ Database connection active")
except Exception as e:
    print(f"❌ Database connection failed: {e}")

# Close connections when done (optional - handled automatically)
ngl_db.close()
```

### Connection Pooling

```python
# dapi automatically manages connection pooling
# Multiple queries reuse connections efficiently

queries = [
    "SELECT COUNT(*) FROM SITE",
    "SELECT COUNT(*) FROM RECORD", 
    "SELECT COUNT(*) FROM EVENT"
]

for query in queries:
    result = client.db.ngl.read_sql(query)
    print(f"{query}: {result.iloc[0, 0]}")
```

## 🚨 Error Handling

### Database Connection Errors

```python
try:
    df = client.db.ngl.read_sql("SELECT * FROM SITE LIMIT 5")
    print("✅ Query successful")
except Exception as e:
    print(f"❌ Database error: {e}")
    
    # Check environment variables
    import os
    required_vars = ['NGL_DB_USER', 'NGL_DB_PASSWORD', 'NGL_DB_HOST', 'NGL_DB_PORT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {missing_vars}")
    else:
        print("Environment variables are set, check database credentials")
```

### SQL Query Errors

```python
try:
    # Intentionally bad query
    df = client.db.ngl.read_sql("SELECT * FROM NONEXISTENT_TABLE")
except Exception as e:
    print(f"SQL Error: {e}")
    
    # Provide helpful debugging
    print("💡 Tips:")
    print("- Check table name spelling")
    print("- Verify table exists: SHOW TABLES")
    print("- Check column names: DESCRIBE table_name")
```

## 💡 Best Practices

### 1. Use Parameterized Queries
```python
# ✅ Good - prevents SQL injection
safe_query = client.db.ngl.read_sql(
    "SELECT * FROM SITE WHERE SITE_NAME = %s",
    params=[user_input]
)

# ❌ Dangerous - vulnerable to SQL injection
dangerous_query = client.db.ngl.read_sql(
    f"SELECT * FROM SITE WHERE SITE_NAME = '{user_input}'"
)
```

### 2. Limit Result Sets
```python
# ✅ Good - use LIMIT for large tables
limited_query = client.db.ngl.read_sql(
    "SELECT * FROM LARGE_TABLE LIMIT 1000"
)

# ✅ Better - use pagination for very large datasets
offset = 0
batch_size = 1000
while True:
    batch = client.db.ngl.read_sql(
        "SELECT * FROM LARGE_TABLE LIMIT %s OFFSET %s",
        params=[batch_size, offset]
    )
    if batch.empty:
        break
    # Process batch
    offset += batch_size
```

### 3. Efficient Joins
```python
# ✅ Good - use indexes and appropriate joins
efficient_query = client.db.ngl.read_sql("""
    SELECT s.SITE_NAME, COUNT(r.RECORD_ID) as record_count
    FROM SITE s
    LEFT JOIN RECORD r ON s.SITE_ID = r.SITE_ID
    WHERE s.SITE_STAT = 1
    GROUP BY s.SITE_ID, s.SITE_NAME
    ORDER BY record_count DESC
    LIMIT 50
""")
```

### 4. Data Validation
```python
# ✅ Good - validate data before analysis
df = client.db.ngl.read_sql("SELECT SITE_LAT, SITE_LON FROM SITE")

# Check for missing values
missing_coords = df.isnull().sum()
print(f"Missing coordinates: {missing_coords}")

# Remove invalid coordinates
valid_coords = df.dropna()
valid_coords = valid_coords[
    (valid_coords['SITE_LAT'].between(-90, 90)) &
    (valid_coords['SITE_LON'].between(-180, 180))
]
print(f"Valid coordinates: {len(valid_coords)}/{len(df)}")
```

## 📊 Export and Integration

### Export to Different Formats

```python
# Query data
df = client.db.ngl.read_sql("""
    SELECT s.SITE_NAME, s.SITE_LAT, s.SITE_LON, e.EVENT_NAME, e.EVENT_MAG
    FROM SITE s
    JOIN RECORD r ON s.SITE_ID = r.SITE_ID
    JOIN EVENT e ON r.EVENT_ID = e.EVENT_ID
    WHERE s.SITE_STAT = 1 AND r.RECORD_STAT = 1
""")

# Export to various formats
df.to_csv("ngl_data.csv", index=False)
df.to_excel("ngl_data.xlsx", index=False)
df.to_json("ngl_data.json", orient="records")

# Export to GIS formats (requires geopandas)
try:
    import geopandas as gpd
    from shapely.geometry import Point
    
    # Create GeoDataFrame
    geometry = [Point(xy) for xy in zip(df['SITE_LON'], df['SITE_LAT'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry)
    gdf.to_file("ngl_sites.geojson", driver="GeoJSON")
    print("✅ Exported to GeoJSON")
except ImportError:
    print("Install geopandas for GIS export: pip install geopandas")
```

### Integration with Analysis Tools

```python
# Prepare data for machine learning
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Get numeric features
features_df = client.db.ngl.read_sql("""
    SELECT 
        cpt.CPT_DEPTH,
        cpt.CPT_QC,
        cpt.CPT_FS,
        cpt.CPT_FC,
        e.EVENT_MAG,
        CASE WHEN l.LIQ_ID IS NOT NULL THEN 1 ELSE 0 END as liquefied
    FROM CPT cpt
    JOIN RECORD r ON cpt.RECORD_ID = r.RECORD_ID
    JOIN EVENT e ON r.EVENT_ID = e.EVENT_ID
    LEFT JOIN LIQUEFACTION l ON r.RECORD_ID = l.RECORD_ID
    WHERE cpt.CPT_STAT = 1 AND r.RECORD_STAT = 1
    AND cpt.CPT_DEPTH IS NOT NULL
    AND cpt.CPT_QC IS NOT NULL
    AND cpt.CPT_FS IS NOT NULL
    AND e.EVENT_MAG IS NOT NULL
""")

# Remove missing values
clean_df = features_df.dropna()

# Prepare features and target
X = clean_df[['CPT_DEPTH', 'CPT_QC', 'CPT_FS', 'CPT_FC', 'EVENT_MAG']]
y = clean_df['liquefied']

# Split and scale
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"Training set: {X_train.shape}")
print(f"Test set: {X_test.shape}")
print(f"Liquefaction rate: {y.mean():.3f}")
```

## ➡️ Next Steps

- **[Explore complete examples](examples/database.md)** showing real database workflows
- **Learn about file operations** for data management
- **Check API reference** for detailed method documentation
- **[Review job integration](jobs.md)** for computational workflows with database data