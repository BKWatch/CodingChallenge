import xml.etree.ElementTree as ET
import sys

# Function to parse XML file
def parse_xml(file_path):
    address_list = []
    try:
        xml_tree = ET.parse(file_path)
        root = xml_tree.getroot()
        for entity in root.findall("./ENTITY/ENT"):
            address_data = {}
            person_name = entity.find("NAME").text.strip()
            org_name = entity.find("COMPANY").text.strip()
            street_parts = [
                entity.find("STREET").text or "",
                entity.find("STREET_2").text or "",
                entity.find("STREET_3").text or ""
            ]
            full_street = " ".join(street_parts).strip()

            local_city = entity.find("CITY").text.strip()
            local_state = entity.find("STATE").text.strip()
            postal_code = entity.find("POSTAL_CODE").text.strip()

            if person_name:
                address_data["name"] = person_name
            if org_name:
                address_data["organization"] = org_name
            if full_street:
                address_data["street"] = full_street
            if local_city:
                address_data["city"] = local_city
            if local_state:
                address_data["state"] = local_state
            if postal_code:
                address_data["zip"] = postal_code[:5] if postal_code.endswith("-") else postal_code.replace(" ", "")

            address_list.append(address_data)
    except Exception as err:
        sys.stderr.write(f"Error parsing XML file at {filepath}\n")
        sys.stderr.write(f"Exception: {err}\n")
        sys.exit(1)

    return address_list