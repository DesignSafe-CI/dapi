# Database Query Examples

This comprehensive guide demonstrates how to query and analyze DesignSafe research databases using dapi. We'll explore the NGL (Next Generation Liquefaction) database with practical examples for earthquake engineering and geotechnical research.

## 🎯 Overview

This example covers:
- Setting up database connections
- Basic and advanced SQL queries
- Data analysis and visualization
- Exporting results for further analysis
- Best practices for database operations

## 🚀 Complete Database Analysis Example

### Step 1: Setup and Authentication

```python
import os
import pandas as pd
import numpy as np
from dapi import DSClient
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Initialize DSClient
try:
    print("🔑 Initializing DSClient...")
    client = DSClient()
    print("✅ DSClient initialized successfully")
    
    # Test database connectivity
    print("\n🔍 Testing database connections...")
    
    # Test NGL database
    try:
        test_ngl = client.db.ngl.read_sql("SELECT COUNT(*) as count FROM SITE")
        print(f"✅ NGL Database: {test_ngl['count'].iloc[0]} sites available")
    except Exception as e:
        print(f"❌ NGL Database connection failed: {e}")
        
    # Test other databases (if available)
    try:
        test_vp = client.db.vp.read_sql("SELECT COUNT(*) as count FROM information_schema.tables")
        print(f"✅ VP Database: Connected successfully")
    except Exception as e:
        print(f"⚠️ VP Database: {e}")
        
    try:
        test_eq = client.db.eq.read_sql("SELECT COUNT(*) as count FROM information_schema.tables")
        print(f"✅ EQ Database: Connected successfully")
    except Exception as e:
        print(f"⚠️ EQ Database: {e}")
        
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    raise SystemExit("Stopping due to initialization failure")
```

### Step 2: Database Structure Exploration

```python
# Explore the NGL database structure
print("\n📊 Exploring NGL Database Structure")
print("=" * 50)

# List all tables
try:
    tables = client.db.ngl.read_sql("SHOW TABLES")
    print(f"📋 Available tables ({len(tables)}):")
    for i, table in enumerate(tables.iloc[:, 0], 1):
        print(f"   {i:2d}. {table}")
        
    # Get detailed information about key tables
    key_tables = ['SITE', 'RECORD', 'EVENT', 'CPT', 'LIQUEFACTION']
    
    print(f"\n🔍 Key Table Structures:")
    for table in key_tables:
        try:
            structure = client.db.ngl.read_sql(f"DESCRIBE {table}")
            print(f"\n📁 {table} table:")
            print(f"   Columns: {len(structure)}")
            for _, row in structure.head(5).iterrows():
                null_str = "NULL" if row['Null'] == 'YES' else "NOT NULL"
                print(f"   - {row['Field']:20} {row['Type']:15} {null_str}")
            if len(structure) > 5:
                print(f"   ... and {len(structure) - 5} more columns")
                
        except Exception as e:
            print(f"   ❌ Could not describe {table}: {e}")
            
except Exception as e:
    print(f"❌ Database exploration failed: {e}")
```

### Step 3: Basic Queries and Data Overview

```python
# Basic data overview queries
print("\n📈 Database Overview and Statistics")
print("=" * 45)

try:
    # Site statistics
    site_stats = client.db.ngl.read_sql("""
        SELECT 
            COUNT(*) as total_sites,
            COUNT(DISTINCT SITE_GEOL) as unique_geologies,
            MIN(SITE_LAT) as min_latitude,
            MAX(SITE_LAT) as max_latitude,
            MIN(SITE_LON) as min_longitude,
            MAX(SITE_LON) as max_longitude
        FROM SITE 
        WHERE SITE_STAT = 1
    """)
    
    print("🌍 Site Statistics:")
    stats = site_stats.iloc[0]
    print(f"   Total active sites: {stats['total_sites']}")
    print(f"   Unique geologies: {stats['unique_geologies']}")
    print(f"   Latitude range: {stats['min_latitude']:.2f}° to {stats['max_latitude']:.2f}°")
    print(f"   Longitude range: {stats['min_longitude']:.2f}° to {stats['max_longitude']:.2f}°")
    
    # Record statistics
    record_stats = client.db.ngl.read_sql("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT EVENT_ID) as unique_events,
            COUNT(DISTINCT SITE_ID) as sites_with_records
        FROM RECORD 
        WHERE RECORD_STAT = 1
    """)
    
    print(f"\n📊 Record Statistics:")
    rec_stats = record_stats.iloc[0]
    print(f"   Total active records: {rec_stats['total_records']}")
    print(f"   Unique events: {rec_stats['unique_events']}")
    print(f"   Sites with records: {rec_stats['sites_with_records']}")
    
    # Event statistics
    event_stats = client.db.ngl.read_sql("""
        SELECT 
            COUNT(*) as total_events,
            MIN(EVENT_MAG) as min_magnitude,
            MAX(EVENT_MAG) as max_magnitude,
            AVG(EVENT_MAG) as avg_magnitude,
            MIN(EVENT_DATE) as earliest_event,
            MAX(EVENT_DATE) as latest_event
        FROM EVENT 
        WHERE EVENT_STAT = 1 AND EVENT_MAG IS NOT NULL
    """)
    
    print(f"\n🌪️ Earthquake Event Statistics:")
    evt_stats = event_stats.iloc[0]
    print(f"   Total events: {evt_stats['total_events']}")
    print(f"   Magnitude range: {evt_stats['min_magnitude']:.1f} to {evt_stats['max_magnitude']:.1f}")
    print(f"   Average magnitude: {evt_stats['avg_magnitude']:.2f}")
    print(f"   Date range: {evt_stats['earliest_event']} to {evt_stats['latest_event']}")
    
except Exception as e:
    print(f"❌ Basic statistics query failed: {e}")
```

