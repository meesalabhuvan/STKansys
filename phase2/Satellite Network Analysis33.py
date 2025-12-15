"""
Satellite Communication Network Analysis using Python and STK
This project analyzes access between satellites, ground stations, and aircraft
"""

from agi.stk12.stkdesktop import STKDesktop
from agi.stk12.stkobjects import *
from agi.stk12.stkutil import *
from agi.stk12.vgt import *
import os
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

class SatelliteNetworkAnalyzer:
    """Main class for satellite network analysis"""
    
    def __init__(self, scenario_name="SatComm_Network"):
        """Initialize STK and create scenario"""
        print("Initializing STK Desktop Application...")
        self.stk = STKDesktop.StartApplication(visible=True)
        self.root = self.stk.Root
        self.scenario_name = scenario_name
        self.scenario = None
        self.satellites = []
        self.ground_stations = []
        self.aircraft = []
        
    def create_scenario(self, start_time="1 Jan 2025 00:00:00.000", duration_hours=24):
        """Create a new STK scenario"""
        print(f"\nCreating scenario: {self.scenario_name}")
        
        # Create new scenario
        self.root.NewScenario(self.scenario_name)
        self.scenario = self.root.CurrentScenario
        
        # Calculate stop time from start time and duration
        from datetime import datetime, timedelta
        
        # Parse start time (STK format: "1 Jan 2025 00:00:00.000")
        start_dt = datetime.strptime(start_time, "%d %b %Y %H:%M:%S.%f")
        stop_dt = start_dt + timedelta(hours=duration_hours)
        stop_time = stop_dt.strftime("%d %b %Y %H:%M:%S.%f")[:-3]  # Remove last 3 decimals
        
        # Set time period
        self.scenario.SetTimePeriod(start_time, stop_time)
        self.scenario.Epoch = start_time
        
        # Reset animation time
        self.root.Rewind()
        
        print(f"Scenario created from {start_time} to {stop_time}")
        
    def create_satellite(self, name, semi_major_axis_km, eccentricity, 
                        inclination_deg, raan_deg, arg_perigee_deg, true_anomaly_deg):
        """Create a satellite with specified orbital parameters"""
        print(f"\nCreating satellite: {name}")
        
        # Create satellite
        satellite = self.scenario.Children.New(AgESTKObjectType.eSatellite, name)
        
        # Set propagator to J2 Perturbation
        satellite.SetPropagatorType(AgEVePropagatorType.ePropagatorJ2Perturbation)
        
        # Get propagator and set classical orbital elements
        propagator = satellite.Propagator
        initial_state = propagator.InitialState.Representation
        
        # Convert to COE (Classical Orbital Elements)
        coe_axes = initial_state.ConvertTo(AgEOrbitStateType.eOrbitStateClassical)
        
        # Set size/shape type to use semi-major axis
        coe_axes.SizeShapeType = AgEClassicalSizeShape.eSizeShapeSemimajorAxis
        
        # Access the SizeShape as the correct interface type
        size_shape = coe_axes.SizeShape
        size_shape.SemiMajorAxis = semi_major_axis_km
        size_shape.Eccentricity = eccentricity
        
        # Set orientation
        orientation = coe_axes.Orientation
        orientation.Inclination = inclination_deg
        orientation.ArgOfPerigee = arg_perigee_deg
        orientation.AscNode = raan_deg
        
        # Set location (true anomaly)
        coe_axes.LocationType = AgEClassicalLocation.eLocationTrueAnomaly
        location = coe_axes.Location
        location.Value = true_anomaly_deg
        
        # Assign the state and propagate
        propagator.InitialState.Representation.Assign(coe_axes)
        propagator.Propagate()
        
        self.satellites.append(satellite)
        print(f"Satellite {name} created with orbital elements:")
        print(f"  Semi-major axis: {semi_major_axis_km} km")
        print(f"  Inclination: {inclination_deg}°")
        
        return satellite
        
    def create_ground_station(self, name, latitude, longitude, altitude_m=0):
        """Create a ground station facility"""
        print(f"\nCreating ground station: {name}")
        
        # Create facility
        facility = self.scenario.Children.New(AgESTKObjectType.eFacility, name)
        
        # Set position
        facility.Position.AssignGeodetic(latitude, longitude, altitude_m)
        
        self.ground_stations.append(facility)
        print(f"Ground station {name} created at ({latitude}°, {longitude}°)")
        
        return facility
        
    def create_aircraft(self, name, latitude_start, longitude_start, 
                       altitude_m, speed_mps, heading_deg):
        """Create an aircraft with a simple flight path"""
        print(f"\nCreating aircraft: {name}")
        
        # Create aircraft
        aircraft = self.scenario.Children.New(AgESTKObjectType.eAircraft, name)
        
        # Set route propagator
        aircraft.SetRouteType(AgEVePropagatorType.ePropagatorGreatArc)
        route = aircraft.Route
        
        # Create waypoints for a simple flight path
        waypoints = route.Waypoints
        
        # Starting waypoint
        wp1 = waypoints.Add()
        wp1.Latitude = latitude_start
        wp1.Longitude = longitude_start
        wp1.Altitude = altitude_m
        wp1.Speed = speed_mps
        
        # Destination waypoint (fly 1000 km in specified heading)
        distance_km = 1000
        lat2, lon2 = self._calculate_destination(latitude_start, longitude_start, 
                                                 distance_km, heading_deg)
        
        wp2 = waypoints.Add()
        wp2.Latitude = lat2
        wp2.Longitude = lon2
        wp2.Altitude = altitude_m
        wp2.Speed = speed_mps
        
        # Propagate the route
        route.Propagate()
        
        self.aircraft.append(aircraft)
        print(f"Aircraft {name} created flying from ({latitude_start}°, {longitude_start}°)")
        
        return aircraft
        
    def _calculate_destination(self, lat1, lon1, distance_km, bearing_deg):
        """Calculate destination point given distance and bearing"""
        R = 6371  # Earth radius in km
        
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        bearing_rad = np.radians(bearing_deg)
        
        lat2_rad = np.arcsin(np.sin(lat1_rad) * np.cos(distance_km/R) +
                            np.cos(lat1_rad) * np.sin(distance_km/R) * 
                            np.cos(bearing_rad))
        
        lon2_rad = lon1_rad + np.arctan2(np.sin(bearing_rad) * 
                                        np.sin(distance_km/R) * np.cos(lat1_rad),
                                        np.cos(distance_km/R) - 
                                        np.sin(lat1_rad) * np.sin(lat2_rad))
        
        return np.degrees(lat2_rad), np.degrees(lon2_rad)
        
    def compute_access(self, from_object, to_object, min_elevation_deg=10):
        """Compute access between two objects"""
        print(f"\nComputing access: {from_object.InstanceName} -> {to_object.InstanceName}")
        
        # Create access object
        access = from_object.GetAccessToObject(to_object)
        
        # Set constraints (minimum elevation for ground stations)
        if from_object.ClassName == "Facility":
            access_constraint = access.AccessConstraints
            constraint_active = access_constraint.GetActiveConstraint(
                AgEAccessConstraints.eCstrElevationAngle)
            constraint_active.EnableMin = True
            constraint_active.Min = min_elevation_deg
            
        # Compute access
        access.ComputeAccess()
        
        return access
        
    def get_access_intervals(self, access):
        """Extract access intervals as a list"""
        intervals = []
        
        try:
            # Get access intervals
            access_dp = access.DataProviders.Item("Access Data")
            result = access_dp.Exec(self.scenario.StartTime, self.scenario.StopTime)
            
            start_times = result.DataSets.GetDataSetByName("Start Time").GetValues()
            stop_times = result.DataSets.GetDataSetByName("Stop Time").GetValues()
            durations = result.DataSets.GetDataSetByName("Duration").GetValues()
            
            for i in range(len(start_times)):
                intervals.append({
                    'start': start_times[i],
                    'stop': stop_times[i],
                    'duration': durations[i]
                })
                
            print(f"Found {len(intervals)} access intervals")
            
        except Exception as e:
            print(f"No access periods found or error: {e}")
            
        return intervals
        
    def analyze_network(self, min_elevation_deg=10):
        """Analyze all access paths in the network"""
        print("\n" + "="*60)
        print("ANALYZING COMPLETE NETWORK")
        print("="*60)
        
        results = {}
        
        # Satellite to Ground Station access
        print("\n--- SATELLITE TO GROUND STATION ACCESS ---")
        for sat in self.satellites:
            for gs in self.ground_stations:
                access = self.compute_access(gs, sat, min_elevation_deg)
                intervals = self.get_access_intervals(access)
                key = f"{sat.InstanceName}-{gs.InstanceName}"
                results[key] = intervals
                
                if intervals:
                    total_duration = sum([iv['duration'] for iv in intervals])
                    print(f"  {key}: {len(intervals)} intervals, "
                          f"Total: {total_duration:.2f} sec")
                    
        # Satellite to Aircraft access
        print("\n--- SATELLITE TO AIRCRAFT ACCESS ---")
        for sat in self.satellites:
            for ac in self.aircraft:
                access = self.compute_access(ac, sat)
                intervals = self.get_access_intervals(access)
                key = f"{sat.InstanceName}-{ac.InstanceName}"
                results[key] = intervals
                
                if intervals:
                    total_duration = sum([iv['duration'] for iv in intervals])
                    print(f"  {key}: {len(intervals)} intervals, "
                          f"Total: {total_duration:.2f} sec")
                    
        # Ground Station to Aircraft access
        print("\n--- GROUND STATION TO AIRCRAFT ACCESS ---")
        for gs in self.ground_stations:
            for ac in self.aircraft:
                access = self.compute_access(gs, ac, min_elevation_deg)
                intervals = self.get_access_intervals(access)
                key = f"{ac.InstanceName}-{gs.InstanceName}"
                results[key] = intervals
                
                if intervals:
                    total_duration = sum([iv['duration'] for iv in intervals])
                    print(f"  {key}: {len(intervals)} intervals, "
                          f"Total: {total_duration:.2f} sec")
                    
        return results
        
    def export_results_to_csv(self, results, filename="access_results.csv"):
        """Export access results to CSV file"""
        print(f"\nExporting results to {filename}...")
        
        data = []
        for link, intervals in results.items():
            for interval in intervals:
                data.append({
                    'Link': link,
                    'Start Time': interval['start'],
                    'Stop Time': interval['stop'],
                    'Duration (sec)': interval['duration']
                })
                
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Exported {len(data)} access intervals to {filename}")
        
        return df
        
    def visualize_access_timeline(self, results, output_file="access_timeline.png"):
        """Create a timeline visualization of access periods"""
        print(f"\nCreating access timeline visualization...")
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        link_names = list(results.keys())
        y_positions = range(len(link_names))
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(link_names)))
        
        for idx, (link, intervals) in enumerate(results.items()):
            for interval in intervals:
                # Convert time strings to relative hours from start
                # This is simplified - in production you'd parse actual times
                start_hour = idx * 2  # Simplified for visualization
                duration_hour = interval['duration'] / 3600
                
                ax.barh(idx, duration_hour, left=start_hour, height=0.8,
                       color=colors[idx], alpha=0.7, edgecolor='black')
                
        ax.set_yticks(y_positions)
        ax.set_yticklabels(link_names)
        ax.set_xlabel('Time (hours from start)')
        ax.set_title('Communication Access Timeline')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Timeline saved to {output_file}")
        
    def generate_report(self, results, filename="network_report.txt"):
        """Generate a comprehensive text report"""
        print(f"\nGenerating report: {filename}")
        
        with open(filename, 'w') as f:
            f.write("="*70 + "\n")
            f.write("SATELLITE COMMUNICATION NETWORK ANALYSIS REPORT\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Scenario: {self.scenario_name}\n")
            f.write(f"Analysis Period: {self.scenario.StartTime} to {self.scenario.StopTime}\n\n")
            
            f.write(f"Network Components:\n")
            f.write(f"  Satellites: {len(self.satellites)}\n")
            f.write(f"  Ground Stations: {len(self.ground_stations)}\n")
            f.write(f"  Aircraft: {len(self.aircraft)}\n\n")
            
            f.write("-"*70 + "\n")
            f.write("ACCESS ANALYSIS RESULTS\n")
            f.write("-"*70 + "\n\n")
            
            for link, intervals in results.items():
                f.write(f"\n{link}:\n")
                if intervals:
                    total_duration = sum([iv['duration'] for iv in intervals])
                    f.write(f"  Number of access periods: {len(intervals)}\n")
                    f.write(f"  Total access time: {total_duration:.2f} seconds "
                           f"({total_duration/3600:.2f} hours)\n")
                    f.write(f"  Average access duration: {total_duration/len(intervals):.2f} seconds\n")
                else:
                    f.write(f"  No access periods found\n")
                    
        print(f"Report generated: {filename}")
        
    def close(self):
        """Close STK application"""
        print("\nClosing STK application...")
        # Don't close if user wants to inspect
        # self.stk.ShutDown()


