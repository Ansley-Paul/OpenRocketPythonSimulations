#launch longitude:-81.8 deg, launch latitude: 48 deg
#Thrust Curve First Line: <designation> <diameter> <length> <delays> <propellantWeight> <totalWeight> <manufacturer>
#Sustainer thrust curve for new file was exported sustainer w/out booster.
#Booster thrust curve for new file was exported booster without sustainer and selected booster before export.
#XML file created and did convert all motors.




import os
import random
import uuid
import math
import csv
import logging
import jpype
import orhelper as orh
from orhelper import FlightDataType, FlightEvent
import zipfile
import xml.etree.ElementTree as ET
from scipy.stats import truncnorm

def extract_separation_delay_charge(ork_path):
    with zipfile.ZipFile(ork_path, 'r') as ork_zip:
        with ork_zip.open("rocket.ork") as xml_file:
            tree = ET.parse(xml_file)
            root = tree.getroot()

    # Search all <motor> configs for <ignition><delay> value
    for motor in root.findall(".//motor"):
        ignition = motor.find("ignition")
        if ignition is not None:
            delay = ignition.find("delay")
            if delay is not None and delay.text:
                return float(delay.text)
    return None

# ========== CONFIGURATION ==========
os.environ['JAVA_HOME'] = r"E:/Monte Carlo Method/dependencies/JDK File/jdk-21"
OPENROCKET_JAR_PATH = r"E:/Monte Carlo Method/dependencies/JAR FIle/OpenRocket-23.09 (2).jar"
ORK_FILE = r"E:/Monte Carlo Method/dependencies/ORK files/OTMKIII (present)/UpdatedRocket_DualMotors.ork"
BASE_ENG_FILE = r"C:/Users/ansle/AppData/Roaming/OpenRocket/ThrustCurves/Pro98-6GXL-N2900-P.eng"
BASE_ENG_FILE_2 = r"C:/Users/ansle/AppData/Roaming/OpenRocket/ThrustCurves/Pro98-6GXL-N4100-P.eng"
RESULTS_FILE = "OTMKII_results_76.csv"
ENG_OUTPUT_DIR = "generated_engines"
MOTOR_NAME = "Pro98-6GXL-N2900-P"
MOTOR_NAME_2 = "Pro98-6GXL-N4100-P"
SIMULATIONS_PER_RUN = 10