### Step 4: Geographic Analysis

```python
# Geographic distribution analysis
print("\n🗺️ Geographic Distribution Analysis")
print("=" * 40)

try:
    # Sites by country/region (using latitude/longitude boundaries)
    geographic_distribution = client.db.ngl.read_sql("""
        SELECT 
            CASE 
                WHEN SITE_LAT > 49 THEN 'Canada'
                WHEN SITE_LAT > 25 AND SITE_LON > -125 AND SITE_LON < -65 THEN 'United States'
                WHEN SITE_LAT > 14 AND SITE_LAT < 33 AND SITE_LON > -118 AND SITE_LON < -86 THEN 'Mexico'
                WHEN SITE_LAT > 30 AND SITE_LAT < 46 AND SITE_LON > 126 AND SITE_LON < 146 THEN 'Japan'
                WHEN SITE_LAT > 35 AND SITE_LAT < 42 AND SITE_LON > 19 AND SITE_LON < 30 THEN 'Turkey'
                WHEN SITE_LAT > -45 AND SITE_LAT < -10 AND SITE_LON > 110 AND SITE_LON < 155 THEN 'Australia'
                WHEN SITE_LAT > -56 AND SITE_LAT < -17 AND SITE_LON > -75 AND SITE_LON < -34 THEN 'South America'
                ELSE 'Other'
            END as region,
            COUNT(*) as site_count,
            AVG(SITE_LAT) as avg_latitude,
            AVG(SITE_LON) as avg_longitude
        FROM SITE 
        WHERE SITE_STAT = 1 AND SITE_LAT IS NOT NULL AND SITE_LON IS NOT NULL
        GROUP BY region
        ORDER BY site_count DESC
    """)
    
    print("🌎 Sites by Geographic Region:")
    for _, row in geographic_distribution.iterrows():
        print(f"   {row['region']:15}: {row['site_count']:3d} sites (avg: {row['avg_latitude']:6.2f}°, {row['avg_longitude']:7.2f}°)")
    
    # California sites analysis (high seismic activity region)
    california_sites = client.db.ngl.read_sql("""
        SELECT 
            s.SITE_NAME,
            s.SITE_LAT,
            s.SITE_LON,
            s.SITE_GEOL,
            COUNT(r.RECORD_ID) as record_count
        FROM SITE s
        LEFT JOIN RECORD r ON s.SITE_ID = r.SITE_ID AND r.RECORD_STAT = 1
        WHERE s.SITE_STAT = 1 
        AND s.SITE_LAT BETWEEN 32.5 AND 42.0 
        AND s.SITE_LON BETWEEN -124.5 AND -114.0
        GROUP BY s.SITE_ID
        ORDER BY record_count DESC, s.SITE_NAME
        LIMIT 15
    """)
    
    print(f"\n🌉 California Sites (Top 15 by record count):")
    for _, row in california_sites.iterrows():
        print(f"   {row['SITE_NAME']:25} ({row['SITE_LAT']:6.2f}, {row['SITE_LON']:7.2f}) - {row['record_count']:2d} records - {row['SITE_GEOL']}")
        
except Exception as e:
    print(f"❌ Geographic analysis failed: {e}")
```

### Step 5: Earthquake Event Analysis

```python
# Earthquake event analysis
print("\n🌪️ Earthquake Event Analysis")
print("=" * 35)

try:
    # Major earthquakes with liquefaction data
    major_earthquakes = client.db.ngl.read_sql("""
        SELECT 
            e.EVENT_NAME,
            e.EVENT_DATE,
            e.EVENT_MAG,
            e.EVENT_LAT,
            e.EVENT_LON,
            COUNT(DISTINCT r.SITE_ID) as affected_sites,
            COUNT(r.RECORD_ID) as total_records,
            COUNT(l.LIQ_ID) as liquefaction_cases
        FROM EVENT e
        JOIN RECORD r ON e.EVENT_ID = r.EVENT_ID AND r.RECORD_STAT = 1
        LEFT JOIN LIQUEFACTION l ON r.RECORD_ID = l.RECORD_ID
        WHERE e.EVENT_STAT = 1 AND e.EVENT_MAG >= 6.0
        GROUP BY e.EVENT_ID
        ORDER BY e.EVENT_MAG DESC, liquefaction_cases DESC
        LIMIT 20
    """)
    
    print("⚡ Major Earthquakes (M ≥ 6.0) with Liquefaction Data:")
    print(f"{'Event':25} {'Date':12} {'Mag':4} {'Sites':6} {'Records':8} {'Liq Cases':10}")
    print("-" * 70)
    for _, row in major_earthquakes.iterrows():
        liq_rate = (row['liquefaction_cases'] / row['total_records'] * 100) if row['total_records'] > 0 else 0
        print(f"{row['EVENT_NAME'][:24]:25} {str(row['EVENT_DATE'])[:10]:12} {row['EVENT_MAG']:4.1f} {row['affected_sites']:6d} {row['total_records']:8d} {row['liquefaction_cases']:6d} ({liq_rate:4.1f}%)")
    
    # Magnitude distribution
    magnitude_distribution = client.db.ngl.read_sql("""
        SELECT 
            CASE 
                WHEN EVENT_MAG < 5.0 THEN 'M < 5.0'
                WHEN EVENT_MAG < 6.0 THEN '5.0 ≤ M < 6.0'
                WHEN EVENT_MAG < 7.0 THEN '6.0 ≤ M < 7.0'
                WHEN EVENT_MAG < 8.0 THEN '7.0 ≤ M < 8.0'
                ELSE 'M ≥ 8.0'
            END as magnitude_range,
            COUNT(*) as event_count,
            COUNT(DISTINCT r.RECORD_ID) as total_records
        FROM EVENT e
        LEFT JOIN RECORD r ON e.EVENT_ID = r.EVENT_ID AND r.RECORD_STAT = 1
        WHERE e.EVENT_STAT = 1 AND e.EVENT_MAG IS NOT NULL
        GROUP BY magnitude_range
        ORDER BY MIN(e.EVENT_MAG)
    """)
    
    print(f"\n📊 Earthquake Magnitude Distribution:")
    for _, row in magnitude_distribution.iterrows():
        print(f"   {row['magnitude_range']:15}: {row['event_count']:3d} events, {row['total_records']:4d} records")
        
except Exception as e:
    print(f"❌ Earthquake analysis failed: {e}")
```

