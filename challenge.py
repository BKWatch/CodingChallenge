import os
import sys
import json
import xml.etree.ElementTree as ET
import csv

def parse_file(file_path):
    addresses = []
    file_extension = os.path.splitext(file_path)[1].lower()
    # Check if the file extension is valid
    if file_extension == '.xml':
        addresses = parse_xml(file_path)
    elif file_extension == '.tsv':
        addresses = parse_tsv(file_path)
    elif file_extension == '.txt':
        addresses = parse_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")

    return addresses

def parse_xml(file_path):
    addresses = []
    try:
         # Parse the XML file
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Iterate through each <ENT> element under <ENTITY>
        for ent_elem in root.findall('.//ENTITY/ENT'):
            # Initialize a dictionary to store the address details
            address = {}

            # Extract the address details from the XML elements
            name_elem = ent_elem.find('NAME')
            company_elem = ent_elem.find('COMPANY')
            street_elem = ent_elem.find('STREET')
            city_elem = ent_elem.find('CITY')
            state_elem = ent_elem.find('STATE')
            country_elem = ent_elem.find('COUNTRY')
            postal_code_elem = ent_elem.find('POSTAL_CODE')

            # Check if name or company is available
            if name_elem is not None and name_elem.text.strip():
                name = name_elem.text.strip()
                company = None
            elif company_elem is not None and company_elem.text.strip():
                name = None
                company = company_elem.text.strip()
            else:
                # Skip this address if both name and company are missing
                continue

            street = street_elem.text.strip() if street_elem is not None else ""
            city = city_elem.text.strip() if city_elem is not None else ""
            state = state_elem.text.strip() if state_elem is not None else ""
            country = country_elem.text.strip() if country_elem is not None else ""
            postal_code = postal_code_elem.text.strip() if postal_code_elem is not None else ""

            # Add address details to the dictionary
            if name:
                address["name"] = name
            if company:
                address["organization"] = company
            address["street"] = street
            address["city"] = city
            address["state"] = state
            if country:
                address["country"] = country
            address["zip"] = postal_code

            # Append the address dictionary to the list
            addresses.append(address)
    except ET.ParseError:
        raise ValueError(f"Error parsing XML file: {file_path}")

    return addresses

def parse_tsv(file_path):
    addresses = []
    try:
        with open(file_path, 'r', newline='') as file:
            # Create a CSV reader object using the tab delimiter
            reader = csv.reader(file, delimiter='\t')
            
            # Skip the header row
            next(reader)
            
            for row in reader:
                # Initialize a dictionary to store the address details
                address = {}

                # Check if name is available, else check for organization
                if row[0].strip() or row[1].strip() or row[2].strip():
                    name = f"{row[0]} {row[1]} {row[2]}".strip()
                    organization = None
                elif row[3].strip():
                    name = None
                    organization = row[3].strip()
                else:
                    # Skip this row if both name and organization are missing
                    continue

                street = row[4].strip()
                city = row[5].strip()
                state = row[6].strip()
                county = row[7].strip()
                zip_code = row[8].strip()

                # Add address details to the dictionary
                if name:
                 address["name"] = name
                if organization:
                 address["organization"] = organization
                address["street"] = street
                address["city"] = city
                if county:
                    address["county"] = county
                address["state"] = state
                address["zip"] = zip_code

                # Append the address dictionary to the list
                addresses.append(address)
    except (IndexError, csv.Error) as e:
        print(f"Error parsing TSV file: {file_path}")
        print(f"Error: {e}")
        raise ValueError(f"Error parsing TSV file: {file_path}")

    return addresses

def parse_txt(file_path):
    addresses = []

    try:
        with open(file_path, 'r') as file:
        # Read the file line by line
            lines = file.readlines()
            i = 2
            while i < len(lines):
                # Initialize a dictionary to store the address details
                address = {}

                # Assuming each address has either 4 or 5 lines
                name = lines[i].strip()
                street = lines[i+1].strip()

                # Check if county is mentioned
                if lines[i+2].strip().upper().endswith('COUNTY'):
                    county = lines[i+2].strip().split()[0]
                    city_state_zip = lines[i+3].strip()
                    # Move to the next address
                    i += 5
                else:
                    county = None
                    city_state_zip = lines[i+2].strip()
                    # Move to the next address
                    i += 4

                # Split city, state, and zip by the comma
                city_state_parts = city_state_zip.split(',')
                city = city_state_parts[0].strip()

                # Check if there are enough elements in city_state_parts
                if len(city_state_parts) > 1:
                    state_zip = city_state_parts[1].strip()

                    # Split state and zip by space
                    state, zip_code = state_zip.rsplit(' ', 1)
                else:
                    # If no state and zip are provided, set them to empty strings
                    state = ""
                    zip_code = ""

                # Add address details to the dictionary
                address["name"] = name
                address["street"] = street
                address["city"] = city
                if county:
                    address["county"] = county
                address["state"] = state
                address["zip"] = zip_code

                # Append the address dictionary to the list
                addresses.append(address)

    except (IndexError, ValueError):
        raise ValueError(f"Error parsing TXT file: {file_path}")

    return addresses


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        print("Usage: python challenge.py <file_path1> <file_path2> ... <file_pathN>")
        sys.exit(1)

    all_addresses = []
    for file_path in sys.argv[1:]:
        try:
            addresses = parse_file(file_path)
            all_addresses.extend(addresses)
        except (ValueError, IOError) as e:
            print(f"Error processing file {file_path}: {e}", file=sys.stderr)
            sys.exit(1)

    all_addresses.sort(key=lambda x: x['zip'])
    print(json.dumps(all_addresses, indent=2))
    sys.exit(0)

if __name__ == "__main__":
    main()