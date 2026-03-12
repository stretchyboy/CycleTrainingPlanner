# CycleTrainingPlanner Refresh Plan

## Project Overview

Modernize the CycleTrainingPlanner - a Python tool that generates progressive cycling training plans for endurance events. Currently hardcoded with 2020 data and outputs only to VeloHero browser tabs. Goal: Make it usable for other people while maintaining privacy-by-design.

## Current State

### Repository Structure
- `planner.py` - Single 156-line script with all logic
- `README.md` - Minimal ("Create training plans fast")
- Branches: `master`, `gui`, `Installable`, `gpx`

### Existing Functionality
- Calculates progressive weekly training plans based on:
  - Current fitness level (weekly mileage)
  - Target event (distance, duration, elevation)
  - Basic route inputs (if provided)
  - Training period (start/end weeks)
  - Rest cycles, taper, plateau periods
- Splits weeks into: commutes, main ride, secondary ride
- Generates VeloHero goal URLs (opens in browser tabs)

### New Findings From This Refresh
- Multiple historical plan variants exist (2020, 2022, 2023, 2024) with different rules
- BikeComputer Pro backup covers 2023-05-06 to 2026-02-04 (SQLite sessions)
- VeloHero JSON exports exist back to at least 2017-04-23 and are smaller to parse than GPX
- Event matching needs a configurable window and multi-day selection (e.g., 2-day events)
- Planned event routes are now available as GPX in `routes/`

### Key Issues
- All parameters hardcoded (2020 target year)
- No user input mechanism
- Disabled credentials in code (security concern)
- No data persistence
- Single output format (VeloHero URLs)
- No error handling
- Monolithic script structure

### Target Events & Prediction Requirements (NEW)
Target events are the anchor for every plan. We need structured support for:
- Event identity: name, date, organizer (optional)
- Event goals: target duration, target distance, target elevation
- Route detail levels:
  - Summary only: distance + elevation (e.g., 200km / 3000m)
  - Waypoints: control points or key locations (routing between)
  - Official GPX route from the organizer (most precise)
- Predictions:
  - Predicted event time based on performance curves
  - Gap to target time (how much improvement is required)
- Weekly targets:
  - Distance targets and climbing targets that map to event demands
  - Progression of climbing volume toward event elevation