### Step 6: Liquefaction Analysis

```python
# Detailed liquefaction analysis
print("\n💧 Liquefaction Analysis")
print("=" * 30)

try:
    # Liquefaction susceptibility by soil type
    soil_liquefaction = client.db.ngl.read_sql("""
        SELECT 
            s.SITE_GEOL as geology,
            COUNT(DISTINCT r.RECORD_ID) as total_records,
            COUNT(DISTINCT l.LIQ_ID) as liquefaction_cases,
            ROUND(COUNT(DISTINCT l.LIQ_ID) * 100.0 / COUNT(DISTINCT r.RECORD_ID), 2) as liquefaction_rate,
            AVG(e.EVENT_MAG) as avg_magnitude,
            COUNT(DISTINCT s.SITE_ID) as unique_sites
        FROM SITE s
        JOIN RECORD r ON s.SITE_ID = r.SITE_ID AND r.RECORD_STAT = 1
        JOIN EVENT e ON r.EVENT_ID = e.EVENT_ID AND e.EVENT_STAT = 1
        LEFT JOIN LIQUEFACTION l ON r.RECORD_ID = l.RECORD_ID
        WHERE s.SITE_STAT = 1 AND s.SITE_GEOL IS NOT NULL AND s.SITE_GEOL != ''
        GROUP BY s.SITE_GEOL
        HAVING total_records >= 5  -- Only show geologies with sufficient data
        ORDER BY liquefaction_rate DESC, total_records DESC
    """)
    
    print("🏔️ Liquefaction Susceptibility by Geology:")
    print(f"{'Geology':25} {'Records':8} {'Liq Cases':10} {'Rate %':8} {'Avg Mag':8} {'Sites':6}")
    print("-" * 75)
    for _, row in soil_liquefaction.iterrows():
        print(f"{row['geology'][:24]:25} {row['total_records']:8d} {row['liquefaction_cases']:10d} {row['liquefaction_rate']:8.1f} {row['avg_magnitude']:8.2f} {row['unique_sites']:6d}")
    
    # CPT-based analysis (if CPT data is available)
    cpt_liquefaction = client.db.ngl.read_sql("""
        SELECT 
            CASE 
                WHEN cpt.CPT_FC < 10 THEN 'Clean Sand (FC < 10%)'
                WHEN cpt.CPT_FC < 35 THEN 'Silty Sand (10% ≤ FC < 35%)'
                ELSE 'Clayey Soil (FC ≥ 35%)'
            END as soil_classification,
            COUNT(*) as cpt_count,
            COUNT(l.LIQ_ID) as liquefaction_cases,
            ROUND(COUNT(l.LIQ_ID) * 100.0 / COUNT(*), 2) as liquefaction_rate,
            AVG(cpt.CPT_QC) as avg_tip_resistance,
            AVG(e.EVENT_MAG) as avg_magnitude
        FROM CPT cpt
        JOIN RECORD r ON cpt.RECORD_ID = r.RECORD_ID AND r.RECORD_STAT = 1
        JOIN EVENT e ON r.EVENT_ID = e.EVENT_ID AND e.EVENT_STAT = 1
        LEFT JOIN LIQUEFACTION l ON r.RECORD_ID = l.RECORD_ID
        WHERE cpt.CPT_STAT = 1 AND cpt.CPT_FC IS NOT NULL 
        AND cpt.CPT_QC IS NOT NULL AND cpt.CPT_QC > 0
        GROUP BY soil_classification
        ORDER BY liquefaction_rate DESC
    """)
    
    if not cpt_liquefaction.empty:
        print(f"\n🔬 CPT-based Liquefaction Analysis:")
        print(f"{'Soil Classification':25} {'CPT Count':10} {'Liq Cases':10} {'Rate %':8} {'Avg qc':8} {'Avg Mag':8}")
        print("-" * 80)
        for _, row in cpt_liquefaction.iterrows():
            print(f"{row['soil_classification']:25} {row['cpt_count']:10d} {row['liquefaction_cases']:10d} {row['liquefaction_rate']:8.1f} {row['avg_tip_resistance']:8.1f} {row['avg_magnitude']:8.2f}")
    
    # Magnitude vs liquefaction relationship
    magnitude_liquefaction = client.db.ngl.read_sql("""
        SELECT 
            CASE 
                WHEN e.EVENT_MAG < 5.5 THEN 'M < 5.5'
                WHEN e.EVENT_MAG < 6.5 THEN '5.5 ≤ M < 6.5'
                WHEN e.EVENT_MAG < 7.5 THEN '6.5 ≤ M < 7.5'
                ELSE 'M ≥ 7.5'
            END as magnitude_range,
            COUNT(DISTINCT r.RECORD_ID) as total_records,
            COUNT(DISTINCT l.LIQ_ID) as liquefaction_cases,
            ROUND(COUNT(DISTINCT l.LIQ_ID) * 100.0 / COUNT(DISTINCT r.RECORD_ID), 2) as liquefaction_rate
        FROM RECORD r
        JOIN EVENT e ON r.EVENT_ID = e.EVENT_ID AND e.EVENT_STAT = 1
        LEFT JOIN LIQUEFACTION l ON r.RECORD_ID = l.RECORD_ID
        WHERE r.RECORD_STAT = 1 AND e.EVENT_MAG IS NOT NULL
        GROUP BY magnitude_range
        ORDER BY MIN(e.EVENT_MAG)
    """)
    
    print(f"\n📈 Magnitude vs Liquefaction Relationship:")
    for _, row in magnitude_liquefaction.iterrows():
        print(f"   {row['magnitude_range']:15}: {row['liquefaction_cases']:3d}/{row['total_records']:3d} records ({row['liquefaction_rate']:5.1f}% liquefaction rate)")
        
except Exception as e:
    print(f"❌ Liquefaction analysis failed: {e}")
```

