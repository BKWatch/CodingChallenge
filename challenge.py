import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET

# Function to parse XML file
def parse_xml(file_path):
    addresses = []
    try:
        # Parse XML file
        tree = ET.parse(file_path)
        root = tree.getroot()
        # Iterate over ENTITY elements
        for ent in root.findall('ENTITY/ENT'):
            # Extract data from XML and construct address dictionary
            name = ent.find('NAME').text.strip()
            organization = ent.find('COMPANY').text.strip()
            street = ent.find('STREET').text.strip()
            city = ent.find('CITY').text.strip()
            state = ent.find('STATE').text.strip()
            zip_code = ent.find('POSTAL_CODE').text.strip().replace('-', '')
            address = {'name': name, 'organization': organization, 'street': street,
                       'city': city, 'state': state, 'zip': zip_code}
            addresses.append(address)
    except Exception as e:
        # Print error message if parsing fails
        print(f"Error parsing XML file {file_path}: {e}", file=sys.stderr)
    return addresses

# Function to parse TSV file
def parse_tsv(file_path):
    addresses = []
    try:
        # Open TSV file
        with open(file_path, 'r') as file:
            # Iterate over each line in the file
            for line in file:
                # Split the line by tab delimiter
                fields = line.strip().split('\t')
                # Check if the line contains all required fields
                if len(fields) >= 9:
                    # Extract data from TSV and construct address dictionary
                    name = f"{fields[0]} {fields[1]} {fields[2]}".strip()
                    organization = fields[3].strip()
                    street = fields[4].strip()
                    city = fields[5].strip()
                    state = fields[6].strip()
                    county = fields[7].strip()
                    zip_code = fields[8].strip().replace('-', '')
                    address = {'name': name, 'organization': organization, 'street': street,
                               'city': city, 'state': state, 'county': county, 'zip': zip_code}
                    addresses.append(address)
    except Exception as e:
        # Print error message if parsing fails
        print(f"Error parsing TSV file {file_path}: {e}", file=sys.stderr)
    return addresses

# Function to parse TXT file
def parse_txt(file_path):
    addresses = []
    try:
        # Open TXT file
        with open(file_path, 'r') as file:
            # Read all lines from the file
            lines = file.readlines()
            i = 0
            # Process lines in groups of 3
            while i < len(lines):
                # Extract data from TXT and construct address dictionary
                name = lines[i].strip()
                street = lines[i+1].strip()
                city_state_zip = lines[i+2].strip().split(',')
                city = city_state_zip[0].strip()
                state_zip = city_state_zip[1].strip().split(' ')
                state = state_zip[0].strip()
                zip_code = state_zip[1].strip().replace('-', '')
                address = {'name': name, 'street': street, 'city': city,
                           'state': state, 'zip': zip_code}
                addresses.append(address)
                i += 3
    except Exception as e:
        # Print error message if parsing fails
        print(f"Error parsing TXT file {file_path}: {e}", file=sys.stderr)
    return addresses

# Function to validate file extension
def validate_file_extension(file_path):
    valid_extensions = ['.xml', '.tsv', '.txt']
    _, extension = os.path.splitext(file_path)
    if extension.lower() not in valid_extensions:
        # Print error message if file format is not supported
        print(f"Error: Unsupported file format for file {file_path}", file=sys.stderr)
        return False
    return True

# Function to print help message
def print_help():
    # Print usage and options information
    print("Usage: python challenge.py [options] file1 file2 ...")
    print("Options:")
    print("  -h, --help  : Show this help message")

# Main function
def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs='+', help="List of input files")
    args = parser.parse_args()

    # If --help option is provided, print help message
    if len(sys.argv) == 2 and (sys.argv[1] == "-h" or sys.argv[1] == "--help"):
        print_help()
        sys.exit(0)

    # Check for errors in argument list
    if not args.files:
        # Print error message if no input files provided
        print("Error: No input files provided", file=sys.stderr)
        sys.exit(1)

    all_addresses = []
    # Parse each input file
    for file_path in args.files:
        if not validate_file_extension(file_path):
            sys.exit(1)
        _, extension = os.path.splitext(file_path)
        if extension.lower() == '.xml':
            addresses = parse_xml(file_path)
        elif extension.lower() == '.tsv':
            addresses = parse_tsv(file_path)
        elif extension.lower() == '.txt':
            addresses = parse_txt(file_path)
        all_addresses.extend(addresses)

    # Sort addresses by ZIP code in ascending order
    all_addresses.sort(key=lambda x: x.get('zip', ''))

    # Output the addresses as JSON
    print(json.dumps(all_addresses, indent=2))

if __name__ == "__main__":
    main()
