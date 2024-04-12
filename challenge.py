import sys
import argparse
import json
import re
import xml.etree.ElementTree as ET

def validate_field(field):
    # Validates and cleans individual fields from the input data.
    if field is None or field.strip() == "" or field.strip().upper() == "N/A":
        return None
    return field.strip()

def parse_name(fields):
    # Parses names considering possible middle name issues.
    if fields[1] == "N/M/N":
        return f"{fields[0]} {fields[2]}"
    return " ".join(fields[:3]).strip()

def format_zip_code(zip_code):
    # Formats the ZIP code to ZIP+4 format if necessary.
    clean_zip = re.sub(r'\D', '', zip_code)
    if len(clean_zip) == 9:
        return f"{clean_zip[:5]}-{clean_zip[5:]}"
    return clean_zip

def parse_xml(file_path):
    # Parses an XML file and extracts entity data into a structured format.
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        entries = []
        for ent in root.findall('.//ENTITY/ENT'):
            data = {
                'name': validate_field(ent.find('NAME').text),
                'organization': validate_field(ent.find('COMPANY').text),
                'street': validate_field(ent.find('STREET').text),
                'city': validate_field(ent.find('CITY').text),
                'state': validate_field(ent.find('STATE').text),
                'zip': format_zip_code(validate_field(ent.find('POSTAL_CODE').text))
            }
            entries.append({k: v for k, v in data.items() if v is not None})
        return entries
    except IOError as e:
        sys.stderr.write(f"Error reading XML file: {e}\n")
        sys.exit(1)
    except ET.ParseError as e:
        sys.stderr.write(f"Error parsing XML file: {e}\n")
        sys.exit(1)

def parse_tsv(file_path):
    # Parses a TSV file and converts it into a structured list of dictionaries.
    try:
        with open(file_path, 'r') as file:
            entries = []
            for line in file:
                fields = line.rstrip('\n').split('\t')
                entry = {
                    'name': parse_name(fields),
                    'organization': validate_field(fields[3]),
                    'street': validate_field(fields[4]),
                    'city': validate_field(fields[5]),
                    'state': validate_field(fields[6]),
                    'county': validate_field(fields[7]),
                    'zip': format_zip_code(f"{fields[8]}-{fields[9]}")
                }
                entries.append({k: v for k, v in entry.items() if v is not None})
            return entries
    except IOError as e:
        sys.stderr.write(f"Error reading TSV file: {e}\n")
        sys.exit(1)

def parse_txt(file_path):
    # Parses a TXT file and extracts entity data into a structured format.
    entries = []
    try:
        with open(file_path, 'r') as file:
            data = file.read()
            # Split the input data into separate entries
            data_blocks = data.strip().split('\n\n')

            for block in data_blocks:
                lines = block.strip().split('\n')
                name = lines[0].strip()
                street = lines[1].strip()
                
                county = ""  # Default county to empty if not provided
                
                if len(lines) > 3:
                    # County information is present
                    county = lines[2].replace("COUNTY", "").strip()
                
                # Extract the city, state, and zip using regex
                pattern = r"(.+?),\s*(.+?)\s*(\d{5}-?\d{0,4})"
                match = re.search(pattern, lines[len(lines) - 1].strip())
                if match:
                    city, state, zip_code = match.groups()
                    # Create dictionary for current entry
                    entry = {
                        "name": validate_field(name),
                        "street": validate_field(street),
                        "city": validate_field(city),
                        "state": validate_field(state),
                        "county": validate_field(county),
                        "zip": format_zip_code(zip_code)
                    }
                    entries.append({k: v for k, v in entry.items() if v is not None})
                else:
                    # Handle entries with malformed or missing address information
                    print(f"Error parsing block: {block}")
        return entries
    except IOError as e:
        sys.stderr.write(f"Error reading TXT file: {e}\n")
        sys.exit(1)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Parse address files and output JSON sorted by ZIP code.')
    parser.add_argument('files', metavar='FILE', type=str, nargs='+', help='Files to process')
    args = parser.parse_args()

    # Define file parsers based on file extensions
    file_parsers = {
        '.xml': parse_xml,
        '.tsv': parse_tsv,
        '.txt': parse_txt,
    }

    data = []
    # Process each file provided as argument
    for file_path in args.files:
        file_ext = file_path[file_path.rfind('.'):]
        parser_func = file_parsers.get(file_ext)
        if parser_func:
            # Call the appropriate parser function based on file extension
            data.extend(parser_func(file_path))
        else:
            # Handle unsupported file formats
            sys.stderr.write(f'Error: Unsupported file format in {file_path}\n')
            sys.exit(1)
    
    if not data:
        # Exit if no valid address data found
        sys.stderr.write('Error: No valid address data found.\n')
        sys.exit(1)

    # Sort data by ZIP code and output as JSON
    sorted_data = sorted(data, key=lambda x: x['zip'])
    print(json.dumps(sorted_data, indent=2))

if __name__ == "__main__":
    main()