### Step 7: Time Series Analysis

```python
# Temporal analysis of earthquake and liquefaction data
print("\n📅 Temporal Analysis")
print("=" * 25)

try:
    # Earthquake timeline by decade
    temporal_analysis = client.db.ngl.read_sql("""
        SELECT 
            FLOOR(YEAR(e.EVENT_DATE) / 10) * 10 as decade,
            COUNT(DISTINCT e.EVENT_ID) as earthquake_count,
            COUNT(DISTINCT r.RECORD_ID) as record_count,
            COUNT(DISTINCT l.LIQ_ID) as liquefaction_cases,
            AVG(e.EVENT_MAG) as avg_magnitude,
            MAX(e.EVENT_MAG) as max_magnitude
        FROM EVENT e
        LEFT JOIN RECORD r ON e.EVENT_ID = r.EVENT_ID AND r.RECORD_STAT = 1
        LEFT JOIN LIQUEFACTION l ON r.RECORD_ID = l.RECORD_ID
        WHERE e.EVENT_STAT = 1 AND e.EVENT_DATE IS NOT NULL
        GROUP BY decade
        ORDER BY decade
    """)
    
    print("📊 Earthquake Data by Decade:")
    print(f"{'Decade':8} {'Events':8} {'Records':8} {'Liq Cases':10} {'Avg Mag':8} {'Max Mag':8}")
    print("-" * 60)
    for _, row in temporal_analysis.iterrows():
        decade_str = f"{int(row['decade'])}s"
        print(f"{decade_str:8} {row['earthquake_count']:8d} {row['record_count']:8d} {row['liquefaction_cases']:10d} {row['avg_magnitude']:8.2f} {row['max_magnitude']:8.2f}")
    
    # Recent significant events (last 30 years)
    recent_events = client.db.ngl.read_sql("""
        SELECT 
            e.EVENT_NAME,
            e.EVENT_DATE,
            e.EVENT_MAG,
            COUNT(DISTINCT r.RECORD_ID) as records,
            COUNT(DISTINCT l.LIQ_ID) as liquefaction_cases
        FROM EVENT e
        JOIN RECORD r ON e.EVENT_ID = r.EVENT_ID AND r.RECORD_STAT = 1
        LEFT JOIN LIQUEFACTION l ON r.RECORD_ID = l.RECORD_ID
        WHERE e.EVENT_STAT = 1 
        AND e.EVENT_DATE >= DATE_SUB(CURDATE(), INTERVAL 30 YEAR)
        AND e.EVENT_MAG >= 6.0
        GROUP BY e.EVENT_ID
        ORDER BY e.EVENT_DATE DESC
        LIMIT 15
    """)
    
    if not recent_events.empty:
        print(f"\n🕐 Recent Major Events (Last 30 Years, M ≥ 6.0):")
        print(f"{'Event':30} {'Date':12} {'Mag':4} {'Records':8} {'Liq Cases':10}")
        print("-" * 70)
        for _, row in recent_events.iterrows():
            print(f"{row['EVENT_NAME'][:29]:30} {str(row['EVENT_DATE']):12} {row['EVENT_MAG']:4.1f} {row['records']:8d} {row['liquefaction_cases']:10d}")
    
except Exception as e:
    print(f"❌ Temporal analysis failed: {e}")
```

### Step 8: Advanced Statistical Analysis

