import pandas as pd
import simplekml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def shift_coordinates(lon, lat, lon_offset, lat_offset):
    """
    Shift coordinates by the given longitude and latitude offsets.
    
    Args:
        lon (float): Original longitude in degrees.
        lat (float): Original latitude in degrees.
        lon_offset (float): Longitude offset to apply in degrees.
        lat_offset (float): Latitude offset to apply in degrees.
    
    Returns:
        tuple: Shifted (longitude, latitude).
    """
    return lon + lon_offset, lat + lat_offset

def csv_to_kml(csv_path, kml_output_path="landing_points_shifted.kml"):
    """
    Convert CSV with rocket simulation data to a KML file with shifted coordinates.
    
    Args:
        csv_path (str): Path to the input CSV file.
        kml_output_path (str): Path to save the output KML file.
    """
    try:
        # Define original and actual launch coordinates
        original_launch_lon = -81.8
        original_launch_lat = 48
        actual_launch_lon = -81.8511
        actual_launch_lat = 47.9901
        
        # Calculate offsets
        lon_offset = actual_launch_lon - original_launch_lon  # -0.0511
        lat_offset = actual_launch_lat - original_launch_lat  # -0.0099
        
        # Print actual launch coordinates
        print(f"Actual Launch Longitude: {actual_launch_lon} deg")
        print(f"Actual Launch Latitude: {actual_launch_lat} deg")
        
        # Read CSV file
        logging.info(f"Reading CSV file: {csv_path}")
        df = pd.read_csv(csv_path, usecols=["Run #", "Landing Lon (deg)", "Landing Lat (deg)", "Max Altitude (m)"])
        
        # Create KML object
        kml = simplekml.Kml()
        kml.document.name = "OTMKIII VERSION 1.0 Rocket Landing Points (Shifted)"
        
        # Define style for landing points (red pushpin)
        landing_style = simplekml.Style()
        landing_style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png"
        
        # Define style for launch point (blue pushpin)
        launch_style = simplekml.Style()
        launch_style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/pushpin/blue-pushpin.png"
        
        # Add placemark for actual launch point
        launch_pnt = kml.newpoint(name="Actual Launch Point")
        launch_pnt.coords = [(actual_launch_lon, actual_launch_lat, 0)]
        launch_pnt.description = f"Actual Launch Point\nLongitude: {actual_launch_lon:.6f} deg\nLatitude: {actual_launch_lat:.6f} deg"
        launch_pnt.style = launch_style
        
        # Process each row for landing points
        for index, row in df.iterrows():
            try:
                run_num = int(row["Run #"])
                lon = float(row["Landing Lon (deg)"])
                lat = float(row["Landing Lat (deg)"])
                alt = float(row["Max Altitude (m)"])
                
                # Skip invalid coordinates
                if pd.isna(lon) or pd.isna(lat) or abs(lon) > 180 or abs(lat) > 90:
                    logging.warning(f"Skipping invalid coordinates for Run {run_num}: lon={lon}, lat={lat}")
                    continue
                
                # Shift landing coordinates
                shifted_lon, shifted_lat = shift_coordinates(lon, lat, lon_offset, lat_offset)
                
                # Skip invalid shifted coordinates
                if abs(shifted_lon) > 180 or abs(shifted_lat) > 90:
                    logging.warning(f"Skipping invalid shifted coordinates for Run {run_num}: lon={shifted_lon}, lat={shifted_lat}")
                    continue
                
                # Create placemark for shifted landing point
                pnt = kml.newpoint(name=f"Run {run_num}")
                pnt.coords = [(shifted_lon, shifted_lat, 0)]  # Altitude set to 0 for ground-level visualization
                pnt.description = f"Simulation Run {run_num}\nMax Altitude: {alt:.2f} m\nShifted Longitude: {shifted_lon:.6f} deg\nShifted Latitude: {shifted_lat:.6f} deg"
                pnt.style = landing_style
                
            except (ValueError, TypeError) as e:
                logging.warning(f"Error processing row {index} (Run {run_num}): {e}")
                continue
        
        # Save KML file
        kml.save(kml_output_path)
        logging.info(f"KML file saved successfully: {kml_output_path}")
        
    except FileNotFoundError:
        logging.error(f"CSV file not found: {csv_path}")
        raise
    except Exception as e:
        logging.error(f"Error processing CSV to KML: {e}")
        raise

if __name__ == "__main__":
    csv_file = "OTMKIII_results.csv"
    try:
        csv_to_kml(csv_file)
    except Exception as e:
        logging.error(f"Failed to generate KML: {e}")
