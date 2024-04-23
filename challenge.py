import argparse
import csv
import json
import os
import sys
import xml.etree.ElementTree as ET


def parse_xml(file_path):
    addresses = []
    tree = ET.parse(file_path)
    root = tree.getroot()
    for ent in root.findall('ENTITY/ENT'):
        address = {}
        name = ent.find('NAME').text.strip()
        if name:
            address['name'] = name
        else:
            address['organization'] = ent.find('COMPANY').text.strip()

        address['street'] = ent.find('STREET').text.strip()
        address['city'] = ent.find('CITY').text.strip()
        address['state'] = ent.find('STATE').text.strip()
        address['zip'] = ent.find('POSTAL_CODE').text.strip().split('-')[0]

        county = ent.find('COUNTY')
        if county is not None:
            address['county'] = county.text.strip()

        addresses.append(address)
    return addresses


def parse_tsv(file_path):
    addresses = []
    with open(file_path, 'r', newline='') as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter='\t')
        for row in reader:
            address = {
                'organization': row['organization'],
                'street': row['address'],
                'city': row['city'],
                'state': row['state'],
                'zip': row['zip']
            }
            addresses.append(address)
    return addresses


def parse_txt(file_path):
    addresses = []
    with open(file_path, 'r') as txtfile:
        lines = txtfile.readlines()
        address = {}
        for line in lines:
            line = line.strip()
            if line:
                if not address.get('name'):
                    address['name'] = line
                elif not address.get('street'):
                    address['street'] = line
                elif 'COUNTY' in line:
                    address['county'] = line
                elif ',' in line:
                    city_state_zip = line.split(',')
                    address['city'] = city_state_zip[0].strip()
                    state_zip = city_state_zip[1].strip().split()
                    address['state'] = state_zip[0]
                    address['zip'] = state_zip[1].split('-')[0]
                    addresses.append(address)
                    address = {}
                
    return addresses


def parse_file(file_path):
    if file_path.endswith('.xml'):
        return parse_xml(file_path)
    elif file_path.endswith('.tsv'):
        return parse_tsv(file_path)
    elif file_path.endswith('.txt'):
        return parse_txt(file_path)
    else:
        raise ValueError("Unsupported file format")


def main():
    parser = argparse.ArgumentParser(description="Parse US names and addresses files")
    parser.add_argument('files', metavar='file', type=str, nargs='+', help="Paths to input files")
    args = parser.parse_args()

    all_addresses = []
    for file_path in args.files:
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist", file=sys.stderr)
            sys.exit(1)

        try:
            addresses = parse_file(file_path)
            all_addresses.extend(addresses)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}", file=sys.stderr)
            sys.exit(1)

    all_addresses.sort(key=lambda x: x['zip'])

    print(json.dumps(all_addresses, indent=2))


if __name__ == "__main__":
    main()