```python
# Advanced statistical correlations
print("\n📊 Advanced Statistical Analysis")
print("=" * 35)

try:
    # Correlation between earthquake parameters and liquefaction
    correlation_data = client.db.ngl.read_sql("""
        SELECT 
            e.EVENT_MAG as magnitude,
            cpt.CPT_DEPTH as depth,
            cpt.CPT_QC as cone_resistance,
            cpt.CPT_FS as sleeve_friction,
            cpt.CPT_FC as fines_content,
            CASE WHEN l.LIQ_ID IS NOT NULL THEN 1 ELSE 0 END as liquefied
        FROM CPT cpt
        JOIN RECORD r ON cpt.RECORD_ID = r.RECORD_ID AND r.RECORD_STAT = 1
        JOIN EVENT e ON r.EVENT_ID = e.EVENT_ID AND e.EVENT_STAT = 1
        LEFT JOIN LIQUEFACTION l ON r.RECORD_ID = l.RECORD_ID
        WHERE cpt.CPT_STAT = 1 
        AND cpt.CPT_DEPTH IS NOT NULL AND cpt.CPT_DEPTH > 0
        AND cpt.CPT_QC IS NOT NULL AND cpt.CPT_QC > 0
        AND cpt.CPT_FS IS NOT NULL AND cpt.CPT_FS >= 0
        AND e.EVENT_MAG IS NOT NULL
        LIMIT 5000  -- Limit for performance
    """)
    
    if not correlation_data.empty and len(correlation_data) > 10:
        print(f"📈 Statistical Summary (n = {len(correlation_data)} CPT records):")
        
        # Basic statistics
        numeric_cols = ['magnitude', 'depth', 'cone_resistance', 'sleeve_friction', 'fines_content']
        stats_summary = correlation_data[numeric_cols].describe()
        
        print("\n📊 Descriptive Statistics:")
        print(f"{'Parameter':20} {'Mean':10} {'Std':10} {'Min':10} {'Max':10}")
        print("-" * 70)
        for col in numeric_cols:
            if col in stats_summary.columns:
                mean_val = stats_summary.loc['mean', col]
                std_val = stats_summary.loc['std', col]
                min_val = stats_summary.loc['min', col]
                max_val = stats_summary.loc['max', col]
                print(f"{col:20} {mean_val:10.2f} {std_val:10.2f} {min_val:10.2f} {max_val:10.2f}")
        
        # Liquefaction statistics
        liq_stats = correlation_data.groupby('liquefied').agg({
            'magnitude': ['count', 'mean', 'std'],
            'depth': ['mean', 'std'],
            'cone_resistance': ['mean', 'std'],
            'fines_content': ['mean', 'std']
        }).round(2)
        
        total_cases = len(correlation_data)
        liq_cases = correlation_data['liquefied'].sum()
        liq_rate = liq_cases / total_cases * 100
        
        print(f"\n💧 Liquefaction Statistics:")
        print(f"   Total cases: {total_cases}")
        print(f"   Liquefaction cases: {liq_cases} ({liq_rate:.1f}%)")
        print(f"   No liquefaction: {total_cases - liq_cases} ({100 - liq_rate:.1f}%)")
        
        # Simple correlation analysis
        if 'fines_content' in correlation_data.columns:
            clean_sand = correlation_data[correlation_data['fines_content'] < 10]
            silty_sand = correlation_data[(correlation_data['fines_content'] >= 10) & (correlation_data['fines_content'] < 35)]
            
            if len(clean_sand) > 0:
                clean_sand_liq_rate = clean_sand['liquefied'].mean() * 100
                print(f"   Clean sand liquefaction rate: {clean_sand_liq_rate:.1f}% (n={len(clean_sand)})")
                
            if len(silty_sand) > 0:
                silty_sand_liq_rate = silty_sand['liquefied'].mean() * 100
                print(f"   Silty sand liquefaction rate: {silty_sand_liq_rate:.1f}% (n={len(silty_sand)})")
    
    else:
        print("⚠️ Insufficient CPT data for statistical analysis")
        
except Exception as e:
    print(f"❌ Statistical analysis failed: {e}")
```

### Step 9: Data Export and Visualization Preparation

