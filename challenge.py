import argparse
import json
import sys
import os
import xml.etree.ElementTree as ET
import re
import csv

def parse_arguments():
    parser = argparse.ArgumentParser(description='Parse and combine US addresses from multiple file formats (.xml, .tsv, .txt).')
    parser.add_argument('files', metavar='FILE', type=str, nargs='+', help='List of file paths to process')
    # parser.add_argument('--help', action='help', help='Show this help message and exit')
    return parser.parse_args()

def parse_xml(file_path):
    addresses = []
    tree = ET.parse(file_path)
    root = tree.getroot()

    for ent in root.findall('.//ENT'):
        address = {}
        name_element = ent.find('NAME')
        company_element = ent.find('COMPANY')

        name = name_element.text.strip() if name_element is not None and name_element.text.strip() != "" else None
        company = company_element.text.strip() if company_element is not None else None

        if name:
            address['name'] = name
        elif company:
            address['organization'] = company

        address['street'] = ent.find('STREET').text.strip()
        street_2 = ent.find('STREET_2').text
        if street_2:
            address['street'] += ' ' + street_2.strip()

        address['city'] = ent.find('CITY').text.strip()
        # address['county'] = ent.find('COUNTY').text.strip()
        address['state'] = ent.find('STATE').text.strip()
        postal_code = ent.find('POSTAL_CODE').text.strip()
        address['zip'] = postal_code.split('-')[0].strip()

        addresses.append(address)

    return addresses


def parse_tsv(file_path):
    addresses = []
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        next(reader)
        for row in reader:
            if len(row) >= 9:
                address = {}
                first, middle, last, organization, street, city, state, county, zipcode, zip4 = row[:10]

                if organization.strip().upper() == 'N/A':
                    if first.strip() == '' and middle.strip().upper() == '':
                        address['organization'] = last.strip()
                    elif middle.strip().upper() == 'N/M/N':
                        name_parts = [part.strip() for part in (first, last) if part.strip()]
                        address['name'] = ' '.join(name_parts)
                    else:
                        name_parts = [part.strip() for part in (first, middle, last) if part.strip()]
                        address['name'] = ' '.join(name_parts)

                else:
                    address['organization'] = organization.strip()

                address['street'] = street.strip()
                address['city'] = city.strip()
                if county:
                    address['county'] = county.strip()
                address['state'] = state.strip()
                
                address['zip'] = zipcode.strip()
                if zip4:
                    address['zip'] += '-' + zip4.strip()

                addresses.append(address)

    return addresses



def parse_txt(file_path):
    addresses = []
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read().strip()
        entries = content.split('\n\n')
        for entry in entries:
            lines = [line.strip() for line in entry.split('\n') if line.strip()]
            if not lines:
                continue
            address = {}
            name_line = lines[0]
            if name_line.isupper():
                
                parts = name_line.split(',')
                if len(parts) > 1:
                    address['name'] = ' '.join(parts[:-1]).strip()
                    address['county'] = parts[-1].strip()
                else:
                    address['name'] = name_line
            else:
                
                address['name'] = name_line

            address['street'] = lines[1]

            if len(lines) > 3:
                
                address['county'] = lines[2].upper()
                city_state_zip = lines[3]
            else:
                city_state_zip = lines[2]

            
            city_state_zip_parts = city_state_zip.split(',')
            city = city_state_zip_parts[0].strip()
            state_zip = city_state_zip_parts[1].strip() if len(city_state_zip_parts) > 1 else ''

            address['city'] = city

            if state_zip:
                state_zip_parts = re.split(r'\s+', state_zip, maxsplit=1)
                address['state'] = state_zip_parts[0]
                address['zip'] = ''.join(state_zip_parts[1:]).replace('-', '')
            else:
                print(f"Failed to parse state and zip correctly: {city_state_zip}")
                print("Skipping entry due to incorrect formatting.")
                continue

            addresses.append(address)
    return addresses




def process_files(file_paths):
    addresses = []
    for path in file_paths:
        if path.endswith('.xml'):
            addresses.extend(parse_xml(path))
        elif path.endswith('.tsv'):
            addresses.extend(parse_tsv(path))
        elif path.endswith('.txt'):
            addresses.extend(parse_txt(path))
        else:
            sys.stderr.write(f"Unsupported file format: {path}\n")
            sys.exit(1)
    return sorted(addresses, key=lambda x: x['zip'])

def main():
    args = parse_arguments()
    try:
        all_addresses = process_files(args.files)
        print(json.dumps(all_addresses, indent=2))
    except Exception as e:
        sys.stderr.write(str(e) + '\n')
        sys.exit(1)

if __name__ == "__main__":
    main()
