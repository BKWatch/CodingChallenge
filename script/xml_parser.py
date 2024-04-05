import xml.etree.ElementTree as ET
import sys
import json
import os

def parse_xml(file_path):
    """
    Parse XML file and extract address information.

    Args:
        file_path (str): Path to the XML file.

    Returns:
        list: List of dictionaries containing address information.
    """
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        addresses = []

        for ent in root.findall('.//ENTITY/ENT'):
            # Extracting name, company, county, and determining their presence
            name = ent.find('NAME').text.strip() if ent.find('NAME') is not None else ""
            organization = ent.find('COMPANY').text.strip() if ent.find('COMPANY') is not None else ""
            county = ent.find('COUNTY').text.strip() if ent.find('COUNTY') is not None else ""
            county_name_present = bool(county)
            personal_name_present = bool(name)
            organization_present = bool(organization)

            # Only include personal name or organization name, not both
            if personal_name_present:
                address_name = name
                variable_name = "name"
            elif organization_present:
                address_name = organization
                variable_name = "company"
            else:
                print(f"No personal name or organization found in {file_path}. Skipping this entry.", file=sys.stderr)
                continue

            # Creating address dictionary
            address = {
                variable_name: address_name,
                "street": ent.find('STREET').text.strip(),
                "city": ent.find('CITY').text.strip(),
                "state": ent.find('STATE').text.strip(),
                "zip": ent.find('POSTAL_CODE').text.strip()
            }

            # Adding county if present
            if county_name_present:
                address["county"] = county

            addresses.append(address)

        # Sorting addresses based on zip code
        sorted_data = sorted(addresses, key=lambda item: item['zip'].rstrip('-'))

        # Convert addresses to JSON string
        json_data = json.dumps(sorted_data, indent=2)
        return json_data

    except Exception as e:
        print(f"Error parsing XML file: {file_path}. {e}", file=sys.stderr)
        sys.exit(1)