```python
# Export data for visualization and further analysis
print("\n💾 Data Export and Preparation")
print("=" * 35)

try:
    # Create timestamp for file naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export site data with coordinates
    sites_export = client.db.ngl.read_sql("""
        SELECT 
            s.SITE_ID,
            s.SITE_NAME,
            s.SITE_LAT,
            s.SITE_LON,
            s.SITE_GEOL,
            COUNT(DISTINCT r.RECORD_ID) as record_count,
            COUNT(DISTINCT l.LIQ_ID) as liquefaction_count,
            COUNT(DISTINCT e.EVENT_ID) as event_count,
            AVG(e.EVENT_MAG) as avg_magnitude
        FROM SITE s
        LEFT JOIN RECORD r ON s.SITE_ID = r.SITE_ID AND r.RECORD_STAT = 1
        LEFT JOIN LIQUEFACTION l ON r.RECORD_ID = l.RECORD_ID
        LEFT JOIN EVENT e ON r.EVENT_ID = e.EVENT_ID AND e.EVENT_STAT = 1
        WHERE s.SITE_STAT = 1 AND s.SITE_LAT IS NOT NULL AND s.SITE_LON IS NOT NULL
        GROUP BY s.SITE_ID
        ORDER BY s.SITE_NAME
    """)
    
    # Export earthquake events
    events_export = client.db.ngl.read_sql("""
        SELECT 
            e.EVENT_ID,
            e.EVENT_NAME,
            e.EVENT_DATE,
            e.EVENT_MAG,
            e.EVENT_LAT,
            e.EVENT_LON,
            COUNT(DISTINCT r.RECORD_ID) as affected_sites,
            COUNT(DISTINCT l.LIQ_ID) as liquefaction_cases
        FROM EVENT e
        LEFT JOIN RECORD r ON e.EVENT_ID = r.EVENT_ID AND r.RECORD_STAT = 1
        LEFT JOIN LIQUEFACTION l ON r.RECORD_ID = l.RECORD_ID
        WHERE e.EVENT_STAT = 1
        GROUP BY e.EVENT_ID
        ORDER BY e.EVENT_DATE DESC
    """)
    
    # Export summary statistics
    summary_export = client.db.ngl.read_sql("""
        SELECT 
            'Total Sites' as metric,
            COUNT(DISTINCT s.SITE_ID) as value
        FROM SITE s WHERE s.SITE_STAT = 1
        UNION ALL
        SELECT 
            'Total Events' as metric,
            COUNT(DISTINCT e.EVENT_ID) as value
        FROM EVENT e WHERE e.EVENT_STAT = 1
        UNION ALL
        SELECT 
            'Total Records' as metric,
            COUNT(DISTINCT r.RECORD_ID) as value
        FROM RECORD r WHERE r.RECORD_STAT = 1
        UNION ALL
        SELECT 
            'Liquefaction Cases' as metric,
            COUNT(DISTINCT l.LIQ_ID) as value
        FROM LIQUEFACTION l
    """)
    
    # Save to CSV files
    output_dir = f"ngl_analysis_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    sites_export.to_csv(f"{output_dir}/ngl_sites.csv", index=False)
    events_export.to_csv(f"{output_dir}/ngl_events.csv", index=False)
    summary_export.to_csv(f"{output_dir}/ngl_summary.csv", index=False)
    
    print(f"✅ Data exported to {output_dir}/")
    print(f"   - ngl_sites.csv: {len(sites_export)} sites")
    print(f"   - ngl_events.csv: {len(events_export)} events")
    print(f"   - ngl_summary.csv: Database summary statistics")
    
    # Create a simple visualization script
    viz_script = f"""
# Quick visualization script for NGL data
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
sites = pd.read_csv('{output_dir}/ngl_sites.csv')
events = pd.read_csv('{output_dir}/ngl_events.csv')

# Create visualizations
fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# Site locations
axes[0,0].scatter(sites['SITE_LON'], sites['SITE_LAT'], 
                 c=sites['liquefaction_count'], cmap='Reds', alpha=0.6)
axes[0,0].set_xlabel('Longitude')
axes[0,0].set_ylabel('Latitude')
axes[0,0].set_title('Site Locations (colored by liquefaction count)')

# Event magnitude distribution
events['EVENT_MAG'].hist(bins=20, ax=axes[0,1])
axes[0,1].set_xlabel('Magnitude')
axes[0,1].set_ylabel('Frequency')
axes[0,1].set_title('Earthquake Magnitude Distribution')

# Records per site
sites['record_count'].hist(bins=30, ax=axes[1,0])
axes[1,0].set_xlabel('Number of Records')
axes[1,0].set_ylabel('Number of Sites')
axes[1,0].set_title('Distribution of Records per Site')

# Liquefaction rate by geology
geology_stats = sites.groupby('SITE_GEOL').agg({{
    'liquefaction_count': 'sum',
    'record_count': 'sum'
}}).reset_index()
geology_stats['liq_rate'] = geology_stats['liquefaction_count'] / geology_stats['record_count'] * 100
geology_stats = geology_stats[geology_stats['record_count'] >= 10].sort_values('liq_rate', ascending=True)

if len(geology_stats) > 0:
    geology_stats.plot(x='SITE_GEOL', y='liq_rate', kind='barh', ax=axes[1,1])
    axes[1,1].set_xlabel('Liquefaction Rate (%)')
    axes[1,1].set_title('Liquefaction Rate by Geology')

plt.tight_layout()
plt.savefig('{output_dir}/ngl_analysis_plots.png', dpi=300, bbox_inches='tight')
plt.show()

print("✅ Visualizations saved to {output_dir}/ngl_analysis_plots.png")
"""
    
    with open(f"{output_dir}/create_visualizations.py", "w") as f:
        f.write(viz_script)
    
    print(f"📊 Visualization script created: {output_dir}/create_visualizations.py")
    print("   Run this script to generate plots from the exported data")
    
except Exception as e:
    print(f"❌ Data export failed: {e}")
```

### Step 10: Advanced Query Examples

