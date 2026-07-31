import zipfile
import xml.etree.ElementTree as ET
import os

# === SETUP ===
input_ork_path = "C:/Users/ansle/Downloads/OTMKII_-_R07_AJ.ork"   # <-- UPDATE THIS PATH
output_ork_path = "UpdatedRocket.ork"
custom_motor_name = "Pro98-6G-N1975GR"

# === STEP 1: Extract rocket.ork from input file ===
with zipfile.ZipFile(input_ork_path, 'r') as ork_zip:
    file_list = ork_zip.namelist()
    if "rocket.ork" not in file_list:
        raise FileNotFoundError("rocket.ork not found in .ork archive")

    with ork_zip.open("rocket.ork") as xml_file:
        tree = ET.parse(xml_file)
        root = tree.getroot()

# === STEP 2: Replace all motor assignments ===
motor_count = 0
for motor_conf in root.findall(".//motorConfiguration"):
    for motor in motor_conf.findall("motor"):
        old_motor = motor.text
        motor.text = custom_motor_name
        print(f"Replaced motor: '{old_motor}' → '{custom_motor_name}'")
        motor_count += 1

print(f"Total motors replaced: {motor_count}")

# === STEP 3: Save modified XML as new rocket.ork ===
temp_xml_path = "rocket_modified.ork"
tree.write(temp_xml_path, encoding="UTF-8", xml_declaration=True)

# === STEP 4: Repackage as .ork file ===
with zipfile.ZipFile(output_ork_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
    new_zip.write(temp_xml_path, arcname="rocket.ork")

# Clean up temporary file
os.remove(temp_xml_path)

print(f"\n✅ Updated .ork saved as: {output_ork_path}")