def main():
    """Main execution function"""
    print("="*70)
    print("SATELLITE COMMUNICATION NETWORK ANALYSIS")
    print("Python + STK Integration Project")
    print("="*70)
    
    # Initialize analyzer
    analyzer = SatelliteNetworkAnalyzer("MultiLayer_SatComm")
    
    # Create scenario
    analyzer.create_scenario("1 Jan 2025 00:00:00.000", duration_hours=24)
    
    # Create satellites (LEO constellation)
    print("\n--- Creating Satellite Constellation ---")
    analyzer.create_satellite(
        name="LEO_Sat_1",
        semi_major_axis_km=7000,  # ~600 km altitude
        eccentricity=0.001,
        inclination_deg=98,
        raan_deg=0,
        arg_perigee_deg=0,
        true_anomaly_deg=0
    )
    
    analyzer.create_satellite(
        name="LEO_Sat_2",
        semi_major_axis_km=7000,
        eccentricity=0.001,
        inclination_deg=98,
        raan_deg=120,
        arg_perigee_deg=0,
        true_anomaly_deg=0
    )
    
    # Create ground stations
    print("\n--- Creating Ground Stations ---")
    analyzer.create_ground_station("GS_NewYork", 40.7128, -74.0060, 10)
    analyzer.create_ground_station("GS_London", 51.5074, -0.1278, 11)
    analyzer.create_ground_station("GS_Tokyo", 35.6762, 139.6503, 40)
    
    # Create aircraft
    print("\n--- Creating Aircraft ---")
    analyzer.create_aircraft(
        name="Flight_AA100",
        latitude_start=40.7128,
        longitude_start=-74.0060,
        altitude_m=10000,
        speed_mps=250,
        heading_deg=45
    )
    
    analyzer.create_aircraft(
        name="Flight_BA200",
        latitude_start=51.5074,
        longitude_start=-0.1278,
        altitude_m=11000,
        speed_mps=240,
        heading_deg=90
    )
    
    # Analyze network
    results = analyzer.analyze_network(min_elevation_deg=10)
    
    # Export results
    df = analyzer.export_results_to_csv(results, "satellite_network_access.csv")
    
    # Generate visualizations
    analyzer.visualize_access_timeline(results, "access_timeline.png")
    
    # Generate report
    analyzer.generate_report(results, "network_analysis_report.txt")
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print("\nGenerated files:")
    print("  - satellite_network_access.csv")
    print("  - access_timeline.png")
    print("  - network_analysis_report.txt")
    print("\nSTK scenario remains open for inspection.")
    
    # Don't close so user can inspect
    # analyzer.close()


if __name__ == "__main__":
    main()