### **CRITICAL UPDATE: VeloHero Service Closing**
**Issue**: VeloHero (http://app.velohero.com) is shutting down, removing the original output method.

**Impact**:
- Can't rely on VeloHero for goal tracking
- Can't import historical ride data from VeloHero
- Need self-contained goal tracking in the web app
- Need alternative data import paths

**Current Data Sources**:
- **BikeComputer Pro** (https://bikecomputer-pro.andro.io/) - Android cycling computer in use
- Previously: VeloHero → Tapiriik sync (no longer viable)
- Need: Direct import from BikeComputer Pro or alternative platforms

**Additional Available Data**:
- **VeloHero JSON exports** (compact per-ride summaries + samples)
- **Event route GPX** files in `routes/` for planned targets

**Solution Required**:
1. Build goal tracking into the web app (replace VeloHero dependency)
2. Support backuped_sessions.db import from Google Drive
3. Support GPX/FIT file uploads as a fallback

## Privacy & PII Considerations (UK GDPR)

### Data Types & Classification

**Type 1: Historical Training GPX (Speed @ Gradient)**
- Extract: Speed at gradients, distance, date (aggregated)
- Do NOT store: GPS coordinates, precise times, locations
- Classification: Potentially health-related data if authenticated
- Risk: LOW if properly anonymized (can't reverse-engineer locations)
- Requirement: Privacy policy if stored with authentication

**Type 2: Future Route GPX (Planning)**
- Store: Route geometry for planning purposes
- No activity history, just intended routes
- Classification: Minimal/no PII (similar to bookmarked routes)
- Risk: VERY LOW
- Requirement: Basic privacy notice

**Type 3: Historical Performance Data (Essential for Modeling) ⭐ BETTER APPROACH**
- Extract from past rides: Speed at gradient (up AND down), fatigue curves, stop patterns
- Do NOT store: Weight, age, gender, biometrics (not needed!)
- Classification: Regular personal data (activity history, not health data)
- Why it works: Your own ride data predicts YOUR capabilities better than weight formulas
- GDPR burden: LOW

**Key Performance Modeling Parameters** (based on audax riding):
- **Granularity**: 10km slices (not 50km) - allows fine-grained fatigue tracking
- **Starting point**: Works with 20km training rides initially
- **Fatigue rate**: ~0.6% per 10km (12% over 200km) - realistic for endurance riding
- **Gradient tracking**: UP (flat, 2-5%, 5-8%, 8%+) AND DOWN (-2 to -5%, -5%+) - descents matter!
- **Stop prediction**: ~3 minutes per 20km for eating/audax checkpoints - for TIME accounting, not recovery
- **Recovery**: Minimal from short stops (20 minutes max) - just time accounting
- **Realistic speeds**: 15 km/h on 5% climbs (audax pace), not elite racing speeds

**Your insight**: Instead of weight-based modeling, use **actual performance history**
- Map performance at different gradients (up AND down): "You do 15 km/h on 5% climbs, 35 km/h on -5% descents"
- Model fatigue decay in 10km slices: "Every 10km, you lose ~0.6% speed at any gradient"
- Account for stops: "You stop ~3 minutes per 20km for food/checkpoints (time accounting, minimal recovery)"
- Predict future: Use this curve to adjust weekly targets = no weight data needed

### Historical Performance Data: Compliance Options

Extract and store performance history from Type 1 GPX instead of weight data. This is **better legally AND technically**:

---

#### **Option 1: Latest Performance Snapshot (LIGHTWEIGHT)**
**Compliance Burden**: 🟢 MINIMAL | **Data Utility**: 🟡 MEDIUM | **User Control**: ⭐⭐⭐⭐⭐

**What You Store** (NO weight data):
- Last uploaded ride's performance curves
- Speed at each gradient range: "You averaged 18 km/h on 5% climbs in last ride"
- Fatigue factor: "You're ~3% slower per 50km ridden"
- NO historical archive, just latest snapshot

**Legal Basis**: "Legitimate Interest" (activity history analysis)
- ✅ Full legal clarity - NOT health data, it's activity data
- ✅ No consent needed (like storing training data normally)
- ✅ Zero DPIA required
- ✅ User controls: can delete, upload new ride anytime

**Database Schema**:
```python
class UserPerformanceSnapshot(db.Model):
    """Latest known performance from most recent ride"""
    user_id: Mapped[str] = mapped_column(db.String(100), primary_key=True)
    
    # Latest ride metadata
    last_ride_date: Mapped[datetime] = mapped_column()
    last_ride_distance_km: Mapped[float] = mapped_column()
    
    # Performance at each gradient (speed in km/h) - both up and down
    speed_flat_kmh: Mapped[float] = mapped_column()  # -2% to +2%
    speed_rolling_up_kmh: Mapped[float] = mapped_column()  # 2-5% climb
    speed_moderate_climb_kmh: Mapped[float] = mapped_column()  # 5-8% climb
    speed_steep_climb_kmh: Mapped[float] = mapped_column()  # 8%+ climb
    speed_rolling_down_kmh: Mapped[float] = mapped_column()  # -2% to -5% descent
    speed_steep_down_kmh: Mapped[float] = mapped_column()  # -5%+ descent
    
    # Fatigue curve (how speed changes over distance in 10km slices)
    fatigue_rate_per_10km: Mapped[float] = mapped_column(default=0.006)  # 0.6% decay per 10km
    
    calculated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

**How You Use It**:
- User uploads first 20km ride (starting point)
- Extract: "15 km/h on 5% sections, 10 km/h on 10% sections, 35 km/h on descents"
- Calculate: "You fade ~0.6% per 10km (at 100km: 15 * (1 - 0.006*10) = 14.1 km/h on 5% climbs)"
- Plan target: "Week 3 long ride: 160km with 2000m - expect avg moving speed ~22 km/h (with stops, 9-10 hours total)"

**Privacy Statement**:
> "When you upload a ride file, we analyze your performance at different gradients and how your speed changes over the ride distance. We store only the summary (speed at each gradient), not GPS location data. This helps us predict realistic targets for your plan. You can delete this anytime."

**Trade-offs**:
- ✅ Zero legal complexity
- ✅ Accurate to YOUR actual capability
- ✅ Self-learns from your rides
- ✅ Completely privacy-safe (no weight!)
- ❌ Needs at least one uploaded ride
- ❌ Can't show long-term trends

---

#### **Option 2: Performance History with Fatigue Modeling (RECOMMENDED) ⭐**
**Compliance Burden**: 🟢 MINIMAL | **Data Utility**: 🟢 HIGH | **User Control**: ⭐⭐⭐⭐

**What You Store** (NO weight data):
- Last 12 months of ride summaries
- Performance at each gradient for each ride
- Fitted fatigue curve: "You fade X% per 50km on average"
- Seasonal patterns: "You're stronger in summer"
- NO coordinates, NO timestamps, NO location data

**Legal Basis**: Activity history analysis
- ✅ Not health data - it's fitness activity data
- ✅ Simple privacy notice (covers activity history)
- ✅ No DPIA required
- ✅ Standard GDPR rights apply (delete, export)

**Database Schema**:
```python
class RidePerformance(db.Model):
    """Each uploaded ride's performance analysis"""
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(db.String(100), ForeignKey('user_profile.user_id'))
    
    ride_date: Mapped[datetime] = mapped_column()
    total_distance_km: Mapped[float] = mapped_column()
    total_elevation_m: Mapped[float] = mapped_column()
    total_time_minutes: Mapped[int] = mapped_column()
    stop_time_minutes: Mapped[int] = mapped_column(default=0)  # For time prediction, not recovery
    
    # Performance (speed km/h at each gradient band) - UP and DOWN
    speed_flat_kmh: Mapped[float] = mapped_column()  # -2% to +2%
    speed_rolling_up_kmh: Mapped[float] = mapped_column()  # 2-5% up
    speed_moderate_climb_kmh: Mapped[float] = mapped_column()  # 5-8% up
    speed_steep_climb_kmh: Mapped[float] = mapped_column()  # 8%+ up
    speed_rolling_down_kmh: Mapped[float] = mapped_column()  # -2% to -5% down
    speed_steep_down_kmh: Mapped[float] = mapped_column()  # -5%+ down
    
    analyzed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

class UserFatigueCurve(db.Model):
    """Your learned fatigue pattern from ride history"""
    user_id: Mapped[str] = mapped_column(db.String(100), primary_key=True)
    
    # Speed at distance X = baseline * (1 - fatigue_rate * (distance_km / 10))
    # e.g., audax rider doing 15 km/h on fresh 5% climbs with 0.6% decay per 10km:
    # At 100km: 15 * (1 - 0.006 * 10) = 14.1 km/h
    # At 200km: 15 * (1 - 0.006 * 20) = 13.2 km/h
    fatigue_rate_per_10km: Mapped[float] = mapped_column(default=0.006)
    
    # Stop time prediction (minutes per distance unit)
    avg_stop_minutes_per_20km: Mapped[float] = mapped_column(default=3.0)  # For eating/checkpoints
    
    # Recovery after stops (minimal for short audax stops)
    recovery_factor_after_stop: Mapped[float] = mapped_column(default=1.0)  # No real recovery from 20-min stops
    
    # Seasonal adjustment (multiplier for current season vs baseline)
    seasonal_multiplier: Mapped[float] = mapped_column(default=1.0)
    
    curve_from_date: Mapped[datetime] = mapped_column()
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

**How You Use It**:
- User uploads Ride 1: "200km with 3000m, averaged 15 km/h on 5% sections"
- User uploads Ride 2 (3 weeks): Same route, "15.5 km/h (improving!)"
- System detects: "You fade ~0.6% per 10km (12% total over 200km)"
- Plan generation: "Week 4's 300km target: Starting pace 15 km/h → expect 13.2 km/h by 200km mark"
- Trend report: "You're 3% faster than 3 months ago"
- Stop prediction: "200km ride = ~10 stops × 3 min = 30 min stopped time, plus moving time = 10-11 hours total"

**Privacy Statement**:
> "We analyze your ride history (last 12 months) to understand your performance at different gradients and how fatigue affects your pace. We extract only: speed at each gradient and time into ride. We do NOT store GPS location, route names, or precise timestamps. You can request deletion of your ride history anytime."

**Trade-offs**:
- ✅ Not health data - it's activity history
- ✅ Minimal legal burden
- ✅ Excellent accuracy after 3-5 rides
- ✅ Shows user their progress/trends
- ✅ No weight data needed!
- ❌ Needs 3-5 rides minimum
- ❌ Can't extrapolate to completely new distances instantly

---

#### **Option 3: Full Performance Analytics (Advanced)**
**Compliance Burden**: 🟢 MINIMAL | **Data Utility**: 🟢 EXCELLENT |  **User Control**: ⭐⭐⭐⭐

**What You Store**:
- Option 2 plus:
- User's optional notes: "Felt strong today", "New bike", "Recovering from illness"
- Optional weather context from API (temperature, wind speed/direction, rain, road wetness)
- Detailed weekly trends and weekly context
- Calculate: "You're 5% stronger on new wheels"

**Legal Basis**: Activity history with optional contextual metadata
- ✅ Still just activity data
- ✅ Notes are user-provided
- ✅ Zero health classification
- ✅ Same privacy notice coverage

**How You Use It**:
- Show trend: "You're trending 4% stronger than last month"
- Identify patterns: "You perform 3% better in Tuesday group rides vs solo"
- Identify weather impact: "Headwinds reduce your rolling speed by ~2 km/h"
- Detect improvements: "You recovered 5% power after rest week"
- Plan adaptation: "Based on your forms trends, I'm suggesting next week be easier"
- User sees: "Your best 5% performance was in summer, averaging..."

**Trade-offs**:
- ✅ Best modeling accuracy
- ✅ Users love seeing precise trends
- ✅ Still zero compliance burden
- ✅ Self-learning gets smarter weekly
- ❌ More data to manage

---

#### **Option 4: Route Planning Algorithm (Future Enhancement) 🚀**
**Compliance Burden**: 🟢 MINIMAL | **Data Utility**: 🟢 EXCELLENT | **User Control**: ⭐⭐⭐⭐⭐

**What You Build**:
Audax route planner that uses your actual performance data to optimize routes:

**Inputs**:
- Target distance (e.g., 200km)
- Target elevation (e.g., 3000m)
- Your performance curves from ride history
- Road/path network with elevation data

**Routing Algorithm**:
- Use speed-at-gradient as **cost function** for each road segment
- Account for fatigue accumulation (every 10km, speeds decrease)
- Add stop time (3 min per 20km for food/checkpoints)
- Minimize total time (moving + stopped)
- Constraint: Must pass audax checkpoints

**Example**:
- Option A: Flat route, 200km, 500m elevation = 7h moving + 30 min stops = 7.5h total
- Option B: Hilly route, 180km, 3000m elevation = 8h moving + 27 min stops = 8.5h total
- Algorithm picks fastest based on YOUR speed curves, not generic formulas

**Advanced Features** (later):
- Recovery modeling between multi-day rides
- Weather impact (headwind costs)
- Road surface quality
- Traffic/safety scoring
- "Find me the fastest 300km route with 3500m climbing"

**Database Schema**:
```python
class Route(db.Model):
    """Route with elevation profile"""
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(db.String(100), ForeignKey('user_profile.user_id'))
    
    name: Mapped[str] = mapped_column()
    total_distance_km: Mapped[float] = mapped_column()
    total_elevation_m: Mapped[float] = mapped_column()
    
    # Predicted performance using user's curves
    predicted_moving_time_minutes: Mapped[int] = mapped_column()
    predicted_stop_time_minutes: Mapped[int] = mapped_column()
    predicted_total_time_minutes: Mapped[int] = mapped_column()
    
    # Gradient profile (JSON)
    gradient_distribution: Mapped[dict] = mapped_column(JSON)
    # e.g., {"flat": 80km, "rolling_up": 40km, "moderate_climb": 30km, ...}
    
    # Route geometry (simplified, no personal data)
    gpx_data: Mapped[str] = mapped_column(db.Text, nullable=True)

class RouteSegment(db.Model):
    """Individual segment with gradient and predicted speed"""
    id: Mapped[int] = mapped_column(primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey('route.id'))
    
    segment_order: Mapped[int] = mapped_column()  # Position in route
    distance_km: Mapped[float] = mapped_column()
    gradient_pct: Mapped[float] = mapped_column()
    
    # Predicted for this user at this point in ride
    distance_into_ride_km: Mapped[float] = mapped_column()  # Fatigue calculation
    predicted_speed_kmh: Mapped[float] = mapped_column()  # Based on gradient + fatigue
    predicted_time_minutes: Mapped[float] = mapped_column()
```

**Routing Cost Function**:
```python
def calculate_segment_time(user_perf: UserFatigueCurve, 
                           segment_gradient: float,
                           distance_into_ride: float) -> float:
    """Calculate time for a segment based on user's actual performance"""
    
    # Get base speed for this gradient
    base_speed = user_perf.get_speed_for_gradient(segment_gradient)
    
    # Apply fatigue based on distance into ride (10km slices)
    fatigue_multiplier = 1 - (user_perf.fatigue_rate_per_10km * (distance_into_ride / 10))
    
    # Predicted speed at this point
    predicted_speed = base_speed * fatigue_multiplier
    
    # Time = distance / speed
    return segment.distance / predicted_speed

def optimize_route(start, end, constraints, user_perf):
    """Find fastest route using user's performance curves"""
    # Dijkstra's algorithm with custom cost = time (not distance)
    # Cost of each road segment = predicted time based on user's speed curves
    pass
```

**Privacy Implications**:
- ✅ Routes are planning (Type 2 GPX) - low PII
- ✅ Uses performance curves (already stored)
- ✅ No new consent needed
- ✅ User controls which routes to save

**Implementation Roadmap**:
1. **Phase 1** (Option 2): Build performance curve extraction
2. **Phase 2** (Option 3): Add detailed analytics and trends
3. **Phase 3** (Option 4): Build route cost calculator
4. **Phase 4**: Integrate with routing API (GraphHopper, OSRM)
5. **Phase 5**: Multi-day planning with proper recovery modeling

**Trade-offs**:
- ✅ Incredibly useful for audax planning
- ✅ Personalized to YOUR capability
- ✅ Accounts for fatigue accumulation
- ✅ Predicts real total time (moving + stops)
- ❌ Complex to build (routing algorithms)
- ❌ Needs road network with elevation data
- ❌ Compute-intensive for large areas

---

### Recommendation for Your System

**Development Progression**:

1. **Start with Performance History + Fatigue Modeling (10km slices)**:
  - Build models from user's ride history starting with 20km rides
  - After 3-5 uploads, have accurate fatigue curve
  - Show users their trends
  - Zero legal complexity
  - Track up AND down gradient performance
  - Predict stop times (time accounting, not recovery)

2. **Add Full Analytics (Optional)**:
  - User notes ("felt strong", "new bike")
  - Detailed weekly trends
  - Pattern detection

3. **Build toward Route Planning Algorithm (Optional)**:
  - Use actual speed-on-gradient data as routing costs
  - Account for fatigue accumulation (10km slices)
  - Predict total time (moving + stops)
  - Optimize audax routes for YOUR capability
  - Future: Multi-day planning with proper recovery

**No weight input ever required** - you have everything you need in the GPX files!

---

### Implementation: Performance History (Recommended)

Add to models.py:
```python
class RidePerformance(db.Model):
    """Analysis of each uploaded ride"""
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(db.String(100), ForeignKey('user_profile.user_id'))
    
    ride_date: Mapped[datetime] = mapped_column()
    total_distance_km: Mapped[float] = mapped_column()
    total_elevation_m: Mapped[float] = mapped_column()
    total_time_minutes: Mapped[int] = mapped_column()
    stop_time_minutes: Mapped[int] = mapped_column(default=0)
    
    # Speed at each gradient band (km/h) - UP and DOWN
    speed_flat_kmh: Mapped[float] = mapped_column()  # -2% to +2%
    speed_rolling_up_kmh: Mapped[float] = mapped_column()  # 2-5% up
    speed_moderate_climb_kmh: Mapped[float] = mapped_column()  # 5-8% up  
    speed_steep_climb_kmh: Mapped[float] = mapped_column()  # 8%+ up
    speed_rolling_down_kmh: Mapped[float] = mapped_column()  # -2% to -5% down
    speed_steep_down_kmh: Mapped[float] = mapped_column()  # -5%+ down

    # Optional weather context (API-sourced)
    weather_context: Mapped[dict] = mapped_column(JSON, nullable=True)
    # Example: {"temperature_c": 12.3, "wind_speed_kmh": 18, "wind_dir_deg": 240, "rain": true, "road_wet": true}
    
    analyzed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

class UserFatigueCurve(db.Model):
    """Your personal fatigue/pacing pattern"""
    user_id: Mapped[str] = mapped_column(db.String(100), primary_key=True)
    
    # How much do you slow down per 10km?
    fatigue_rate_per_10km: Mapped[float] = mapped_column(default=0.006)  # 0.6% per 10km
    
    # Stop time prediction (minutes per 20km for food/checkpoints)
    avg_stop_minutes_per_20km: Mapped[float] = mapped_column(default=3.0)
    
    # Recovery factor after stops (minimal for short audax stops)
    recovery_factor: Mapped[float] = mapped_column(default=1.0)  # No real recovery
    
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

**Privacy Policy Addition**:
```markdown
## Ride Analysis and Performance Tracking

When you upload ride files (GPX format), we analyze your performance to improve 
your training plan recommendations. We extract:

- Your speed at different gradient ranges (both up and down)
- How your pace changes over ride duration (fatigue patterns)
- Stop patterns for time prediction (food stops, checkpoints)

We do NOT store or extract:
- GPS coordinates or route locations
- Timestamps or precise timing data
- Any personal location information
- Your home or work address

This data helps us predict realistic training targets based on YOUR actual 
fitness and pacing patterns, not generic formulas.

You can delete all your ride analysis history anytime from your settings.
```

**Example: Audax 200km with 3000m Ride Prediction**
```python
# User's learned performance (from 5 previous rides)
user_perf = UserFatigueCurve(
    fatigue_rate_per_10km=0.006,  # 0.6% per 10km
    avg_stop_minutes_per_20km=3.0
)

# User's base speeds on fresh legs
base_speeds = {
    "flat": 28,      # km/h on flat
    "rolling_up": 22,  # km/h on 2-5% climbs
    "moderate_climb": 15,  # km/h on 5-8% climbs
    "steep_climb": 10,  # km/h on 8%+ climbs
    "rolling_down": 35,  # km/h on -2 to -5% descents
    "steep_down": 40,  # km/h on -5%+ descents
}

# Route: 200km, 3000m elevation
# Breakdown: 80km flat, 40km rolling up, 30km moderate climb, 10km steep, 40km descents

# Predictions at different points:
# At 0km: Full speed
# At 100km: 6% fatigue = base * 0.94
# At 200km: 12% fatigue = base * 0.88

# Moving time calculation:
# Early pace (0-100km, avg 6% fatigue): ~9h moving
# Late pace (100-200km, avg 12% fatigue): ~10h moving total

# Stop time: 200km / 20km * 3min = 30 minutes

# Total predicted time: 10h moving + 0.5h stopped = 10.5 hours
# This matches your actual 200km/3000m audax performance!
```

### Why This Works

✅ **No weight data**: You have everything from GPX speed/gradient analysis  
✅ **Not health data**: It's activity history  
✅ **Minimal compliance**: Just activity history privacy notice  
✅ **Better accuracy**: Uses user's actual performance, not formulas  
✅ **Self-improving**: Model gets smarter with each uploaded ride  
✅ **Zero DPIA needed**: Not stored as health data  

This is your best approach - well thought out!
- ❌ Higher breach notification liability

---

#### **Option 3: Pseudonymized Analytics (Aggregate Only)**
**Compliance Burden**: 🟢 LOW | **Data Utility**: 🟡 MEDIUM-HIGH | **User Control**: ⭐⭐⭐⭐⭐

**What You Store**:
- Individual weight/FTP data stored, but hashed/linked to unique ID, not name
- Historical trends calculated locally, only aggregates sent to analytics
- "In your weight class (70-79kg), average W/kg is 3.2" (no individual data revealed)
- Never return individual user's full health history to anyone else

**Legal Basis**: "Legitimate Interest" (system improvement) + simple notice
- ✅ No DPIA needed (pseudonymized per GDPR Article 32)
- ✅ Simple one-checkbox consent
- ✅ Easy to implement, minimal compliance burden
- ✅ Can still show personal trends to user

**Database Schema**:
```python
class UserHealth(db.Model):
    # Stored normally for individual use
    user_id: Mapped[str] = mapped_column(db.String(100), primary_key=True)
    weight_kg: Mapped[float] = mapped_column()
    ftp_watts: Mapped[float] = mapped_column()
    recorded_date: Mapped[datetime] = mapped_column()

class AggregateHealthStats(db.Model):
    # Analytics only - weight classes, averages, trends
    weight_class: Mapped[str] = mapped_column()  # "70-79kg"
    ftp_class: Mapped[str] = mapped_column()  # "3.0-3.5 W/kg"
    average_w_kg: Mapped[float] = mapped_column()
    percentile: Mapped[int] = mapped_column()  # 50th percentile
    count: Mapped[int] = mapped_column()  # How many users in this class
    calculated_date: Mapped[datetime] = mapped_column()
```

- ✅ Fully privacy-safe
- ❌ Less accurate modeling (categories vs real data)
- ❌ Can't show W/kg or personal metrics
- ❌ Can't track progress over time

---

### Comparison Matrix

### Recommended Approach: Privacy-by-Design

**For CycleTrainingPlanner v1.0: Use performance history only**

- No weight or health data required
- No special consent or DPIA
- Modeling accuracy based on real ride performance
- Simplifies privacy policy and user onboarding
- Is stored securely and encrypted at rest
- Is never shared with third parties
- Is visible only to you
- Can be deleted anytime by clearing your profile
- Is used only to estimate your power zones and training load

You may opt-out by leaving these fields blank. The plan will use default 
estimates instead.
```

### Recommended Approach: Privacy-by-Design (Flask Web App + Web-Based Storage)

For your web-based system with external authentication:

**Data to store in database**:
1. ✅ Training plans (per-user) - Required for functionality
2. ✅ Weekly progressions (weeks, workouts) - Required
3. ✅ Future routes (Type 2 GPX) - Low PII risk, user bookmarks routes
4. ✅ Aggregate metrics (no coordinates/timestamps) - Privacy-safe, useful for modeling
5. ✅ Performance history only (no weight data)

**What to extract but NOT store**:
- GPS coordinates/location data (one-time processing)
- Precise timestamps from GPX files
- User address or home/work locations
- Individual ride metadata that could identify location

**Privacy guarantees**:
- Encrypted at rest (database password protection)
- User can delete everything (cascade deletes in models)
- Right to export in portable format (JSON API endpoint)
- No third-party sharing (not sold, not tracked for ads)
- Simple privacy policy (template included in Flask starter)

## Data Import Strategy (NEW - Critical for Performance Modeling)

**Problem**: VeloHero is closing, can't import historical ride data from there anymore.

**Current Setup**:
- User rides with **BikeComputer Pro** (https://bikecomputer-pro.andro.io/) Android app
- **BikeComputer Pro backs up sessions to Google Drive** (key discovery!)
- Backup file: `backuped_sessions.db` (SQLite database)
- Previously uploaded to VeloHero → synced to Tapiriik (no longer viable)
- Need direct import path for performance analysis

### Priority 1: BikeComputer Pro backuped_sessions.db (EASIEST)

**Why This is Perfect**:
- ✅ SQLite database (we know how to parse it)
- ✅ Bulk historical data (all your rides in one file)
- ✅ Stores elevation, coordinates, speed data
- ✅ Already backed up to Google Drive automatically

**Implementation Process**:
1. User downloads `backuped_sessions.db` from Google Drive
2. User uploads to web app (/performance/import-backup)
3. App parses with `sqlite3` library
4. Extracts all sessions with performance data
5. **Privacy-safe extraction**: Strip GPS, keep aggregates only
6. Stores in `RidePerformance` model (one record per ride)
7. Calculates `UserFatigueCurve` from aggregate data

**Required Research**:
- SQLite schema of `backuped_sessions.db`
  - Table names (likely: `sessions`, `records`, `trackpoints`, etc.)
  - Column names (distance, elevation, speed, duration, timestamp?)
  - Data types and valid ranges
  - Any obfuscated/encoded fields?
- What fields are in each ride record?
- How is elevation stored (points vs aggregated)?
- How is speed calculated (GPS points vs recorded values)?

**Implementation Code Pattern**:
```python
import sqlite3

def parse_backuped_sessions(db_file_path, user_id):
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    
    # Query all sessions
    cursor.execute("SELECT * FROM sessions")  # table name TBD
    sessions = cursor.fetchall()
    
    for session in sessions:
        # Extract ONLY these fields per ride:
        ride = RidePerformance(
            user_id=user_id,
            ride_date=session['date'],  # Track date
            distance_km=session['distance'],
            elevation_gain_m=session['elevation'],
            moving_time_minutes=session['moving_time'],
            # Calculate speed_at_gradient from trackpoints
            speed_flat_kmh=calculate_speed_at_gradient(session, 0, 2),
            speed_rolling_up_kmh=calculate_speed_at_gradient(session, 2, 5),
            speed_moderate_climb_kmh=calculate_speed_at_gradient(session, 5, 8),
            speed_steep_climb_kmh=calculate_speed_at_gradient(session, 8, 100),
            speed_rolling_down_kmh=calculate_speed_at_gradient(session, -5, 0),
            speed_steep_down_kmh=calculate_speed_at_gradient(session, -100, -5)
        )
        # DO NOT store: GPS coordinates (lat/lon), exact timestamps, route name
        db.session.add(ride)
    
    conn.close()
    db.session.commit()
```

### Priority 2: GPX File Upload (Fallback & Supplement)
**For users who**:
- Don't have backuped_sessions.db access
- Want to import individual rides from other sources
- Want to supplement backup data with newer rides

**Supported Formats**: GPX, FIT, TCX (any standard cycling format)
**Sources**: Any GPX/FIT/TCX export

**Implementation**: See Phase 7 (same GPX processing code)

### Priority 3: VeloHero JSON Import (NEW - Compact Historical Source)

**Why This Helps**:
- Much smaller than GPX
- Includes distance, ascent, duration, ride type
- Good for long-term history back to 2017

**Implementation**:
- Accept JSON directory export
- Parse only summary fields (`date_ymd`, `dist_km`, `asc_m`, `dur_time`, `type_name`)
- Ignore `samples` for privacy unless explicitly enabled

### Planned Routes Integration (NEW)

**Use Case**: Tie each plan to a known event route GPX and compare planned vs actual.

**Plan-to-Route Mapping**:
- Config file (example `routes_map.json`)
- Allows multi-day events (two GPX files)

**Route Metrics**:
- Distance km
- Ascent m
- Optional: gradient distribution (future)

## Recommendation: Hybrid Strategy

**Phase 7 Implementation** (Week 3-4):
1. **First Priority**: Upload/parse `backuped_sessions.db` from Google Drive
   - Bulk import of all historical rides at once
   - Most complete data source
   - SQLite parsing (no external API needed)

2. **Second Priority**: Manual GPX upload form
   - For individual rides not in backup
   - For rides from other sources
   - As supplement for newer rides

3. **Future** (Phase 9+): Optional enhancements
  - Lower priority since backuped_sessions.db exists

## Output Format Strategy

### Phase 1: File Exports (No Authentication Required)

#### 1. iCalendar (.ics) - PRIORITY 1
**Effort**: 30 minutes | **Library**: `icalendar` or string formatting

**Features**:
- 3 events per week (overall goal, commute goal, long ride)
- Description: distance, duration, elevation, workout count
- Import into: Google Calendar, Apple Calendar, Outlook
- Most universal format

**Implementation**:
```python
def generate_ical(plan_data, filename):
    # Create VCALENDAR
    # For each week: create 3 VEVENTs
    # SUMMARY, DTSTART, DTEND, DESCRIPTION
    # Write to .ics file
```

#### 2. CSV Export - PRIORITY 2
**Effort**: 15 minutes | **Library**: Built-in `csv`

**Columns**: Week, Date Range, Total Distance, Commute Dist, Main Ride, Second Ride, Duration, Elevation, Rest Week

**Use case**: Spreadsheet analysis, data portability

#### 3. JSON Export
**Effort**: 5 minutes | **Library**: Built-in `json`

**Use case**: Custom integrations, API development

#### 4. Event Summary Export (NEW)
**Effort**: 30 minutes | **Library**: `csv`, `json`

**Outputs**:
- Per-plan event summary CSV/JSON
- Includes event day metrics and % vs plan target
- Includes recovery comparison for multi-day events

## Architecture: Flask Web App with Database Storage

### Decision: Use python-web-oauth-orm-rest-starter as Base

**Repository**: https://github.com/UTCSheffield/python-web-oauth-orm-rest-starter

**Rationale**:
- Proven OAuth authentication (Auth0 + GitHub)
- SQLAlchemy ORM already configured
- REST API with Swagger docs (Flask-RESTX)
- Per-user data isolation built-in
- Admin interface (Flask-Admin)
- Privacy policy template included
- Render deployment ready
- Supports SQLite (local) → PostgreSQL (production)

**What We'll Add**:
- Training plan calculation engine (from existing planner.py)
- Database models: Plan, Week, Workout, Route, TargetEvent
- Web UI for creating/viewing plans
- Export endpoints (iCal, CSV, JSON)
- GPX processing for route analysis

### Target Event Model (NEW)
Target events are first-class objects. Plans are created *for* a target event.

```python
class TargetEvent(db.Model):
  """Event the user is training for"""
  id: Mapped[int] = mapped_column(primary_key=True)
  user_id: Mapped[str] = mapped_column(db.String(100), ForeignKey('user_profile.user_id'))

  name: Mapped[str] = mapped_column()
  event_date: Mapped[datetime] = mapped_column()

  # Goal targets
  target_distance_km: Mapped[float] = mapped_column()
  target_elevation_m: Mapped[int] = mapped_column()
  target_duration_minutes: Mapped[int] = mapped_column(nullable=True)  # Optional

  # Route detail level
  route_type: Mapped[str] = mapped_column(default='summary')
  # 'summary' | 'waypoints' | 'gpx'
  route_waypoints: Mapped[dict] = mapped_column(JSON, nullable=True)
  # Waypoint format: [{"name": "Control 1", "lat": 53.12345, "lon": -1.23456}, ...]
  route_gpx_data: Mapped[str] = mapped_column(db.Text, nullable=True)

  # Predictions (computed on plan generation)
  predicted_moving_time_minutes: Mapped[int] = mapped_column(nullable=True)
  predicted_stop_time_minutes: Mapped[int] = mapped_column(nullable=True)
  predicted_total_time_minutes: Mapped[int] = mapped_column(nullable=True)

  created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

**Plan Relationship**:
- Plan has `target_event_id` foreign key
- Plan generation uses event distance/elevation/route detail
- Predicted time is computed from performance curves and stored on the event

### Target Event Prediction & Weekly Targets (NEW)
Given a target event, the system should:
- Predict the user's likely completion time (moving + stops)
- Compare prediction vs target time to find improvement gap
- Translate gap into weekly targets (distance and climbing progression)

**Example**:
- Event: 200km, 3000m, target 10h 00m
- Predicted from curves: 10h 30m
- Gap: 30 minutes (5% improvement)
- Weekly targets adjusted to close the gap:
  - Increase weekly climbing by +5-8% per block
  - Add hill repeats or climbing-focused long ride segments

**Output Fields (derived)**:
- `predicted_total_time_minutes`
- `target_duration_minutes`
- `target_gap_minutes` = predicted - target
- `required_improvement_pct` = gap / target
- `weekly_climb_target_m` (derived from event elevation and training window)

### Adaptive Plan Tweaks (NEW)

As actuals roll in and event predictions update, the system suggests focused tweaks that are most likely to improve the gap. Examples:
- "Find more routes with 5% climbs" if climbing deficit is the main limiter
- "Add one extra rolling-hill session per week" if moderate gradients are weak
- "Prioritize long-ride duration" if time-on-bike is the limiting factor

**Inputs**:
- Target event route profile (gradient distribution)
- Actual weekly performance vs plan (distance, climb, duration)
- Updated prediction gap (time/pace)

**Output**:
- Ranked list of 2-3 suggested tweaks for the next block
- Each tweak tied to a measurable metric (e.g., +X km at 5-8% grade)

**Ranking Rubric (example)**:
- Score = (prediction gap %) × (route share for that gradient band) × (recent compliance shortfall)
- Prefer the smallest number of tweaks that cover the biggest weighted gaps
- Avoid repeating the same tweak if compliance is already high in that area

**Starter Weights (proposal)**:
- prediction gap weight: 0.5
- route gradient share weight: 0.3
- recent compliance shortfall weight: 0.2

**Example scoring**:
```text
score = 0.5 * gap_pct + 0.3 * route_share_pct + 0.2 * shortfall_pct
```

### Proposed Structure

```
CycleTrainingPlanner/
├── app.py                      # Main Flask app (from starter)
├── auth/                       # OAuth authentication (from starter)
│   ├── __init__.py
│   ├── auth0.py
│   └── github.py
├── models.py                   # NEW: Training plan database models
├── planner.py                  # NEW: Core calculation logic (refactored)
├── plans.py                    # NEW: Blueprint for plan CRUD routes
├── api.py                      # Extended: REST API for plans
├── exporters.py                # NEW: Export to iCal, CSV, JSON
├── gpx_processor.py            # NEW: GPX analysis
├── admin.py                    # Extended: Admin for plans (from starter)
├── schemas.py                  # NEW: Marshmallow schemas for validation
├── templates/
│   ├── layout.html             # From starter
│   ├── privacy.html            # Extended privacy policy
│   ├── plans_list.html         # NEW: List user's plans
│   ├── plan_create.html        # NEW: Form to create plan
│   ├── plan_view.html          # NEW: View/edit plan details
│   └── plan_export.html        # NEW: Export options
├── static/
│   ├── style.css
│   └── plan_chart.js           # NEW: Visualize progression
├── tests/
│   ├── test_app.py             # From starter
│   ├── test_planner.py         # NEW: Test calculations
│   ├── test_exporters.py       # NEW: Test exports
│   └── test_api.py             # NEW: Test API endpoints
├── requirements.txt            # Extended dependencies
├── render.yaml                 # From starter
├── README.md
├── .env.example
└── .gitignore
```

### Core Classes

```python
class TrainingPlan:
    """Represents a complete training plan"""
    def __init__(self, config):
        self.plan_name = config.plan_name
        self.weeks = []
        
    def calculate(self):
        """Generate week-by-week plan"""
        
    def get_week(self, week_number):
        """Get specific week data"""

class Week:
    """Represents one week of training"""
    def __init__(self, week_number, date_range):
        self.week_number = week_number
        self.date_range = date_range
        self.total_distance = 0
        self.commute_distance = 0
        self.main_ride = 0
        self.second_ride = 0
        self.duration = 0
        self.elevation = 0
        self.is_rest_week = False
        
class TrainingPlanExporter:
    """Base exporter class"""
    def __init__(self, plan):
        self.plan = plan
        
    def export(self):
        raise NotImplementedError

class ICalExporter(TrainingPlanExporter):
    def export(self, filename):
        """Generate .ics file"""
```

### Web Interface

#### User Flow

1. **Login** (Auth0/GitHub OAuth) → User authenticated
2. **Dashboard** → List of user's plans
3. **Create Target Event** → Name, date, distance, elevation, target time, route detail
4. **Create Plan** → Form with training parameters linked to target event
4. **Calculate** → Server generates Week records
5. **View Plan** → Week-by-week table + chart
6. **Export** → Buttons for iCal/CSV/JSON
7. **GPX Upload** (optional) → Analyze route for elevation profile

#### GPX-First UX Notes (Updated)

Most users will only have GPX files (or no route yet). The primary flow must work with summary inputs and template presets, then allow later refinement:

- **Start with summary targets**: distance + climb only (no route required)
- **Starter presets**: e.g., "Hilly 100km Audax", "Flat 200km Audax", "Commuter Base"
- **Later refinement**: upload a GPX route or adjust target event info
- **Recalculate**: plan can be edited and recalculated when better info arrives or new events are added

#### Core Screens (Priority)
- Plan (create/edit/recalculate)
- Upload/sync ride data (GPX + backuped_sessions.db)
- Monitor progress against plan (weekly + event comparisons)

#### Starter Presets (Draft)
- **Hilly 100km Audax**:
  - Target: 100km / 1500m, target time 6h
  - Duration: 12 weeks, rest cycle 4 weeks, taper 2 weeks, plateau 1 week
  - Progression: target week 130%, target ride 65%, second ride 30%
  - Commute split: 8 commutes/week, long commute 15km, max long commutes 1
- **Flat 200km Audax**:
  - Target: 200km / 1200m, target time 12h
  - Duration: 16 weeks, rest cycle 4 weeks, taper 2 weeks, plateau 1 week
  - Progression: target week 135%, target ride 60%, second ride 35%
  - Commute split: 10 commutes/week, long commute 20km, max long commutes 1
- **Hilly 200km Audax**:
  - Target: 200km / 3000m, target time 14h
  - Duration: 18 weeks, rest cycle 4 weeks, taper 2 weeks, plateau 1 week
  - Progression: target week 140%, target ride 60%, second ride 35%
  - Commute split: 10 commutes/week, long commute 20km, max long commutes 2
- **Commuter Base Build**:
  - Target: 150km/week, 500m/week climb, target time 7h
  - Duration: 8 weeks, rest cycle 4 weeks, taper 1 week, plateau 0 weeks
  - Progression: target week 120%, target ride 50%, second ride 25%
  - Commute split: 10 commutes/week, long commute 15km, max long commutes 1
- **Couch-to-100km**:
  - Target: 100km / 800m, target time 7h
  - Duration: 12 weeks, rest cycle 3 weeks, taper 1 week, plateau 0 weeks
  - Progression: target week 125%, target ride 60%, second ride 25%
  - Commute split: 6 commutes/week, long commute 12km, max long commutes 1

#### Key Routes (plans.py Blueprint)

```python
@plans_bp.route('/')
def list_plans():
    """Show all plans for logged-in user"""
    user = get_current_user()
    plans = Plan.query.filter_by(user_id=user['id']).all()
    return render_template('plans_list.html', plans=plans)

@plans_bp.route('/create', methods=['GET', 'POST'])
def create_plan():
    """Form to create new plan"""
    if request.method == 'POST':
    # TargetEvent created earlier or created inline
        plan = Plan(
            user_id=session['user_id'],
            name=request.form['name'],
      target_event_id=int(request.form['target_event_id']),
            # ...
        )
        db.session.add(plan)
        db.session.flush()
        
        # Calculate weeks
        calculator = TrainingPlanCalculator(plan)
        calculator.save_to_database()
        
        return redirect(url_for('plans.view_plan', plan_id=plan.id))
    
    return render_template('plan_create.html')

  @plans_bp.route('/events/create', methods=['GET', 'POST'])
  def create_event():
    """Create a target event"""
    if request.method == 'POST':
      event = TargetEvent(
        user_id=session['user_id'],
        name=request.form['name'],
        event_date=request.form['event_date'],
        target_distance_km=float(request.form['target_distance_km']),
        target_elevation_m=int(request.form['target_elevation_m']),
        target_duration_minutes=request.form.get('target_duration_minutes') or None,
        route_type=request.form.get('route_type', 'summary'),
      )
      db.session.add(event)
      db.session.commit()
      return redirect(url_for('plans.create_plan'))

    return render_template('event_create.html')

@plans_bp.route('/<int:plan_id>')
def view_plan(plan_id):
    """View plan details"""
    user = get_current_user()
    plan = Plan.query.filter_by(id=plan_id, user_id=user['id']).first_or_404()
    return render_template('plan_view.html', plan=plan)

@plans_bp.route('/<int:plan_id>/export/ical')
def export_ical(plan_id):
    """Download .ics file"""
    plan = Plan.query.filter_by(id=plan_id, user_id=session['user_id']).first_or_404()
    exporter = ICalExporter()
    ical_data = exporter.export(plan)
    return Response(ical_data, mimetype='text/calendar', 
                    headers={'Content-Disposition': f'attachment; filename={plan.name}.ics'})
```

#### REST API (Extended api.py)

```python
# api.py (extend from starter)
@api.route('/plans')
class PlanList(Resource):
    @api.marshal_list_with(plan_model)
    def get(self):
        """List all plans for current user"""
        user = require_auth()
        plans = Plan.query.filter_by(user_id=user['id']).all()
        return plan_schema.dump(plans, many=True)
    
    @api.expect(plan_input, validate=True)
    @api.marshal_with(plan_model, code=201)
    def post(self):
        """Create new plan"""
        user = require_auth()
        data = request.get_json()
        plan = Plan(user_id=user['id'], **data)
        db.session.add(plan)
        db.session.flush()
        
        calculator = TrainingPlanCalculator(plan)
        calculator.save_to_database()
        
        return plan_schema.dump(plan), 201

@api.route('/plans/<int:plan_id>/weeks')
class WeekList(Resource):
    @api.marshal_list_with(week_model)
    def get(self, plan_id):
        """Get all weeks for a plan"""
        user = require_auth()
        plan = Plan.query.filter_by(id=plan_id, user_id=user['id']).first_or_404()
        return week_schema.dump(plan.weeks, many=True)
```

## Implementation Phases

### Phase 1: Setup Flask Starter (Week 1, Days 1-2)
- [ ] Clone python-web-oauth-orm-rest-starter to new branch
- [ ] Test local setup with GitHub OAuth
- [ ] Verify database creation and admin interface
- [ ] Deploy to Render with Auth0
- [ ] Confirm authentication flow works
- [ ] Study existing code structure (models, routes, API, admin)

### Phase 2: Core Models & Calculation (Week 1, Days 3-5)
- [ ] Create models.py with Plan, Week, Workout, Route, TargetEvent models
- [ ] Refactor existing planner.py calculation logic into TrainingPlanCalculator class
- [ ] Remove hardcoded values, use Plan model attributes
- [ ] Update year handling to be dynamic (2026+)
- [ ] Add event prediction step:
  - [ ] Predict target event time from performance curves
  - [ ] Calculate gap to target duration (improvement needed)
  - [ ] Derive weekly distance/climbing targets to close the gap
- [ ] Write unit tests for calculation accuracy
- [ ] Add database migrations if using Alembic

### Phase 3: Web UI for Plans (Week 2, Days 1-3)
- [ ] Create plans.py blueprint
- [ ] Create templates:
  - [ ] plans_list.html (dashboard)
  - [ ] event_create.html (target event form)
    - [ ] Name, date, target duration
    - [ ] Distance + elevation summary
    - [ ] Route type selector: summary | waypoints | gpx
    - [ ] GPX upload (if route type = gpx)
    - [ ] Waypoints input (if route type = waypoints)
      - [ ] Each waypoint: name + lat/lon (control point)
  - [ ] plan_create.html (training parameters + link to target event)
  - [ ] plan_view.html (week-by-week table)
- [ ] Add form validation (Marshmallow schemas)
- [ ] Integrate calculation engine on form submission
- [ ] Display weeks in responsive table
- [ ] Add simple chart (Chart.js) showing progression
- [ ] Test CRUD operations

### Phase 4: REST API Extension (Week 2, Days 4-5)
- [ ] Extend api.py with plan endpoints
- [ ] Add Marshmallow schemas for Plan, Week, Workout
- [ ] Implement GET /api/plans (list user's plans)
- [ ] Implement POST /api/plans (create plan)
- [ ] Implement GET /api/plans/{id} (get plan details)
- [ ] Implement GET /api/plans/{id}/weeks (get weeks)
- [ ] Implement DELETE /api/plans/{id}
- [ ] Add TargetEvent endpoints:
  - [ ] GET /api/events (list user's events)
  - [ ] POST /api/events (create target event)
  - [ ] GET /api/events/{id} (event details + predictions)
  - [ ] DELETE /api/events/{id}
- [ ] Test API with Swagger docs at /api/
- [ ] Add API authentication checks

### Phase 5: Export System & Goal Tracking (Week 3, Days 1-3) **EXPANDED**
- [ ] **PRIORITY**: Create WorkoutCompletion model in models.py
- [ ] **PRIORITY**: Add completion tracking UI to plan_view.html
  - [ ] \"Mark Complete\" button for each workout
  - [ ] Form: actual distance, duration, elevation, notes
  - [ ] Progress indicators (completed/overdue/upcoming)
- [ ] Add POST /plans/{id}/workouts/{workout_id}/complete route
- [ ] Create exporters.py module
- [ ] Implement ICalExporter class
- [ ] Implement CSVExporter class
- [ ] Implement JSONExporter class
- [ ] Add export routes to plans.py:
  - [ ] GET /plans/{id}/export/ical
  - [ ] GET /plans/{id}/export/csv
  - [ ] GET /plans/{id}/export/json
- [ ] Add export buttons to plan_view.html
- [ ] Test all export formats

### Phase 6: Enhanced Tracking Views (Week 3, Days 3-5) **EXPANDED**
- [ ] **NEW**: Add calendar view (/plans/{id}/calendar)
  - [ ] Month/week grid with color-coded workouts
  - [ ] Green = completed, Red = overdue, Blue = upcoming
  - [ ] Click day to see/complete workouts
  - [ ] Mobile-responsive design
- [ ] **NEW**: Add progress dashboard (/plans/{id}/progress)
  - [ ] Total planned vs actual distance/elevation charts
  - [ ] Weekly compliance percentage
  - [ ] Fatigue indicators (over/under target warnings)
  - [ ] Use Chart.js for visualizations

### Phase 7: GPX Integration & Performance Tracking (Week 3-4) **UPDATED WITH SCHEMA**
- [ ] Create gpx_processor.py module
- [ ] **PRIORITY 1: backuped_sessions.db Import** (SQLite → RidePerformance)
  - [ ] Add import form at /performance/import-backup
  - [ ] Accept SQLite backuped_sessions.db file from Google Drive
  - [ ] Parse sessions table:
    ```sql
    SELECT _id, starttime, distance, meters, average, topspeed, 
           sessiontime, pauseTime, overalltime FROM sessions
    ```
  - [ ] For each session, process all trackpoints:
    ```sql
    SELECT lat, lon, elev, time FROM tracks WHERE session_id = :session_id ORDER BY time
    ```
  - [ ] Calculate speed at each gradient band from trackpoints:
    - Use haversine formula (lat/lon → distance)
    - Calculate gradient % = (elev_delta / distance_delta) * 100
    - Group trackpoints by gradient band
    - Average speed for each band → store in RidePerformance
    - [ ] Optional: Attach weather context from API
      - Temperature (C), wind speed (km/h), wind direction (deg)
      - Rain flag and road wetness indicator (if provided)
      - Store in weather_context JSON on RidePerformance
  - [ ] Extract fields for RidePerformance model:
    - ride_date = datetime from starttime
    - distance_km = distance (convert if needed)
    - elevation_gain_m = meters 
    - moving_time_minutes = (sessiontime - pauseTime) / 60000
    - stopped_time_minutes = pauseTime / 60000
    - speed_*_kmh fields (from trackpoint analysis)
  - [ ] **PRIVACY**: Drop lat/lon, exact timestamps, ride name, URLs
  - [ ] Store in RidePerformance model (one record per session)
  - [ ] Bulk import all sessions at once
  - [ ] Display import progress + success/error count
  - [ ] Validate data sanity (distance > 0, elevation valid, speeds reasonable)
- [ ] **PRIORITY 2: Manual GPX/FIT Upload** (for users without backup, or newer rides)
  - [ ] Add upload form at /performance/upload
  - [ ] Accept GPX/FIT files from BikeComputer Pro or other sources
  - [ ] Parse with gpxpy library (standard GPX format)
  - [ ] Extract performance data (same gradient analysis as backup import)
  - [ ] Store in RidePerformance model
  - [ ] **PRIVACY**: Strip GPS coordinates, timestamps, route names
- [ ] Create UserFatigueCurve model
  - [ ] Calculate personalized fatigue curve from 3-5 uploaded rides
  - [ ] Fit exponential decay: speed_at_X_km = baseline_speed * (1 - fatigue_rate * (X / 10))
  - [ ] Store fatigue_rate_per_10km (default 0.006)
- [ ] Display performance summary at /performance/summary
  - [ ] Table: All imported rides (date, distance, elevation, moving time, gradient speeds)
  - [ ] Chart: Speed fade over distance (fatigue curve)
  - [ ] Stats: Avg speed by gradient, personal records, trends
- [ ] Implement Type 2: Route GPX processing (for plan routes, separate from performance)
  - [ ] Parse GPX file with gpxpy library
  - [ ] Extract elevation profile
  - [ ] Calculate gradient distribution (% of distance at each gradient band)
  - [ ] Store in Route model with plan association
  - [ ] NO trackpoint storage (just aggregated profiles)
- [ ] Use event GPX route (if provided) to compute predicted event time
- [ ] Add GPX upload to plan_create.html form (optional - for route planning)
- [ ] Display route analysis in plan_view.html
  - [ ] Show gradient distribution chart
  - [ ] Show elevation profile
  - [ ] Adjust weekly progressions based on route difficulty
  - [ ] Show predicted target times at 50km, 100km etc based on user's performance curve
  - [ ] Show predicted target times at marked waypoints or tops of climbs etc. on user's performance curve
  - [ ] Optional: Show weather context if route date is known (historical weather API)
- [ ] Add RidePerformance management to admin interface
  - [ ] View all imported rides
  - [ ] Delete individual rides
  - [ ] Re-calculate UserFatigueCurve
- [ ] **TESTING** (critical for Phase 7):
  - [ ] Export backuped_sessions.db from BikeComputer Pro
  - [ ] Verify units (km vs m, seconds vs ms) with sample query
  - [ ] Test import with 5-10 rides
  - [ ] Verify gradient speed calculations (sanity check)
  - [ ] Test GPX upload with BikeComputer Pro GPX exports
  - [ ] Test GPX upload with other sources
- [ ] Document in README:
  - [ ] How to export backuped_sessions.db from BikeComputer Pro (Google Drive → Settings)
  - [ ] How to export individual rides as GPX
  - [ ] Privacy notice (what data is kept/dropped)
  - [ ] Data schema documentation for developers

### Phase 8: Polish & Documentation (Week 4)
- [ ] Comprehensive README with examples
- [ ] Usage guide for each export format
- [ ] Privacy policy template (if auth added)
- [ ] Example configurations for common events
  - Century ride (100mi)
  - Double century (200mi)
  - Multi-day tours
  - Commuter training
- [ ] Screenshots/examples of outputs
- [ ] Contribution guidelines
- [ ] License file (choose appropriate license)

### Phase 9: Optional Advanced Features (Future)
- [ ] Cloud sync of plans (with proper privacy)
- [ ] Mobile app considerations (PWA or native)
- [ ] **BikeComputer Pro Direct Integration** (if API becomes available)

## Data Sources Research Needed

### BikeComputer Pro backuped_sessions.db Database Schema - DISCOVERY COMPLETE ✅

**Found**: User has downloaded the backuped_sessions.db file. Schema discovered!

**Key Tables**:

#### 1. **sessions** table (one row = one ride)
```sql
_id              INTEGER PRIMARY KEY
starttime        LONG            -- Unix timestamp (milliseconds?)
sessiontime      LONG            -- Ride duration in milliseconds
pauseTime        LONG            -- Total pause/stop time in milliseconds
distance         FLOAT           -- Total distance (likely kilometers)
topspeed         FLOAT           -- Max speed (km/h)
average          FLOAT           -- Average speed (km/h)
meters           INTEGER         -- Elevation gain in meters (NOT distance!)
overalltime      LONG            -- Total elapsed time in milliseconds
title            TEXT            -- Ride name/title
bike             TEXT            -- Bike used (text)
cat              INTEGER         -- Category ID
calories         INTEGER         -- Energy burned
used_bike        INTEGER         -- Bike ID (FK to bikes table)
heartavg         INTEGER         -- Avg heart rate (bpm)
heartmax         INTEGER         -- Max heart rate (bpm)
pow_avg          INTEGER         -- Avg power (watts)
pow_max          INTEGER         -- Max power (watts)
url              TEXT            -- External URL
hasTrack         INTEGER         -- Boolean: has GPS track
hasUpdatedElevation INTEGER      -- Boolean: elevation corrected
withBarometer    INTEGER         -- Boolean: has barometer data
```

#### 2. **tracks** table (one row = one GPS point)
```sql
_id          INTEGER PRIMARY KEY
lat          INTEGER          -- Latitude (*1e6 or *1e7 format, needs verification)
lon          INTEGER          -- Longitude (*1e6 or *1e7 format, needs verification)
elev         INTEGER          -- Elevation in meters
time         INTEGER          -- Timestamp offset from session start (milliseconds?)
session_id   INTEGER          -- Foreign key to sessions table
heartrate    INTEGER          -- Heart rate (bpm)
power        INTEGER          -- Power (watts)
temperature  INTEGER          -- Celsius
cadence      INTEGER          -- RPM
```

#### 3. **bikes** table (bike definitions)
```sql
name          TEXT
diameter      INTEGER         -- Wheel diameter (mm)
weight        FLOAT           -- Bike weight (kg)
air_res       FLOAT           -- Air resistance coefficient
roll_res      FLOAT           -- Rolling resistance coefficient
overall_dist  INTEGER         -- Lifetime km on this bike
```

#### 4. **Other useful tables**
- **importlocations**: Stop locations with lat/lon/names (checkpoint detection!)
- **waypoints**: Marked waypoints during rides
- **settings**: User preferences including `yourWeight`, `yourHeight`, `age`, `PREFS_MILES`, `PREFS_CELSIUS`

### Data Extraction Strategy

**What We Extract for Performance History**:
```python
EXTRACT_FOR_RIDEPERFORMANCE = {
    'ride_date': starttime,              # Date of ride
    'distance_km': distance,             # Total distance
    'elevation_gain_m': meters,          # Elevation gain
    'moving_time_minutes': (sessiontime - pauseTime) / 60000,  # Moving time
    'stopped_time_minutes': pauseTime / 60000,                  # Stop time
    'speed_flat_kmh': calculate_from_tracks(0, 2),            # Speed gradient 0-2%
    'speed_rolling_up_kmh': calculate_from_tracks(2, 5),      # Speed gradient 2-5%
    'speed_moderate_climb_kmh': calculate_from_tracks(5, 8),  # Speed gradient 5-8%
    'speed_steep_climb_kmh': calculate_from_tracks(8, 100),   # Speed gradient 8%+
    'speed_rolling_down_kmh': calculate_from_tracks(-5, 0),   # Speed gradient -2 to -5%
    'speed_steep_down_kmh': calculate_from_tracks(-100, -5),  # Speed gradient -5%+
}

DROP_FOR_PRIVACY = {
    'lat', 'lon',               # GPS coordinates (not needed for performance)
    'time' (exact),             # GPS timestamps (only keep ride date)
    'title',                    # Ride name (could be location)
    'url',                      # External URLs (location leakage)
    'temperature',              # Optional - combined with location could identify
}

OPTIONAL_STORE = {
    'heartrate': heartavg,      # Heart rate - Article 9 health data (optional)
    'power': pow_avg,           # Power data - biometric (optional)
    'cadence': calculate_avg,   # RPM (non-sensitive)
}
```

**How to Calculate Speed-at-Gradient**:
1. For each trackpoint pair, calculate:
   - Distance delta = haversine(lat1, lon1, lat2, lon2)
   - Elevation delta = elev2 - elev1
   - Gradient % = (elevation delta / distance delta) * 100
   - Speed = distance delta / time delta
2. Group all trackpoints by gradient band
3. Calculate average speed for each band
4. Example: All segments with 5-8% gradient → average those speeds → `speed_moderate_climb_kmh`

**Stop Detection**:
- pauseTime field in sessions table directly gives us total stops!
- Optional: Query importlocations table to find named stops (audax control points)

### Implementation Notes

**Units to Verify** (by running: `sqlite3 backuped_sessions.db "SELECT distance, meters, average FROM sessions LIMIT 1;"`):
- `distance`: Confirm if in km or meters
- `meters`: Confirm if in meters or feet
- `average`: Confirm if km/h or m/s
- `lat/lon`: Confirm if *1e6 or *1e7 format (typical for Android)

**Haversine Function** (calculate lat/lon distance):
```python
from math import radians, sin, cos, acos
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    return R * acos(sin(lat1)*sin(lat2) + cos(lat1)*cos(lat2)*cos(lon1-lon2))
```

**Performance** (1000+ trackpoints per ride):
- May need indexed SQL queries for speed
- Consider batch processing (import X rides at a time)
- Cache calculations if user imports 50+ rides

## Built-in Goal Tracking (NEW - Priority 1)

**Reason**: The app must be self-contained for goal tracking.

### Features Required
1. **Calendar View** - Display all workouts for current month/week
2. **List View** - Upcoming workouts with details
3. **Progress Tracking** - Mark workouts as completed with actual performance
4. **Completion Status** - Visual indicators (✓ completed, ⚠ overdue, ○ upcoming)
5. **Performance Comparison** - Planned vs actual (distance, duration, elevation)
6. **Mobile-Responsive** - Use on phone during/after rides

### Database Schema Addition
```python
class WorkoutCompletion(db.Model):
    __tablename__ = 'workout_completions'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    workout_id: Mapped[int] = mapped_column(ForeignKey('workouts.id', ondelete='CASCADE'))
    
    completion_date: Mapped[datetime]
    actual_distance_km: Mapped[float]
    actual_duration_minutes: Mapped[int]
    actual_elevation_m: Mapped[int] = mapped_column(nullable=True)
    
    # Optional link to uploaded ride file
    ride_performance_id: Mapped[int] = mapped_column(
        ForeignKey('ride_performances.id', ondelete='SET NULL'), 
        nullable=True
    )
    
    notes: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

### UI Components
1. **Weekly View** (`/plans/{id}/week/{week_num}`)
   - Show all 3 workout goals for that week
   - "Mark Complete" button with form (distance, time, elevation, notes)
   - Progress bar showing week completion % 

2. **Calendar Integration** (`/plans/{id}/calendar`)
   - Month/week grid view
   - Color-coded: green (completed), red (overdue), blue (upcoming)
   - Click day to see/complete workouts

3. **Progress Dashboard** (`/plans/{id}/progress`)
   - Total planned vs actual distance/elevation
   - Chart showing weekly compliance
   - Fatigue indicators if consistently over/under target

### Implementation Priority
- **Phase 3** (Week 2): Basic completion tracking (mark done, manual entry)
- **Phase 6** (Week 3-4): Calendar view, progress charts
- **Phase 7** (Week 3-4): Auto-fill from uploaded GPX files

## Testing Strategy

### Unit Tests
- Calculation accuracy (progressive overload, rest weeks, taper)
- Date handling (week ranges, ISO weeks)
- Export format validation (valid iCal, valid CSV)
- Configuration parsing

### Integration Tests
- Full plan generation with various parameters
- Export to all formats

### Manual Testing
- Test plans with sample configs:
  - Short plan (4 weeks)
  - Long plan (20+ weeks)
  - Various rest cycle patterns
  - Different commute configurations
- Import .ics into Google Calendar, Apple Calendar
- Import CSV into Excel/Sheets
- Validate multi-day event matching (windowed + consecutive day selection)
- Validate route GPX metrics vs actual event days

## Documentation Requirements

### README.md Sections
1. **Overview** - What is CycleTrainingPlanner?
2. **Installation** - pip install, requirements
3. **Quick Start** - Simplest example
4. **Configuration** - All parameters explained
5. **Export Formats** - How to use each format
6. **GPX Analysis** - How to use route planning
7. **Privacy** - Data handling explanation
8. **Examples** - Common training plans
9. **Contributing** - How to contribute
10. **License** - License information

### Example Training Plans to Include
- **Century Training** (12 weeks, 50→100 miles)
- **Double Century** (20 weeks, 75→200 miles)
- **Commuter Fitness** (8 weeks, improving daily commute endurance)
- **Multi-day Tour Prep** (16 weeks, back-to-back long days)

## Security & Privacy Checklist

- [ ] Remove all hardcoded credentials
- [ ] Add .env support for optional secrets
- [ ] Never log sensitive data
- [ ] Document data handling in README
- [ ] Add privacy notice if collecting any user data
- [ ] Ensure GPX coordinate stripping works correctly
- [ ] Add warnings before any cloud uploads
- [ ] Make local-first the default behavior

## Branch Merge Strategy

### Recommended Order
1. **Installable branch** - Establish package structure first
2. **GUI branch** - Add user interface layer
3. **GPX branch** - Add advanced features last

### Merge Process
```bash
# 1. Check out and review each branch
git checkout Installable
git log --oneline -10
git diff master..Installable

# 2. Identify conflicts and useful additions
# 3. Create feature branches from master
git checkout master
git checkout -b feature/package-structure
# Cherry-pick or merge specific commits

# 4. Test each integration independently
# 5. Merge to master when stable
```

## Success Criteria

### Minimum Viable Product (MVP)
- [ ] Flask web app running with SQLAlchemy ORM
- [ ] Auth0 or GitHub OAuth authentication working
- [ ] User can create target event (name, date, distance, elevation, route waypoints)
- [ ] API generates training plan from target event (Phases 1-4)
- [ ] Exports functional: iCal, CSV, JSON
- [ ] Event summary export (CSV/JSON)
- [ ] Route GPX comparison for planned vs actual event days
- [ ] Adaptive plan tweak suggestions based on prediction gaps
- [ ] Imports backuped_sessions.db and calculates RidePerformance metrics
- [ ] Database schema deployed (SQLite dev, PostgreSQL prod)
- [ ] Weather API integration for historical performance data
- [ ] Deployed to cloud (Heroku, Railway, or self-hosted)
- [ ] No hardcoded credentials, environment-based config
- [ ] Unit tests for plan algorithm and data models
- [ ] README with deployment and setup instructions

### Full Release (Phase 5+)
- [ ] Route planning with GPX support (Phase 4)
- [ ] Advanced analytics with fatigue curves and gradient analysis (Phase 3)
- [ ] Workout completion tracking against planned targets
- [ ] iCal sync for multi-device calendar integration
- [ ] Test coverage >80% for core logic
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Privacy policy and GDPR compliance documented

## Open Questions & Decisions Needed

1. **Weather API Provider**: OpenWeatherMap, Weatherstack, Weatherapi.com, SMHI, or custom? (Cost vs coverage vs privacy trade-off)
2. **Database Migration**: Use Alembic for schema versioning, or manual migrations during development?
3. **Frontend Framework**: React/Vue SPA or server-rendered Jinja2 templates? (Affects API design and feature velocity)
4. **API Versioning**: Semantic versioning in URL (`/api/v1/`) or via headers?
5. **Cloud Platform**: Heroku (easy, costly), Railway (modern, cheaper), AWS (powerful, complex), or self-host?
6. **Freemium Model**: Optional tier or premium-only? (Decided against free tier to reduce abuse)
7. **Self-Host License**: Perpetual (one-time) or annual renewal?
8. **Whitelabel Support**: Support customer self-branding, or enforce CycleTrainingPlanner branding?
9. **Data Retention**: Auto-delete historical performance after N years, or keep indefinitely?
10. **Rate Limiting**: API throttling by tier (Starter vs Pro), or per-user only?

## Next Steps

1. Review and refine this plan
2. Set up project board/issues for tracking
3. Start with Phase 1: Foundation work
4. Create feature branch for first set of changes
5. Regular commits with clear messages
6. Update this plan as decisions are made

## Sustainability & Pricing (Privacy-First)

**Goal**: Fund hosting and weather API costs without selling data or adding ads.

### Recommended Model (MVP)
1. **Hosted subscription** (primary)
  - Low monthly fee for hosted plans, backups, and multi-device access
  - Covers infrastructure + weather API usage

2. **Self-host license** (one-time)
  - Pay once to run locally or on own server
  - Best for privacy-first users who avoid hosted services

3. **Freemium** (optional)
  - Free: plan generation + basic exports
  - Paid: goal tracking, performance analytics, weather-aware predictions

### Privacy Commitments
- No ads
- No selling or sharing data
- Data minimization by default (no GPS storage, no health data)
- Clear deletion controls

### Cost Drivers to Track
- Weather API usage (per-request fees)
- Storage (ride summaries, plans)
- Compute (GPX parsing, gradient analysis)

### Suggested Pricing Tests
- Starter: low monthly fee (covers basic hosting)
- Pro: adds analytics + weather context
- Self-host: one-time license

## Resources & References

- **iCalendar Spec**: RFC 5545
- **UK GDPR**: https://ico.org.uk/for-organisations/
- **Python Packaging**: https://packaging.python.org/

## Timeline Estimate

- **Phase 1-2**: 1-2 weeks (foundation + exports)
- **Phase 3-4**: 1 week (packaging + usability)
- **Phase 6**: 1 week (GPX features)
- **Phase 7**: 3-4 days (documentation)

**Total**: 4-5 weeks for full implementation

**MVP**: 1-2 weeks (Phase 1-3 only)
