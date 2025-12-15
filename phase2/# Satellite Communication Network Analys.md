# Satellite Communication Network Analysis

## Project Overview

This project demonstrates a complete satellite communication network analysis using **Python** and **AGI's Systems Tool Kit (STK)**. It analyzes communication access between:

- **Satellites** (Space segment)
- **Aircraft** (Air segment)  
- **Ground Stations** (Ground segment)

## Features

### Core Functionality
- ✅ Create LEO satellite constellation with orbital parameters
- ✅ Deploy ground stations at specific geographic locations
- ✅ Simulate aircraft flight paths
- ✅ Compute access intervals between all network elements
- ✅ Apply elevation angle constraints for ground stations
- ✅ Export results to CSV format
- ✅ Generate visualization timelines
- ✅ Create comprehensive analysis reports

### Network Layers Analyzed

1. **Space-to-Ground**: Satellite visibility from ground stations
2. **Space-to-Air**: Satellite coverage of aircraft
3. **Ground-to-Air**: Ground station line-of-sight to aircraft




### Satellite Configuration
- **Orbit Type**: Low Earth Orbit (LEO)
- **Altitude**: ~600 km
- **Inclination**: 98° (Sun-synchronous)
- **Propagator**: J2 Perturbation

### Ground Stations
- New York: (40.71°N, 74.01°W)
- London: (51.51°N, 0.13°W)
- Tokyo: (35.68°N, 139.65°E)
- **Minimum Elevation**: 10° (configurable)

### Aircraft Parameters
- **Altitude**: 10,000-11,000 m
- **Speed**: 240-250 m/s
- **Route**: Great arc propagation

## Output Files

### 1. `satellite_network_access.csv`
Contains all access intervals with:
- Link identification
- Start/stop times
- Duration in seconds

### 2. `access_timeline.png`
Visual timeline showing:
- All communication links
- Access windows over analysis period
- Color-coded by link type

### 3. `network_analysis_report.txt`
Comprehensive text report including:
- Network configuration summary
- Access statistics per link
- Total and average access durations

## Use Cases

1. **Satellite Network Design**: Optimize satellite constellation for coverage
2. **Ground Station Planning**: Determine optimal GS locations
3. **Mission Planning**: Schedule communications for aircraft/UAVs
4. **Link Budget Analysis**: Calculate available communication windows
5. **Coverage Analysis**: Assess global or regional connectivity

## Extending the Project

### Add More Satellites
```python
analyzer.create_satellite(
    name="LEO_Sat_3",
    semi_major_axis_km=7200,
    eccentricity=0.001,
    inclination_deg=51.6,  # ISS-like orbit
    raan_deg=240,
    arg_perigee_deg=0,
    true_anomaly_deg=0
)
```

### Add Custom Constraints
```python
# Add maximum elevation constraint
constraint_active.EnableMax = True
constraint_active.Max = 85

# Add range constraint
range_constraint = access_constraint.GetActiveConstraint(
    AgEAccessConstraints.eCstrRange)
range_constraint.EnableMax = True
range_constraint.Max = 2000000  # 2000 km
```

### Export to Different Formats
```python
# Export to JSON
import json
with open('results.json', 'w') as f:
    json.dump(results, f, indent=2)

# Export to Excel
df.to_excel('results.xlsx', index=False)
```

## Key Concepts Demonstrated

### STK Integration
- COM interface usage
- Scenario creation and management
- Object creation (Satellite, Facility, Aircraft)
- Propagator configuration
- Access computation

### Orbital Mechanics
- Classical Orbital Elements (COE)
- J2 perturbation propagation
- Geodetic coordinate systems

### Network Analysis
- Multi-layer connectivity
- Access constraints
- Temporal analysis

## Performance Notes

- **Analysis Time**: ~2-5 minutes for 24-hour period
- **STK Memory**: ~500 MB typical
- **Python Memory**: ~100 MB typical

