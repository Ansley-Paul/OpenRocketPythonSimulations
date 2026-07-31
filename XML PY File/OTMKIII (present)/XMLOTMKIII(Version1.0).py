import zipfile
import xml.etree.ElementTree as ET
import os

# === SETUP ===
input_ork_path = "C:/Users/ansle/Downloads/7-9-2025 - OT Mk III - AD.ork"
output_ork_path = "UpdatedRocket_DualMotors.ork"

# First motor (e.g., sustainer), second motor (e.g., booster)
custom_motor_1 = "Pro98-6GXL-N4100-P"
custom_motor_2 = "Pro98-6GXL-N2900-P"

# === STEP 1: Extract rocket.ork from input file ===
with zipfile.ZipFile(input_ork_path, 'r') as ork_zip:
    if "rocket.ork" not in ork_zip.namelist():
        raise FileNotFoundError("rocket.ork not found in .ork archive")

    with ork_zip.open("rocket.ork") as xml_file:
        tree = ET.parse(xml_file)
        root = tree.getroot()

# === STEP 2: Replace motors ===
motor_list = root.findall(".//motor")
motor_count = len(motor_list)

if motor_count < 2:
    raise ValueError(f"Expected at least 2 motors, found {motor_count}")

# Replace first motor
old_motor_1 = motor_list[0].text
motor_list[0].text = custom_motor_1
print(f"Replaced Motor 1: '{old_motor_1}' → '{custom_motor_1}'")

# Replace second motor
old_motor_2 = motor_list[1].text
motor_list[1].text = custom_motor_2
print(f"Replaced Motor 2: '{old_motor_2}' → '{custom_motor_2}'")

print(f"✅ Total motors replaced: 2")

# === STEP 3: Save modified XML ===
temp_xml_path = "rocket_modified.ork"
tree.write(temp_xml_path, encoding="UTF-8", xml_declaration=True)

# === STEP 4: Repackage ===
with zipfile.ZipFile(output_ork_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
    new_zip.write(temp_xml_path, arcname="rocket.ork")

os.remove(temp_xml_path)

print(f"\n✅ Updated .ork saved as: {output_ork_path}")
