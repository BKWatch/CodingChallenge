"""
Assumtion: 
    For xml file:
        street_3 only exists if there is street_2
        street_2 only exists if there is street
    For tsv file:
        Every person has first name, and last name
"""

import sys
import os
import json
import argparse
import csv
import xml.etree.ElementTree as ET


def parse_xml(file_path):
    addresses = []
    tree = ET.parse(file_path)
    root = tree.getroot()
    tags = {
        'NAME': 'name',
        'COMPANY': 'organization',
        'STREET': 'street',
        'STREET_2': 'street_2',
        'STREET_3': 'street_3',
        'CITY': 'city',
        'COUNTY': 'county',
        'STATE': 'state',
        'POSTAL_CODE': 'zip'
    }

    for entry in root.findall('.//ENT'):
        address = {}
        for child in entry:
            for tag in tags:
                if child.tag == tag:
                    value = child.text.strip()
                    if tag in ['STREET_2', 'STREET_3'] and value != '':
                        address['street'] += ", " + value
                    elif tag == 'POSTAL_CODE':
                        address[tags[tag]] = value.strip("- ").replace(" - ", "-")
                    elif value != '':
                        address[tags[tag]] = value
        addresses.append(address)
    return addresses


def parse_tsv(file_path):
    addresses = []
    tags = ['name', 'middle', 'last', 'organization', 'street', 'city', 'state', 'county', 'zip', 'zip4']
    with open(file_path, 'r', newline='') as file:
        tsv_reader = csv.reader(file, delimiter='\t')
        next(tsv_reader)
        for row in tsv_reader:
            address = {}
            for i in range(len(tags)):
                value = row[i].strip()
                if value == '' or value == 'N/M/N':
                    continue
                address[tags[i]] = value

            # Trim the address
            if 'name' not in address and 'last' in address:
                address['organization'] = address['last']
                address.pop('last')
            if 'name' in address:
                if 'middle' in address:
                    address['name'] += ' ' + address['middle']
                    address.pop('middle')
                address['name'] += ' ' + address['last']
                address.pop('last')
            if 'organization' in address and address['organization'] == 'N/A':
                address.pop('organization')
            if 'zip4' in address:
                address['zip'] += '-' + address['zip4']
                address.pop('zip4')
            addresses.append(address)
    return addresses


def parse_txt(file_path):
    addresses = []
    with open(file_path, 'r') as file:
        paragraphs = file.read().split('\n\n')

        for paragraph in paragraphs:
            address = {}
            lines = paragraph.split('\n')

            if len(lines) == 3:
                last_line = lines[2].strip().split(',')
                address = {
                    'name': lines[0].strip(),
                    'street': lines[1].strip(),
                    'city': last_line[0],
                    'state': ' '.join(last_line[1].strip().split(' ')[:-1]),
                    'zip': last_line[1].strip("- ").split(' ')[-1]
                }
            elif len(lines) == 4:
                last_line = lines[3].strip().split(',')
                address = {
                    'name': lines[0].strip(),
                    'street': lines[1].strip(),
                    'county': lines[2].strip().split(' ')[0],
                    'city': last_line[0],
                    'state': ' '.join(last_line[1].strip().split(' ')[:-1]),
                    'zip': last_line[1].strip("- ").split(' ')[-1]
                }
            if address:
                addresses.append(address)
    return addresses


def parse_file(file_path):
    _, extension = os.path.splitext(file_path)
    if extension == '.xml':
        return parse_xml(file_path)
    elif extension == '.tsv':
        return parse_tsv(file_path)
    elif extension == '.txt':
        return parse_txt(file_path)
    else:
        raise ValueError("Unsupported file format")


def validate_address(address):
    required_fields = ['street', 'city', 'state', 'zip']
    if not any(field in address for field in required_fields):
        return False
    if 'name' in address and 'organization' in address:
        return False
    if 'name' not in address and 'organization' not in address:
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description='Parse and combine US addresses from multiple file formats')
    parser.add_argument('files', metavar='FILE', type=str, nargs='+', help='Input file paths')
    args = parser.parse_args()

    all_addresses = []
    for file_path in args.files:
        try:
            all_addresses = parse_file(file_path)
        except Exception as e:
            print(f"Error parsing file '{file_path}': {str(e)}", file=sys.stderr)
            sys.exit(1)

    valid_addresses = [address for address in all_addresses if validate_address(address)]
    sorted_addresses = sorted(valid_addresses, key=lambda x: x['zip'])

    if sorted_addresses:
        print(json.dumps(sorted_addresses, indent=2))
    else:
        print("No valid addresses found", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