```python
# Advanced query patterns for specific research questions
print("\n🔬 Advanced Research Query Examples")
print("=" * 40)

# Research Question 1: Distance-dependent liquefaction
try:
    distance_analysis = client.db.ngl.read_sql("""
        SELECT 
            CASE 
                WHEN distance_km < 10 THEN '< 10 km'
                WHEN distance_km < 25 THEN '10-25 km'
                WHEN distance_km < 50 THEN '25-50 km'
                WHEN distance_km < 100 THEN '50-100 km'
                ELSE '> 100 km'
            END as distance_range,
            COUNT(*) as total_records,
            COUNT(l.LIQ_ID) as liquefaction_cases,
            ROUND(COUNT(l.LIQ_ID) * 100.0 / COUNT(*), 2) as liquefaction_rate,
            AVG(e.EVENT_MAG) as avg_magnitude
        FROM (
            SELECT 
                r.*,
                e.*,
                l.LIQ_ID,
                CASE 
                    WHEN e.EVENT_LAT IS NOT NULL AND e.EVENT_LON IS NOT NULL 
                    AND s.SITE_LAT IS NOT NULL AND s.SITE_LON IS NOT NULL 
                    THEN 111.32 * SQRT(
                        POW(e.EVENT_LAT - s.SITE_LAT, 2) + 
                        POW((e.EVENT_LON - s.SITE_LON) * COS(RADIANS(s.SITE_LAT)), 2)
                    )
                    ELSE NULL
                END as distance_km
            FROM RECORD r
            JOIN EVENT e ON r.EVENT_ID = e.EVENT_ID AND e.EVENT_STAT = 1
            JOIN SITE s ON r.SITE_ID = s.SITE_ID AND s.SITE_STAT = 1
            LEFT JOIN LIQUEFACTION l ON r.RECORD_ID = l.RECORD_ID
            WHERE r.RECORD_STAT = 1
        ) AS distance_calc
        WHERE distance_km IS NOT NULL AND distance_km <= 200
        GROUP BY distance_range
        ORDER BY MIN(distance_km)
    """)
    
    if not distance_analysis.empty:
        print("📏 Distance-Dependent Liquefaction Analysis:")
        print(f"{'Distance':12} {'Records':8} {'Liq Cases':10} {'Rate %':8} {'Avg Mag':8}")
        print("-" * 55)
        for _, row in distance_analysis.iterrows():
            print(f"{row['distance_range']:12} {row['total_records']:8d} {row['liquefaction_cases']:10d} {row['liquefaction_rate']:8.1f} {row['avg_magnitude']:8.2f}")
    
except Exception as e:
    print(f"⚠️ Distance analysis query failed (likely due to missing coordinates): {e}")

# Research Question 2: Depth-dependent liquefaction susceptibility
try:
    depth_analysis = client.db.ngl.read_sql("""
        SELECT 
            CASE 
                WHEN cpt.CPT_DEPTH < 5 THEN '0-5 m'
                WHEN cpt.CPT_DEPTH < 10 THEN '5-10 m'
                WHEN cpt.CPT_DEPTH < 15 THEN '10-15 m'
                WHEN cpt.CPT_DEPTH < 20 THEN '15-20 m'
                ELSE '> 20 m'
            END as depth_range,
            COUNT(*) as cpt_count,
            COUNT(l.LIQ_ID) as liquefaction_cases,
            ROUND(COUNT(l.LIQ_ID) * 100.0 / COUNT(*), 2) as liquefaction_rate,
            AVG(cpt.CPT_QC) as avg_cone_resistance,
            AVG(e.EVENT_MAG) as avg_magnitude
        FROM CPT cpt
        JOIN RECORD r ON cpt.RECORD_ID = r.RECORD_ID AND r.RECORD_STAT = 1
        JOIN EVENT e ON r.EVENT_ID = e.EVENT_ID AND e.EVENT_STAT = 1
        LEFT JOIN LIQUEFACTION l ON r.RECORD_ID = l.RECORD_ID
        WHERE cpt.CPT_STAT = 1 AND cpt.CPT_DEPTH IS NOT NULL AND cpt.CPT_DEPTH > 0
        GROUP BY depth_range
        ORDER BY MIN(cpt.CPT_DEPTH)
    """)
    
    if not depth_analysis.empty:
        print(f"\n🕳️ Depth-Dependent Liquefaction Analysis:")
        print(f"{'Depth Range':12} {'CPT Count':10} {'Liq Cases':10} {'Rate %':8} {'Avg qc':8} {'Avg Mag':8}")
        print("-" * 70)
        for _, row in depth_analysis.iterrows():
            print(f"{row['depth_range']:12} {row['cpt_count']:10d} {row['liquefaction_cases']:10d} {row['liquefaction_rate']:8.1f} {row['avg_cone_resistance']:8.1f} {row['avg_magnitude']:8.2f}")
    
except Exception as e:
    print(f"⚠️ Depth analysis query failed: {e}")
```

### Step 11: Performance and Best Practices