# Create output directory if it doesn't exist
os.makedirs(ENG_OUTPUT_DIR, exist_ok=True)

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def validate_file(path):
    """Check if file exists and is accessible"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    if not os.path.isfile(path):
        raise ValueError(f"Path is not a file: {path}")
    return True

# ========== PARAMETER EXTRACTION ==========
def extract_nominal_parameters(helper, doc):
    """Extract nominal parameters from OpenRocket document using the Helper class."""
    rocket = doc.getRocket()
    simulation = doc.getSimulation(0)
    conditions = simulation.getOptions()
    #print(dir(rocket.getChild(0).getChild(4)))
    
    #gross weight
    gross_weight = 49175

    # Extract parameters directly from the rocket and simulation options
    return {
        'gross_weight': float(gross_weight or 0.0),  # Mass is set #maybe +13.248
        #'center_gravity': float(rocket.getCG().x or 0.0),  # Center of gravity
        'diameter': float(rocket.getChild(0).getChild(1).getRadius(1) * 2 or 0.0),  # Diameter from the first child
        #'sustainer_thrust': float(next((c.getThrust() for c in rocket.getChildren() 
                            #if "Sustainer" in c.getName() and hasattr(c, 'getThrust')), 0.0)),
        'wind_speed_average': float(conditions.getWindSpeedAverage() or 0.0),
        'wind_direction': float(conditions.getWindDirection() or 0.0),
        'wind_turbulence_intensity': float(conditions.getWindTurbulenceIntensity() or 0.0),
        'wind_standard_deviation': float(conditions.getWindSpeedDeviation() or 0.0),
        'launch_rod_length': float(conditions.getLaunchRodLength() or 0.0),
        'launch_temperature': float(conditions.getLaunchTemperature() or 0.0),
        'launch_rod_angle': float(conditions.getLaunchRodAngle() or 0.0),
        'launch_rod_direction': float(conditions.getLaunchRodDirection() or 0.0),
        #'seperation_delay_charge': float(rocket.getChild(0).getChild(4).getDelayCharge(2) or 0.0),
        'separation_delay_charge': float(extract_separation_delay_charge(ORK_FILE) or 0.0),
        #'longitudinal_moment_of_inertia': float(rocket.getChild(0).getLongitudinalInertia() or 0.0),  # Assuming first child has inertia
        #'angular_thrust_vector_deviation': 0.0,  # Default value
        #'launcher_coefficient_of_friction': 0.226
    }

# ========== MONTE CARLO PARAMETER GENERATOR ==========
def get_truncated_normal(mean, sd, low, high):
    """Generate truncated normal random variable."""
    a, b = (low - mean) / sd, (high - mean) / sd
    return truncnorm.rvs(a, b, loc=mean, scale=sd)

def generate_random_parameters(nominal_params):
    """Generate random parameters using Gaussian distribution"""
    return {
        'gross_weight': random.gauss(nominal_params['gross_weight'], 7.07),#7.07),  get_truncated_normal(
        #'center_gravity': random.gauss(nominal_params['center_gravity'], 0.14),  
        'diameter': random.gauss(nominal_params['diameter'], 0.0005),#0.0005),  
        'launch_rod_length': random.gauss(nominal_params['launch_rod_length'], 0.22),#0.22),  
        'launch_temperature': random.gauss(nominal_params['launch_temperature'], 9.58),#9.58, 0, 50),  
        'wind_direction': random.gauss(nominal_params['wind_direction'], math.radians(104.21)),#104.21), 0, 2 * math.pi),  
        'wind_speed_average': random.gauss(nominal_params['wind_speed_average'], 4.47),#4.47, 0, 100),  
        'wind_turbulence_intensity': random.gauss(nominal_params['wind_turbulence_intensity'], 3.87),#3.87, 0, 0.3),  
        'launch_rod_angle': random.gauss(nominal_params['launch_rod_angle'], math.radians(1.73)),#1.73)),  
        'launch_rod_direction': random.gauss(nominal_params['launch_rod_direction'], math.radians(3.16)),#3.16), 0, 2 * math.pi),  
        'separation_delay_charge': random.gauss(nominal_params['separation_delay_charge'], 0.32),#0.32),  
        #'booster_thrust': random.gauss(nominal_params['booster_thrust'], x),
        #'sustainer_thrust': random.gauss(nominal_params['sustainer_thrust'], x),
        #'launcher_coefficient_of_friction': random.gauss(nominal_params['launcher_coefficient_of_friction'], ?),
        #'longitudinal_moment_of_inertia': random.gauss(nominal_params['longitudinal_moment_of_inertia'], 2.35),  
        #'angular_thrust_vector_deviation': random.gauss(nominal_params['angular_thrust_vector_deviation'], math.radians(?)),
        'wind_standard_deviation': random.gauss(nominal_params['wind_standard_deviation'], 4.47),#4.47, 0, 15),  
    }

# ========== .ENG GENERATOR ==========
def generate_scaled_eng_file(scale_factor, base_eng_path=BASE_ENG_FILE):
    """Generate scaled engine file with adjusted thrust values"""
    try:
        validate_file(base_eng_path)
        
        with open(base_eng_path, 'r') as f:
            lines = f.readlines()

        motor_name = f"ScaledMotor_{uuid.uuid4().hex[:8]}"
        new_lines = []

        for line in lines:
            if line.startswith("data:"):
                parts = line.strip().split()
                if len(parts) >= 3:
                    try:
                        t, thrust = parts[1], float(parts[2])
                        scaled_thrust = thrust * scale_factor
                        new_lines.append(f"data: {t} {scaled_thrust:.3f}")
                    except (ValueError, IndexError):
                        logging.warning(f"Invalid data line in motor file: {line.strip()}")
                        continue
            elif line.strip() and not line.startswith(("data:", "manufacturer", ";")):
                parts = line.strip().split()
                if len(parts) >= 3:
                    new_lines.append(f"{motor_name} {parts[1]} {parts[2]}")
            else:
                new_lines.append(line.strip())

        eng_path = os.path.join(ENG_OUTPUT_DIR, f"{motor_name}.eng")
        
        try:
            with open(eng_path, 'w') as f:
                f.write("\n".join(new_lines))
            logging.info(f"Generated engine file: {eng_path}")
            return motor_name, eng_path
        except IOError as e:
            logging.error(f"Failed to write engine file: {e}")
            raise
    except Exception as e:
        logging.error(f"Error in generate_scaled_eng_file: {e}")
        raise
        
def generate_scaled_eng_file_2(scale_factor, base_eng_path = BASE_ENG_FILE_2):
    """Generate scaled engine file with adjusted thrust values"""
    try:
        validate_file(base_eng_path)
        
        with open(base_eng_path, 'r') as f:
            lines = f.readlines()

        motor_name = f"ScaledMotor_{uuid.uuid4().hex[:8]}"
        new_lines = []

        for line in lines:
            if line.startswith("data:"):
                parts = line.strip().split()
                if len(parts) >= 3:
                    try:
                        t, thrust = parts[1], float(parts[2])
                        scaled_thrust = thrust * scale_factor
                        new_lines.append(f"data: {t} {scaled_thrust:.3f}")
                    except (ValueError, IndexError):
                        logging.warning(f"Invalid data line in motor file: {line.strip()}")
                        continue
            elif line.strip() and not line.startswith(("data:", "manufacturer", ";")):
                parts = line.strip().split()
                if len(parts) >= 3:
                    new_lines.append(f"{motor_name} {parts[1]} {parts[2]}")
            else:
                new_lines.append(line.strip())

        eng_path = os.path.join(ENG_OUTPUT_DIR, f"{motor_name}.eng")
        
        try:
            with open(eng_path, 'w') as f:
                f.write("\n".join(new_lines))
            logging.info(f"Generated engine file: {eng_path}")
            return motor_name, eng_path
        except IOError as e:
            logging.error(f"Failed to write engine file: {e}")
            raise
    except Exception as e:
        logging.error(f"Error in generate_scaled_eng_file: {e}")
        raise

# ========== SIMULATION RUNNER ==========
def run_simulation(helper, rocket_file, run_num, writer, nominal_params):
    try:
        # Validate files before proceeding
        validate_file(rocket_file)
        validate_file(BASE_ENG_FILE)
        
        # Generate random parameters for this simulation
        random_params = generate_random_parameters(nominal_params)

        doc = helper.load_doc(rocket_file)
        rocket = doc.getRocket()

        # Random thrust scale (±223.61%)
        scale_factor = random.gauss(1.0, 2.2361)

        motor_name, eng_path = generate_scaled_eng_file(scale_factor)
        
        # Booster
        # Validate files before proceeding
        validate_file(rocket_file)
        validate_file(BASE_ENG_FILE_2)
        
        # Generate random parameters for this simulation
        random_params = generate_random_parameters(nominal_params)

        doc = helper.load_doc(rocket_file)
        rocket = doc.getRocket()

        # Random thrust scale (±223.61%)
        scale_factor = random.gauss(1.0, 2.2361)

        motor_name_2, eng_path = generate_scaled_eng_file_2(scale_factor)
#=================================================================================
        sim = doc.getSimulation(0).duplicateSimulation(rocket)
        doc.addSimulation(sim)
        
        #____________________________________________________
        # Apply the random parameters to the simulation
        conditions = sim.getOptions()

        # Launch conditions
        conditions.setLaunchRodLength(random_params['launch_rod_length'])
        conditions.setLaunchTemperature(random_params['launch_temperature'])
        conditions.setWindSpeedAverage(random_params['wind_speed_average'])
        conditions.setWindTurbulenceIntensity(random_params['wind_turbulence_intensity'])
        conditions.setWindSpeedDeviation(random_params['wind_standard_deviation'])
        conditions.setWindDirection(random_params['wind_direction'])
        conditions.setLaunchRodAngle(random_params['launch_rod_angle'])
        conditions.setLaunchRodDirection(random_params['launch_rod_direction'])
        #conditions.setCoefficientOfFriction(random_params['launcher_coefficient_of_friction'])

        # Rocket-level parameters
        rocket.setOverrideMass(random_params['gross_weight'])
        rocket.getChild(0).getChild(0).setAftRadius(random_params['diameter']/2)
        #rocket.setLongitudinalInertia(random_params['longitudinal_moment_of_inertia'])
        
        #rocket.getChild(0).setCGOverridden(True) == random_params['center_gravity']  # X-axis movement only 

        # Apply delay charge to recovery device (if needed)
        for component in rocket.getChild(0).getChild(3).getChild(1):
            if hasattr(component, "setEjectionDelay"):
                component.setEjectionDelay(random_params['separation_delay_charge'])
                
                #can do center gravity
                #cant do center pressure, launcher coefficient, vector thrust deviation

        sim.simulate()

        events = helper.get_events(sim)
        data = helper.get_timeseries(sim, [
            FlightDataType.TYPE_POSITION_X,
            FlightDataType.TYPE_ALTITUDE,
            FlightDataType.TYPE_VELOCITY_Z,
            FlightDataType.TYPE_LONGITUDE,
            FlightDataType.TYPE_LATITUDE
        ])
        
        max_altitude = max(data[FlightDataType.TYPE_ALTITUDE])
        landing_longitude = math.degrees(data[FlightDataType.TYPE_LONGITUDE][-1])
        landing_latitude = math.degrees(data[FlightDataType.TYPE_LATITUDE][-1])
        
        print(f"Simulation {run_num}: Apogee (Max Altitude) = {max_altitude:.2f} m, "
              f"Landing Longitude = {landing_longitude:.6f} deg, "
              f"Landing Latitude = {landing_latitude:.6f} deg")
        
        writer.writerow([
            run_num,
            events.get(FlightEvent.APOGEE, [0])[0],
            events.get(FlightEvent.LAUNCH, [0])[0],
            events.get(FlightEvent.BURNOUT, [0])[0],
            events.get(FlightEvent.GROUND_HIT, [0])[0],
            max(data[FlightDataType.TYPE_POSITION_X]),
            max(data[FlightDataType.TYPE_ALTITUDE]),
            max(data[FlightDataType.TYPE_VELOCITY_Z]),
            data[FlightDataType.TYPE_POSITION_X][-1],
            math.degrees(data[FlightDataType.TYPE_LONGITUDE][-1]),
            math.degrees(data[FlightDataType.TYPE_LATITUDE][-1]),
            scale_factor,
            random_params  # Log the random parameters used
        ])

        logging.info(f"Simulation {run_num} completed successfully")
    except Exception as e:
        logging.error(f"Simulation {run_num} failed: {e}")
        raise

# ========== MAIN ==========
def main():
    try:
        # Check all required files exist before starting
        validate_file(ORK_FILE)
        validate_file(BASE_ENG_FILE)
        validate_file(BASE_ENG_FILE_2)
        validate_file(OPENROCKET_JAR_PATH)

        file_exists = os.path.exists(RESULTS_FILE)
        with open(RESULTS_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "Run #", "Apogee Time (s)", "Launch Time (s)", "Burnout Time (s)",
                    "Ground Hit Time (s)", "Max X Position (m)", "Max Altitude (m)",
                    "Max Velocity Z (m/s)", "Landing X Pos (m)", "Landing Lon (deg)",
                    "Landing Lat (deg)", "Thrust Scale Factor", "Random Parameters"
                ])

            with orh.OpenRocketInstance(jar_path=OPENROCKET_JAR_PATH) as instance:
                helper = orh.Helper(instance)

                # Load the ORK file and extract nominal parameters
                try:
                    doc = helper.load_doc(ORK_FILE)
                    rocket = doc.getRocket()
                    simulation = doc.getSimulation(0)
                    conditions = simulation.getOptions()
                    #print(dir(conditions))
                    nominal_params = extract_nominal_parameters(helper, doc)
                    logging.info("Successfully loaded ORK file and extracted parameters.")
                    
                    sim = doc.getSimulation(0).duplicateSimulation(rocket)
                    doc.addSimulation(sim)
                    print(nominal_params)
                    sim.simulate()

                    events = helper.get_events(sim)
                    data = helper.get_timeseries(sim, [
                        FlightDataType.TYPE_POSITION_X,
                        FlightDataType.TYPE_ALTITUDE,
                        FlightDataType.TYPE_VELOCITY_Z,
                        FlightDataType.TYPE_LONGITUDE,
                        FlightDataType.TYPE_LATITUDE
                    ])
        
                    max_altitude = max(data[FlightDataType.TYPE_ALTITUDE])
                    landing_longitude = math.degrees(data[FlightDataType.TYPE_LONGITUDE][-1])-0.0511
                    landing_latitude = math.degrees(data[FlightDataType.TYPE_LATITUDE][-1])-0.0099
        
                    print(f"Simulation Nominal: Apogee (Max Altitude) = {max_altitude:.2f} m, "
                          f"Landing Longitude = {landing_longitude:.6f} deg, "
                          f"Landing Latitude = {landing_latitude:.6f} deg") 
                except Exception as e:
                    logging.error(f"Failed to load ORK file: {e}")
                    return  # Exit if loading the ORK file fails

                # Run simulations
                for run_num in range(SIMULATIONS_PER_RUN):
                    run_simulation(helper, ORK_FILE, run_num, writer, nominal_params)

    except Exception as e:
        logging.error(f"Fatal error: {e}")
    finally:
        if jpype.isJVMStarted():
            jpype.shutdownJVM()

if __name__ == "__main__":
    main()

