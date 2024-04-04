import xml.etree.ElementTree as ET
import csv
import sys
import json
import re
from collections import OrderedDict

# Define the order of keys in the output dictionary
order = ['name', 'organization', 'street', 'address', 'city', 'county', 'state', 'zip']

# Define US states and their abbreviations
us_states_list = [
    'Alabama', 'AL',
    'Alaska', 'AK',
    'Arizona', 'AZ',
    'Arkansas', 'AR',
    'California', 'CA',
    'Colorado', 'CO',
    'Connecticut', 'CT',
    'Delaware', 'DE',
    'Florida', 'FL',
    'Georgia', 'GA',
    'Hawaii', 'HI',
    'Idaho', 'ID',
    'Illinois', 'IL',
    'Indiana', 'IN',
    'Iowa', 'IA',
    'Kansas', 'KS',
    'Kentucky', 'KY',
    'Louisiana', 'LA',
    'Maine', 'ME',
    'Maryland', 'MD',
    'Massachusetts', 'MA',
    'Michigan', 'MI',
    'Minnesota', 'MN',
    'Mississippi', 'MS',
    'Missouri', 'MO',
    'Montana', 'MT',
    'Nebraska', 'NE',
    'Nevada', 'NV',
    'New Hampshire', 'NH',
    'New Jersey', 'NJ',
    'New Mexico', 'NM',
    'New York', 'NY',
    'North Carolina', 'NC',
    'North Dakota', 'ND',
    'Ohio', 'OH',
    'Oklahoma', 'OK',
    'Oregon', 'OR',
    'Pennsylvania', 'PA',
    'Rhode Island', 'RI',
    'South Carolina', 'SC',
    'South Dakota', 'SD',
    'Tennessee', 'TN',
    'Texas', 'TX',
    'Utah', 'UT',
    'Vermont', 'VT',
    'Virginia', 'VA',
    'Washington', 'WA',
    'West Virginia', 'WV',
    'Wisconsin', 'WI',
    'Wyoming', 'WY'
]

# Replace spaces with underscores to match the pattern in the text data
us_states = [key.replace(" ", "_") for key in us_states_list]

# Function to parse XML files
def parse_xml(file_path):
    try:
        tree = ET.parse(file_path)
    except ET.ParseError as e:
        print(f"Error parsing XML file '{file_path}': {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error parsing XML file '{file_path}': {e}", file=sys.stderr)
        return []

    root = tree.getroot()
    output = []

    for ent in root.findall('./ENTITY/ENT'):
        entry = {}
        # Extract data from XML tags
        name = ent.find('NAME')
        company = ent.find('COMPANY')
        street = ent.find('STREET')
        city = ent.find('CITY')
        county = ent.find('COUNTY')
        state = ent.find('STATE')
        postal_code = ent.find('POSTAL_CODE')

        # Populate entry dictionary with non-empty fields
        if name is not None and name.text.strip():
            entry['name'] = name.text.strip()
        if company is not None and company.text.strip():
            entry['organization'] = company.text.strip()
        if street is not None and street.text.strip():
            entry['street'] = street.text.strip()
        if city is not None and city.text.strip():
            entry['city'] = city.text.strip()
        if county is not None and county.text.strip():
            entry['county'] = county.text.strip()
        if state is not None and state.text.strip():
            entry['state'] = state.text.strip()
        if postal_code is not None and postal_code.text.strip():
            entry['zip'] = postal_code.text.strip()

        # If entry is not empty, append to output list
        if entry:
            output.append(entry)

    return output

# Function to parse TSV files
def parse_tsv(file_path):
    try:
        with open(file_path, 'r', newline='') as file:
            reader = csv.DictReader(file, delimiter='\t')
            data = []

            for entry in reader:
                # Combine zip and zip4 fields and format name
                entry["zip"] = entry.get('zip', '') + "-" + entry.get("zip4", "")
                entry['name'] = " ".join([entry.get("first", ""), entry.get("middle", ""), entry.get("last", "")])
                # Strip whitespace from all fields and filter out empty fields
                entry = {k: v.strip() for k, v in entry.items() if v.strip() != '' and v != 'N/A'}
                # Order the fields as defined in 'order' list
                arr_entry = OrderedDict((key, entry[key]) for key in order if key in entry)
                data.append(arr_entry)

            return data
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error parsing TSV file '{file_path}': {e}", file=sys.stderr)
        return []

# Function to parse TXT files
def parse_txt(file_path):
    try:
        with open(file_path, 'r') as file:
            li = []
            reader = file.read().split("\n\n")

            for row in reader:
                entry = {}
                row_data = row.split("\n")
                if len(row_data) > 1:
                    entry['name'] = row_data[0].strip()
                    entry['street'] = row_data[1].strip()

                    for iteration in row_data[2:]:
                        # Replace state names with abbreviations in the text data
                        pattern = re.compile(r'\b(?:' + '|'.join(us_states_list) + r')\b')
                        iteration = pattern.sub(lambda match: match.group().replace(" ", "_"), iteration)

                        check = iteration.strip().split(" ")
                        for index, i in enumerate(check):
                            if i in us_states:
                                entry['state'] = check[index]
                                entry['zip'] = check[index + 1]
                                entry['city'] = " ".join(check[0: index])[:-1]

                        if "county" in iteration.lower():
                            entry['county'] = iteration.strip()

                if entry:
                    # Order the fields as defined in 'order' list
                    arr_entry = dict(OrderedDict((key, entry[key]) for key in order if key in entry))
                    li.append(arr_entry)

            return li
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error parsing TXT file '{file_path}': {e}", file=sys.stderr)
        return []

# Function to parse all types of files
def parse_files(file_paths):
    combined_addresses = []
    for file_path in file_paths:
        if file_path.endswith('.tsv'):
            combined_addresses.extend(parse_tsv(file_path))
        elif file_path.endswith('.xml'):
            combined_addresses.extend(parse_xml(file_path))
        elif file_path.endswith('.txt'):
            combined_addresses.extend(parse_txt(file_path))
        else:
            print(f"Error: Unsupported file format for '{file_path}'", file=sys.stderr)

    # Exit with status code 1 if no addresses are parsed
    if not combined_addresses:
        sys.exit(1)

    # Sort addresses by ZIP code
    combined_addresses.sort(key=lambda x: x.get("zip", "").split('-')[0])

    return combined_addresses

# Function to print usage instructions
def print_help():
    print("Usage: python script.py [file1 file2 ...]")
    print("Parses XML, TSV, and TXT files containing address information.")
    print("Supported file formats: .xml, .tsv, .txt")
    print("Output: JSON list of addresses")

# Main function
if __name__ == "__main__":
    # Check if there are enough arguments or if the '--help' option is used
    if len(sys.argv) < 2:
        print("Error: At least one file path should be provided.", file=sys.stderr)
        print()
        print_help()
        sys.exit(1)
    elif sys.argv[1] == '--help':
        print_help()
        sys.exit(0)
    
    # Parse file paths from command line arguments
    file_paths = sys.argv[1:]

    # Parse addresses from input files
    addresses = parse_files(file_paths)

    # Convert addresses to JSON format
    json_output = json.dumps(addresses, indent=2)
    print(json_output)

    # Exit with status code 0 to indicate success
    sys.exit(0)