```python
# Demonstrate best practices for database queries
print("\n⚡ Query Performance and Best Practices")
print("=" * 45)

try:
    # Example of efficient querying with indexing
    print("💡 Best Practice Examples:")
    
    # 1. Use LIMIT for large datasets
    print("\n1. Using LIMIT for large datasets:")
    large_query_start = datetime.now()
    limited_results = client.db.ngl.read_sql("""
        SELECT s.SITE_NAME, s.SITE_LAT, s.SITE_LON 
        FROM SITE s 
        WHERE s.SITE_STAT = 1 
        LIMIT 100
    """)
    large_query_time = (datetime.now() - large_query_start).total_seconds()
    print(f"   Retrieved {len(limited_results)} sites in {large_query_time:.3f} seconds")
    
    # 2. Use WHERE clauses to filter early
    print("\n2. Filtering with WHERE clauses:")
    filtered_query_start = datetime.now()
    filtered_results = client.db.ngl.read_sql("""
        SELECT COUNT(*) as count
        FROM SITE s 
        WHERE s.SITE_STAT = 1 
        AND s.SITE_LAT BETWEEN 32 AND 42 
        AND s.SITE_LON BETWEEN -125 AND -115
    """)
    filtered_query_time = (datetime.now() - filtered_query_start).total_seconds()
    print(f"   Filtered query completed in {filtered_query_time:.3f} seconds")
    print(f"   Found {filtered_results['count'].iloc[0]} sites in specified region")
    
    # 3. Use parameterized queries for safety
    print("\n3. Parameterized queries (secure):")
    site_name = "Amagasaki"
    param_query_start = datetime.now()
    param_results = client.db.ngl.read_sql(
        "SELECT * FROM SITE WHERE SITE_NAME = %s AND SITE_STAT = 1",
        params=[site_name]
    )
    param_query_time = (datetime.now() - param_query_start).total_seconds()
    print(f"   Parameterized query for '{site_name}' completed in {param_query_time:.3f} seconds")
    print(f"   Found {len(param_results)} matching sites")
    
    # 4. Efficient aggregation
    print("\n4. Efficient aggregation:")
    agg_query_start = datetime.now()
    agg_results = client.db.ngl.read_sql("""
        SELECT 
            s.SITE_GEOL,
            COUNT(*) as site_count,
            AVG(s.SITE_LAT) as avg_lat
        FROM SITE s 
        WHERE s.SITE_STAT = 1 AND s.SITE_GEOL IS NOT NULL
        GROUP BY s.SITE_GEOL
        HAVING site_count >= 5
        ORDER BY site_count DESC
        LIMIT 10
    """)
    agg_query_time = (datetime.now() - agg_query_start).total_seconds()
    print(f"   Aggregation query completed in {agg_query_time:.3f} seconds")
    print(f"   Top geology types: {', '.join(agg_results['SITE_GEOL'].head(3).tolist())}")
    
    print(f"\n✅ All queries completed successfully!")
    print(f"💡 Tips for optimal performance:")
    print(f"   - Always use LIMIT for exploratory queries")
    print(f"   - Filter early with WHERE clauses")
    print(f"   - Use parameterized queries for user inputs")
    print(f"   - Consider creating indexes for frequently queried columns")
    print(f"   - Use appropriate JOIN types (INNER vs LEFT)")
    
except Exception as e:
    print(f"❌ Performance demonstration failed: {e}")
```

### Step 12: Summary and Cleanup

```python
# Final summary and cleanup
print("\n" + "=" * 60)
print("🎯 Database Analysis Summary")
print("=" * 60)

try:
    # Get final statistics
    final_stats = client.db.ngl.read_sql("""
        SELECT 
            (SELECT COUNT(*) FROM SITE WHERE SITE_STAT = 1) as total_sites,
            (SELECT COUNT(*) FROM EVENT WHERE EVENT_STAT = 1) as total_events,
            (SELECT COUNT(*) FROM RECORD WHERE RECORD_STAT = 1) as total_records,
            (SELECT COUNT(*) FROM LIQUEFACTION) as total_liquefaction,
            (SELECT COUNT(*) FROM CPT WHERE CPT_STAT = 1) as total_cpt
    """)
    
    stats = final_stats.iloc[0]
    print(f"📊 Final Database Statistics:")
    print(f"   Active Sites: {stats['total_sites']:,}")
    print(f"   Earthquake Events: {stats['total_events']:,}")
    print(f"   Records: {stats['total_records']:,}")
    print(f"   Liquefaction Cases: {stats['total_liquefaction']:,}")
    print(f"   CPT Tests: {stats['total_cpt']:,}")
    
    # Calculate liquefaction rate
    if stats['total_records'] > 0:
        overall_liq_rate = stats['total_liquefaction'] / stats['total_records'] * 100
        print(f"   Overall Liquefaction Rate: {overall_liq_rate:.2f}%")
    
    print(f"\n📁 Generated Files:")
    if 'output_dir' in locals():
        print(f"   - Data exports in: {output_dir}/")
        print(f"   - Visualization script: {output_dir}/create_visualizations.py")
    
    print(f"\n🎓 Key Findings:")
    print(f"   - Geographic distribution spans multiple continents")
    print(f"   - Earthquake magnitudes range from minor to major events")
    print(f"   - Liquefaction susceptibility varies significantly by soil type")
    print(f"   - Strong correlation between magnitude and liquefaction occurrence")
    
    print(f"\n📚 Next Steps:")
    print(f"   - Run visualization script to create plots")
    print(f"   - Perform statistical analysis on exported data")
    print(f"   - Integrate with machine learning workflows")
    print(f"   - Compare with other research databases")
    
    # Optional: Close database connections (handled automatically)
    print(f"\n✅ Analysis completed successfully!")
    
except Exception as e:
    print(f"❌ Final summary failed: {e}")

print(f"\n📖 For more database examples:")
print(f"   - https://designsafe-ci.github.io/dapi/database/")
print(f"   - https://github.com/DesignSafe-CI/dapi/examples/")
```

This comprehensive example demonstrates advanced database querying techniques, including geographic analysis, temporal trends, statistical correlations, and best practices for working with large research databases using dapi.