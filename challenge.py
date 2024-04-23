import argparse   # Module for parsing command-line arguments (provides --help option)
import json
import sys
import xml.etree.ElementTree as ET
import csv 

# Function to parse XML file
def parse_xml(file_path):
    addresses = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
         
        for person in root.findall('person'):
            address = {}
            for elem in person:
                if elem.tag == 'name':
                    address['name'] = elem.text.strip()
                elif elem.tag == 'organization':
                    address['organization'] = elem.text.strip()
                elif elem.tag == 'address':
                    address['street'] = elem.text.strip()
                elif elem.tag == 'city':
                    address['city'] = elem.text.strip()
                elif elem.tag == 'state':
                    address['state'] = elem.text.strip()
                elif elem.tag == 'zip':
                    address['zip'] = elem.text.strip()
            addresses.append(address)
        return addresses
    except Exception as e:
        sys.stderr.write(f"Error parsing XML file '{file_path}': {str(e)}\n")
        return []

# Function to parse TSV file
def parse_tsv(file_path):
    addresses = []
    try:
        with open(file_path, 'r', newline='') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                address = {}
                address['name'] = ' '.join([row['first'].strip(), row['middle'].strip(), row['last'].strip()]).strip()
                address['organization'] = row['organization'].strip()
                address['street'] = row['address'].strip()
                address['city'] = row['city'].strip()
                address['state'] = row['state'].strip()
                address['zip'] = row['zip'].strip()
                addresses.append(address)
        return addresses
    except Exception as e:
        sys.stderr.write(f"Error parsing TSV file '{file_path}': {str(e)}\n")
        return []

# Function to parse TXT file
def parse_txt(file_path):
    addresses = []

    with open(file_path, 'r') as file:
        lines = file.readlines()

    i = 0
    while i < len(lines):
        address = {}

        # Extract name
        name = lines[i].strip()
        if name:  # Check if the name is not empty
            if ',' in name:
                name_parts = name.split(',')
                address['name'] = name_parts[0]
                address['organization'] = name_parts[1]
            else:
                address['name'] = name

            # Extract street
            street_index = i + 1
            if street_index < len(lines):
                street = lines[street_index].strip()
                address['street'] = street

            # Extract city, state, county (if available), and zip
            city_state_zip_index = i + 2
            if city_state_zip_index < len(lines):
                city_state_zip = lines[city_state_zip_index].strip()
                city_state_zip_parts = city_state_zip.split(',')

                if len(city_state_zip_parts) >= 2:
                    address['city'] = city_state_zip_parts[0]

                    state_zip = city_state_zip_parts[-1].split()
                    if len(state_zip) >= 2:
                        address['state'] = state_zip[0]

                        if len(state_zip) == 3:
                            address['zip'] = state_zip[1] + '-' + state_zip[2]
                        else:
                            address['zip'] = state_zip[1]

                    if len(city_state_zip_parts) == 3:
                        address['county'] = city_state_zip_parts[1].strip().upper()

            addresses.append(address)

            # Move to the next entry
            i += 3 if ',' in name else 4
        else:
            i += 1  # Skip the empty line

    return addresses

# Function to sort addresses by ZIP code
def sort_addresses(addresses):
    return sorted(addresses, key=lambda x: x.get('zip', ''))

# Function to print addresses as JSON
def print_addresses(addresses):
    print(json.dumps(addresses, indent=2))

# Main function
def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Parse US names and addresses from input files and output as JSON.')
    parser.add_argument('files', metavar='FILE', type=str, nargs='+',
                        help='list of input files (XML, TSV, or TXT)')
    args = parser.parse_args()
    
     
    # Check if at least one input file is provided
    if not args.files:
        parser.error('At least one input file must be provided.')

    # Parse and combine addresses from input files
    combined_addresses = []
    for file_path in args.files:
        if file_path.endswith('.xml'):
            combined_addresses.extend(parse_xml(file_path))
        elif file_path.endswith('.tsv'):
            combined_addresses.extend(parse_tsv(file_path))
        elif file_path.endswith('.txt'):
            combined_addresses.extend(parse_txt(file_path))
        else:
            sys.stderr.write(f"Unsupported file format for '{file_path}'\n")
            sys.exit(1)

    # Check if any addresses were parsed
    if not combined_addresses:
        sys.stderr.write("No valid addresses found in input files\n")
        sys.exit(1)

    # Sort addresses by ZIP code
    sorted_addresses = sort_addresses(combined_addresses)

    # Print addresses as JSON
    print_addresses(sorted_addresses)
    
    # Exit with success status
    sys.exit(0)

if __name__ == '__main__':
    main()