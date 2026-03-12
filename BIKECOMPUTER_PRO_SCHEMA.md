# BikeComputer Pro backup_sessions.db Schema
# BikeComputer Pro backuped_sessions.db Schema

## Overview
BikeComputer Pro stores all ride data in an SQLite database that backs up to Google Drive automatically. This is an ideal data source for extracting performance history without any external APIs.

## Key Tables for Performance Extraction

### 1. sessions table (one row per ride)
```sql
_id              INTEGER PRIMARY KEY autoincrement
starttime        LONG            -- Unix timestamp, ride start
sessiontime      LONG            -- Duration in milliseconds (moving + paused)
pauseTime        LONG            -- Total pause time in milliseconds
distance         FLOAT           -- Total distance in ? (VERIFY: km or meters)
topspeed         FLOAT           -- Max speed in ? (likely km/h)
average          FLOAT           -- Average speed in ? (likely km/h)
meters           INTEGER         -- Elevation gain in meters (NOT distance!)
overalltime      LONG            -- Total elapsed time ms (includes pauses)
title            TEXT            -- Ride name
bike             TEXT            -- Bike type
cat              INTEGER         -- Category
calories         INTEGER         
used_bike        INTEGER         -- FK to bikes table
heartavg         INTEGER         -- Avg heart rate bpm
heartmax         INTEGER         -- Max heart rate bpm
pow_avg          INTEGER         -- Avg power watts
pow_max          INTEGER         -- Max power watts
url              TEXT            -- Strava/external link
hasTrack         INTEGER         -- Boolean: has GPS track
hasUpdatedElevation INTEGER      -- Boolean: elevation corrected
withBarometer    INTEGER         -- Boolean: barometer used
```

### 2. tracks table (one row per GPS point)
```sql
_id              INTEGER PRIMARY KEY autoincrement
lat              INTEGER         -- Latitude (VERIFY: *1e6 or *1e7 format)
lon              INTEGER         -- Longitude (VERIFY: *1e6 or *1e7 format)
elev             INTEGER         -- Elevation in meters
time             INTEGER         -- Timestamp, milliseconds since session start
session_id       INTEGER         -- FK to sessions._id
heartrate        INTEGER         -- Heart rate bpm (optional)
power            INTEGER         -- Power watts (optional)
temperature      INTEGER         -- Temperature celsius (optional)
cadence          INTEGER         -- Cadence RPM (optional)
```

### 3. settings table (user profile)
```sql
yourWeight       FLOAT           -- Weight in kg
yourHeight       INTEGER         -- Height in cm
age              INTEGER         -- Age in years
PREFS_MILES      INTEGER         -- Boolean: prefer miles over km
PREFS_CELSIUS    INTEGER         -- Boolean: prefer celsius
```

### 4. bikes table (bike definitions)
```sql
_id              INTEGER PRIMARY KEY
name             TEXT            -- Bike name
diameter         INTEGER         -- Wheel diameter mm
weight           FLOAT           -- Bike weight kg
air_res          FLOAT           -- Air resistance coefficient
roll_res         FLOAT           -- Rolling resistance coefficient
overall_dist     INTEGER         -- Total km on this bike
```

### 5. importlocations table (useful for stop detection!)
```sql
_id              INTEGER PRIMARY KEY
lat              INTEGER
lon              INTEGER
name             TEXT            -- Stop/checkpoint name (audax control!)
session_id       INTEGER         -- FK to sessions._id
```

## Data Extraction Plan

### Phase 7 Implementation - backup_sessions.db Parser
### Phase 7 Implementation - backuped_sessions.db Parser

**Step 1**: Load all sessions
```python
import sqlite3

def load_sessions(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT _id, starttime, distance, meters, average, topspeed,
               sessiontime, pauseTime, heartavg, pow_avg
        FROM sessions
        ORDER BY starttime DESC
    """)
    return cursor.fetchall()
```

**Step 2**: For each session, load trackpoints and calculate speed-at-gradient
```python
def load_trackpoints(conn, session_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT lat, lon, elev, time
        FROM tracks
        WHERE session_id = ?
        ORDER BY time
    """, (session_id,))
    return cursor.fetchall()

def calculate_speed_by_gradient(trackpoints):
    """
    For each pair of trackpoints:
    - Distance = haversine(lat1, lon1, lat2, lon2)
    - Elevation delta = elev2 - elev1
    - Gradient% = (elev_delta / distance_delta) * 100
    - Speed = distance_delta / time_delta
    
    Then group by gradient band and average speeds.
    """
    # Implementation details in Phase 7
```

**Step 3**: Create RidePerformance record
```python
ride_perf = RidePerformance(
    user_id=current_user.id,
    ride_date=datetime.fromtimestamp(session['starttime'] / 1000),
    distance_km=session['distance'],  # May need /1000 if in meters
    elevation_gain_m=session['meters'],
    moving_time_minutes=(session['sessiontime'] - session['pauseTime']) / 60000,
    stopped_time_minutes=session['pauseTime'] / 60000,
    speed_flat_kmh=gradient_speeds[0],
    speed_rolling_up_kmh=gradient_speeds[1],
    speed_rolling_down_kmh=gradient_speeds[2],
    speed_moderate_climb_kmh=gradient_speeds[3],
    speed_steep_climb_kmh=gradient_speeds[4],
    speed_steep_down_kmh=gradient_speeds[5],
)
```

## VERIFICATION NEEDED

Before implementing, verify these assumptions by running:

```sql
-- Check sample data to verify units
SELECT _id, distance, meters, average, topspeed FROM sessions LIMIT 1;

-- Check user preferences
SELECT yourWeight, PREFS_MILES FROM settings;

-- Check trackpoint format (lat/lon scale)
SELECT lat, lon FROM tracks LIMIT 3;
```

**Questions to answer**:
1. Is `distance` in kilometers (e.g., 205.5) or meters (e.g., 205500)?
2. Is `average`/`topspeed` in km/h or m/s?
3. Are `lat`/`lon` in degrees (e.g., 53.123456) or scaled (e.g., 53123456)?
4. Is `meters` definitely elevation gain (should be 1000-3500 for your rides)?

## Privacy & Data Handling

**Data Extraction** (keep in RidePerformance):
- ✅ ride_date (date only, not time)
- ✅ distance_km
- ✅ elevation_gain_m
- ✅ moving_time_minutes
- ✅ stopped_time_minutes
- ✅ speed_*_kmh (aggregated by gradient band)
- ✅ fatigue_rate_per_10km (calculated from speed decay)

**Data to Drop** (NOT stored; processed then discarded):
- ❌ lat/lon (GPS coordinates - location privacy)
- ❌ exact timestamps (just keep ride date)
- ❌ ride name/title (could indicate location)
- ❌ URL (third-party link)
- ❌ temperature (combined with location = identification)

**Optional** (user can enable/disable):
- ? heartrate (Article 9 health data - require explicit consent)
- ? power data (biometric data - require explicit consent)

## Testing Data

Your data appears to have:
- Multiple rides with various distances (up to 200km+ likely)
- Trackpoints with elevation data
- Stop times recorded
- Possibly audax rides with named checkpoints (importlocations table)

This is perfect for building accurate performance curves!

## Next Steps

1. ✅ Schema discovered
2. ⏳ Run verification queries (see VERIFICATION NEEDED above)
3. ⏳ Implement Phase 7: backup_sessions.db parser
3. ⏳ Implement Phase 7: backuped_sessions.db parser
4. ⏳ Test with actual data import
5. ⏳ Calculate UserFatigueCurve from 5-10 rides
6. ⏳ Display in web UI
