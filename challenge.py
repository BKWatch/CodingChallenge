import argparse
import json
import os
import sys
import csv
import xml.etree.ElementTree as ET

class XMLParser:
    @staticmethod
    def parse(file_path) -> list:
        addresses = []
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            if root.tag != 'EXPORT':
                sys.stderr.write(f"Error: XML file {file_path} does not have the expected structure.\n")
                sys.exit(1)
            for entry in root.findall('.//ENTITY/ENT'):
                address = {}
                for child in entry:
                    if child.tag == 'NAME' and child.text.strip():
                        address['name'] = child.text.strip()
                    elif child.tag == 'COMPANY' and child.text.strip():
                        address['organization'] = child.text.strip()
                    elif child.tag == 'STREET' and child.text.strip():
                        address['street'] = child.text.strip()
                    elif child.tag == 'CITY' and child.text.strip():
                        address['city'] = child.text.strip()
                    elif child.tag == 'STATE' and child.text.strip():
                        address['state'] = child.text.strip()
                    elif child.tag == 'POSTAL_CODE' and child.text.strip():
                        postal_code = child.text.strip()
                        if postal_code.endswith('-'):
                            postal_code = postal_code[:-1]
                        address['zip'] = postal_code.strip()
                addresses.append(address)
        except ET.ParseError as e:
            sys.stderr.write(f"Error parsing XML file {file_path}: {str(e)}\n")
            sys.exit(1)
        return addresses

class TSVParser:
    @staticmethod
    def parse(file_path) -> list:
        addresses = []
        try:
            with open(file_path, 'r') as file:
                reader = csv.DictReader(file, delimiter='\t')
                expected_headers = ['first', 'middle', 'last', 'organization', 'address', 'city', 'state', 'county', 'zip', 'zip4']
                if reader.fieldnames != expected_headers:
                    sys.stderr.write(f"Error: TSV file {file_path} does not have the expected headers.\n")
                    sys.exit(1)
                for row in reader:
                    address = {}
                    cleaned_zip, cleaned_zip4 = TSVParser.clean_value(row.get('zip', '')), TSVParser.clean_value(row.get('zip4', ''))
                    merged_zip = cleaned_zip + "-" + cleaned_zip4 if cleaned_zip4 else cleaned_zip
                    first_name = TSVParser.clean_value(row.get('first', ''))
                    middle_name = TSVParser.clean_value(row.get('middle', ''))
                    last_name = TSVParser.clean_value(row.get('last', ''))
                    name = " ".join([first_name, middle_name, last_name]).strip()
                    organization = TSVParser.clean_value(row.get('organization', ''))
                    name_contains_keyword = any(keyword in part.lower() for part in [last_name] for keyword in ['llc', 'ltd.', 'inc.'])

                    if name_contains_keyword:
                        if organization:
                            organization += ", " + last_name
                        else:
                            organization = last_name
                        name = ""
                    if name:
                        address['name'] = name
                    if organization:
                        address['organization'] = organization
                    address['street'] = TSVParser.clean_value(row.get('address', ''))
                    address['city'] = TSVParser.clean_value(row.get('city', ''))
                    address['state'] = TSVParser.clean_value(row.get('state', ''))
                    # address['zip'] = merged_zip
                    merged_zip = cleaned_zip + "-" + cleaned_zip4 if cleaned_zip4 else cleaned_zip
                    if merged_zip.endswith('-'):
                        merged_zip = merged_zip[:-1]
                    address['zip'] = merged_zip
                    addresses.append(address)

        except Exception as e:
            sys.stderr.write(f"Error parsing TSV file {file_path}: {str(e)}\n")
            sys.exit(1)
        return addresses

    @staticmethod
    def clean_value(value) -> str:
        cleaned = value.strip() if value else ""
        return "" if cleaned.lower() in ("n/a", "n/m/n") else cleaned

class TextParser:
    @staticmethod
    def parse(file_path) -> list:
        try:
            with open(file_path, 'r') as file:
                address_lines = file.readlines()
            parsed_addresses = []
            for line in address_lines:
                if line.strip():
                    address_lines.append(line.strip())
                else:
                    if address_lines:
                        try:
                            parsed_address = TextParser.parse_address(address_lines)
                            parsed_addresses.append(parsed_address)
                        except Exception as e:
                            sys.stderr.write(f"Error parsing address in TXT file {file_path}: {str(e)}\n")
                        address_lines = []
            if address_lines:
                try:
                    parsed_address = TextParser.parse_address(address_lines)
                    parsed_addresses.append(parsed_address)
                except Exception as e:
                    sys.stderr.write(f"Error parsing address in TXT file {file_path}: {str(e)}\n")
        except Exception as e:
            sys.stderr.write(f"Error opening or reading TXT file {file_path}: {str(e)}\n")
            sys.exit(1)
        return parsed_addresses

    @staticmethod
    def parse_address(address_lines) -> dict:
        address = {}
        first_line = address_lines[0].lower()
        keywords = ['llc', 'ltd', 'inc']
        if any(keyword in first_line for keyword in keywords):
            organization = address_lines[0]
            name = ''
        else:
            organization = ''
            name = address_lines[0]

        street = address_lines[1]
        second_last_line = address_lines[-2]
        county = second_last_line.strip() if 'COUNTY' in second_last_line else ''
        last_line_parts = address_lines[-1].split(', ')
        city = last_line_parts[0]
        state_zip = last_line_parts[1].rsplit(' ', 1)
        state = state_zip[0]
        zip_code = state_zip[1]

        if name:
            address['name'] = name.strip()
        if organization:
            address['organization'] = organization.strip()
        address['street'] = street.strip()
        address['city'] = city.strip()
        if county:
            address['county'] = county.strip()
        address['state'] = state.strip()
        # address['zip'] = zip_code.strip()
        state_zip = last_line_parts[1].rsplit(' ', 1)
        state = state_zip[0]
        zip_code = state_zip[1]
        if zip_code.endswith('-'):
            zip_code = zip_code[:-1]
        address['zip'] = zip_code.strip()

        return address

def main():
    parser = argparse.ArgumentParser(description='Parse address files and output JSON.')
    parser.add_argument('files', metavar='F', type=str, nargs='+',
                        help='a list of files to parse')
    args = parser.parse_args()

    if not args.files:
        sys.stderr.write("Error: No input files provided.\n")
        sys.exit(1)

    all_addresses = []
    for filename in args.files:
        if not os.path.exists(filename):
            sys.stderr.write(f"Error: File {filename} does not exist.\n")
            sys.exit(1)
        elif filename.endswith('.tsv'):
            all_addresses.extend(TSVParser.parse(filename))
        elif filename.endswith('.xml'):
            all_addresses.extend(XMLParser.parse(filename))
        elif filename.endswith('.txt'):
            all_addresses.extend(TextParser.parse(filename))
        else:
            sys.stderr.write(f'Error: Unknown file type for file {filename}\n')
            sys.exit(1)

    if all_addresses:
        all_addresses.sort(key=lambda x: x.get('zip', ''))
        print(json.dumps(all_addresses, indent=4))
        sys.exit(0)  # Exit with status 0 on success
    else:
        sys.stderr.write("Error: No addresses found.\n")
        sys.exit(1)  # Exit with status 1 on failure

if __name__ == "__main__":
    main()
