import argparse
import json
import os
import sys
import csv
import xml.etree.ElementTree as ET
class XMLParser:
    @staticmethod
    def parse(file_path):
        addresses = []
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            for entry in root.findall('.//ENTITY/ENT'):
                address = {}
                for child in entry:
                    if child.tag == 'NAME':
                        address['name'] = child.text.strip()
                    elif child.tag == 'COMPANY':
                        address['organization'] = child.text.strip()
                    elif child.tag == 'STREET':
                        address['street'] = child.text.strip()
                    elif child.tag == 'STREET_2':
                        address['street'] += child.text.strip()
                    elif child.tag == 'street_3':
                        address['street'] += child.text.strip()
                    elif child.tag == 'CITY':
                        address['city'] = child.text.strip()
                    elif child.tag == 'COUNTRY':
                        address['county'] = child.text.strip()
                    elif child.tag == 'STATE':
                        address['state'] = child.text.strip()
                    elif child.tag == 'POSTAL_CODE':
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
    def parse(file_path):
        addresses = []
        try:
            with open(file_path, 'r') as file:
                reader = csv.DictReader(file, delimiter='\t')
                for row in reader:
                    cleaned_zip, cleaned_zip4 = TSVParser.clean_value(row.get('zip', '')), TSVParser.clean_value(row.get('zip4', ''))
                    merged_zip = cleaned_zip + " - " + cleaned_zip4 if cleaned_zip4 else cleaned_zip
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
                    address = {
                        'name': name,
                        'organization': organization,
                        'street': TSVParser.clean_value(row.get('address', '')),
                        'city': TSVParser.clean_value(row.get('city', '')),
                        'state': TSVParser.clean_value(row.get('state', '')),
                        'zip': merged_zip
                    }
                    addresses.append(address)
        except Exception as e:
            sys.stderr.write(f"Error parsing TSV file {file_path}: {str(e)}\n")
            sys.exit(1)
        return addresses
   
    def clean_value(value):
        cleaned = value.strip() if value else ""
        return "" if cleaned in ("N/A", "N/M/N") else cleaned
    
class TextParser:
    @staticmethod
    def parse(file_path):
        with open(file_path, 'r') as file:
            addresses = file.readlines()
        parsed_addresses = []
        address_lines = []
        for line in addresses:
            if line.strip():
                address_lines.append(line.strip())
            else:
                if address_lines:
                    parsed_address = TextParser.parse_address(address_lines)
                    parsed_addresses.append(parsed_address)
                    address_lines = []
        if address_lines:
            parsed_address = TextParser.parse_address(address_lines)
            parsed_addresses.append(parsed_address)
        return parsed_addresses

    @staticmethod
    def parse_address(address_lines):
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
        city_state_zip_parts = last_line_parts[-1].split(' ')
        city = last_line_parts[0]
        state = city_state_zip_parts[-2]
        zip_code = city_state_zip_parts[-1]

        return {
            'name': name.strip(),
            'organization': organization.strip(),
            'street': street.strip(),
            'city': city.strip(),
            'county': county.strip(),
            'state': state.strip(),
            'zip': zip_code.strip()
        }

def custom_zip_key(address):
    zip_code = address.get('zip', '')
    if '-' in zip_code:
    # If hyphen exists, split the string and take the first part
        first_zip_part = zip_code.split('-')[0].strip()
    else:
    # If hyphen doesn't exist, take the whole string as the ZIP code
        first_zip_part = zip_code.strip()
    
    return first_zip_part

def main():
    parser = argparse.ArgumentParser(description='Parse US names and addresses from various file formats')
    parser.add_argument('files', metavar='file', type=str, nargs='+', help='input files to parse (supported formats: .xml, .tsv, .txt)')
    args = parser.parse_args()

    if not args.files:
        sys.stderr.write("Error: No input files provided.")
        sys.exit(1)
    

    

    addresses = []
    valid_formats = ['.xml', '.tsv', '.txt']
    for file_path in args.files:
        ext = os.path.splitext(file_path)[1].lower()
        if not os.path.exists(file_path):
            sys.stderr.write("Error: No input files provided or path does not exist.")
            sys.exit(1)
        try:
       
            if ext == '.xml':
                addresses.extend(XMLParser.parse(file_path))
            elif ext == '.tsv':
                addresses.extend(TSVParser.parse(file_path))
            elif ext == '.txt':
                addresses.extend(TextParser.parse(file_path))
            else:
                sys.stderr.write(f"Unsupported file format: {ext}\n")
                sys.exit(1)
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}", file=sys.stderr)
            sys.exit(1)

    if addresses:
        addresses.sort(key=custom_zip_key)

        try:
            json_addresses = json.dumps(addresses, indent=2)
            with open("output.json", "w") as json_file:
                json_file.write(json_addresses)
                print(json_addresses)
                print("Success: Addresses successfully written to output.json", file=sys.stdout)
                sys.exit(0)
            
           
        except Exception as e:
            sys.stderr.write(f"Error encoding addresses to JSON: {str(e)}\n")
            sys.exit(1)
    else:
        sys.stderr.write("No addresses found.\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
