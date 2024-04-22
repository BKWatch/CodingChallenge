import argparse
import json
import sys
import csv

import xml.etree.ElementTree as ET

def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    root = root.find('ENTITY')
    addresses = []
    for person in root.findall('ENT'):
        address = {}
        name = person.find('NAME')
        if name is not None:
            address['name'] = name.text
        organization = person.find('ORGANIZATION')
        if organization is not None:
            address['organization'] = organization.text
        street = person.find('STREET')
        if street is not None:
            address['street'] = street.text
        city = person.find('CITY')
        if city is not None:
            address['city'] = city.text
        county = person.find('COUNTY')
        if county is not None:
            address['county'] = county.text
        state = person.find('STATE')
        if state is not None:
            address['state'] = state.text
        zip_code = person.find('POSTAL_CODE')
        if zip_code is not None:
            zip_text = zip_code.text
            zip_text = zip_text.replace(' ', '')
            if '-' in zip_text:
                zip_parts = zip_text.split('-')
                if len(zip_parts) > 1:
                    if zip_parts[1].isdigit():
                        zip_text = '-'.join(zip_parts)
                    else:
                        zip_text = zip_parts[0]
                else:  
                    zip_text = zip_parts[0]
            address['zip'] = zip_text
        addresses.append(address)
    return addresses

def parse_tsv(file_path):
    addresses = []
    with open(file_path, 'r') as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter='\t')
        for row in reader:
            address = {}
            first_name = row.get('first')
            middle_name = row.get('middle')
            last_name = row.get('last')
            name = ''
            if first_name:
                name += first_name
            if middle_name and middle_name != 'N/M/N':
                name += ' ' + middle_name
            if last_name:
                name += ' ' + last_name
            if name:
                address['name'] = name.strip()
            organization = row.get('organization')
            if organization and organization != 'N/A':
                address['organization'] = organization
            address['street'] = row.get('address')
            address['city'] = row.get('city')
            county = row.get('county')
            if county:
                address['county'] = county
            address['state'] = row.get('state')
            zip_code = row.get('zip')
            zip4_code = row.get('zip4')
            if zip_code and zip4_code:
                address['zip'] = f"{zip_code}-{zip4_code}"
            else:
                address['zip'] = zip_code
            addresses.append(address)
    return addresses

def parse_txt(file_path):
    addresses = []
    with open(file_path, 'r') as txt_file:
        lines = txt_file.read().split('\n\n')
        for line in lines:
            if line.strip():
                address = {}
                parts = line.strip().split('\n')
                address['name'] = parts[0].strip()
                address['street'] = parts[1].strip()
                if len(parts) > 3:
                    county = parts[2].strip().split()[0] if parts[2].strip().endswith('COUNTY') else None
                    if county:
                        address['county'] = county
                    city_state_zip = parts[3].strip().split(',')
                    city, state_zip = city_state_zip[0], city_state_zip[1]
                else:
                    city_state_zip = parts[2].strip().split(',')
                    city, state_zip = city_state_zip[0], city_state_zip[1]
                address['city'] = city
                state_zip_parts = state_zip.strip().split()
                address['state'] = state_zip_parts[0]
                zip_code = state_zip_parts[1]
                if '-' in zip_code:
                    zip_parts = zip_code.split('-')
                    if len(zip_parts) > 1:
                        if zip_parts[1].isdigit():
                            zip_code = '-'.join(zip_parts)
                        else:
                            zip_code = zip_parts[0]
                    else:  
                        zip_code = zip_parts[0]
                address['zip'] = zip_code

                addresses.append(address)
    return addresses

def parse_file(file_path):
    if file_path.endswith('.xml'):
        return parse_xml(file_path)
    elif file_path.endswith('.tsv'):
        return parse_tsv(file_path)
    elif file_path.endswith('.txt'):
        return parse_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")

def parse_files(file_paths):
    addresses = []
    for file_path in file_paths:
        try:
            addresses.extend(parse_file(file_path))
        except Exception as e:
            sys.stderr.write(f"Error parsing file {file_path}: {str(e)}\n")
            sys.exit(1)
    return addresses

def sort_addresses(addresses):
    return sorted(addresses, key=lambda x: x.get('zip', ''))

def main():
    parser = argparse.ArgumentParser(description='Parse names and addresses.')
    parser.add_argument('files', metavar='file', type=str, nargs='+',
                        help='pathnames of files to parse')
    args = parser.parse_args()
    addresses = parse_files(args.files)
    sorted_addresses = sort_addresses(addresses)
    json_output = json.dumps(sorted_addresses, indent=2)
    print(json_output)

if __name__ == '__main__':
    main()

