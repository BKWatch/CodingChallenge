import argparse
import csv
import json
import os
import sys
import xml.etree.ElementTree as ET

def parse_xml(file_path):
    addresses = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for entity in root.findall('.//ENT'):
            address = {}
            for child in entity:
                if child.tag == 'NAME' and child.text.strip() != "":
                    address['name'] = child.text.strip()
                elif child.tag == 'COMPANY' and child.text.strip() != "":
                    address['organization'] = child.text.strip()
                elif child.tag == 'STREET':
                    address['street'] = child.text.strip()
                elif child.tag == 'CITY':
                    address['city'] = child.text.strip()
                elif child.tag == 'COUNTY':
                    address['county'] = child.text.strip().upper()
                elif child.tag == 'STATE':
                    address['state'] = child.text.strip()
                elif child.tag == 'POSTAL_CODE':
                    address['zip'] = child.text.strip().split('-')[0]
            addresses.append(address)
    except Exception as e:
        print(f"Error parsing XML file {file_path}: {e}", file=sys.stderr)
        return None

    return addresses

def parse_tsv(file_path):
    addresses = []
    try:
        with open(file_path, 'r') as tsvfile:
            reader = csv.DictReader(tsvfile, delimiter='\t')
            for row in reader:
                address = {}
                if row['first'] and row['last']:
                    address['name'] = f"{row['first']} {row['middle']} {row['last']}".strip()
                elif row['organization'].strip() != "":
                    address['organization'] = row['organization']
                address['street'] = row['address']
                address['city'] = row['city']
                address['state'] = row['state']
                if row['county']:
                    address['county'] = row['county'].upper()
                address['zip'] = row['zip']
                addresses.append(address)
    except Exception as e:
        print(f"Error parsing TSV file {file_path}: {e}", file=sys.stderr)
        return None
    return addresses

def parse_txt(file_path):
    addresses = []
    try:
        with open(file_path, 'r') as txtfile:
            lines = [line.strip() for line in txtfile.readlines() if line.strip()]
            i = 0
            while i < len(lines):
                if not lines[i]:  # Skip empty lines
                    i += 1
                    continue

                address = {}
                name = lines[i]
                address['name'] = name
                i += 1

                street = lines[i]
                address['street'] = street
                i += 1

                if ',' in lines[i]:
                    city_state_zip_parts = lines[i].split(',')
                else:
                    address['county'] = lines[i]
                    i += 1
                    city_state_zip_parts = lines[i].split(',')

                address['city'] = city_state_zip_parts[0].strip()
                address_state_zip_parts = city_state_zip_parts[1].rsplit(' ', 1)
                address['state'] = address_state_zip_parts[0].strip()
                address['zip'] = address_state_zip_parts[1].strip()

                addresses.append(address)
                i += 1

    except Exception as e:
        print(f"Error parsing TXT file {file_path}: {e}", file=sys.stderr)
        return None

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
        print(f"Unsupported file format: {extension}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="Parse US addresses from input files and output as JSON")
    parser.add_argument("files", metavar="FILE", type=str, nargs="+", help="path to input files")
    args = parser.parse_args()

    addresses = []
    for file_path in args.files:
        file_addresses = parse_file(file_path)
        if file_addresses is None:
            sys.exit(1)
        addresses.extend(file_addresses)

    sorted_addresses = sorted(addresses, key=lambda x: x.get('zip', ''))
    print(json.dumps(sorted_addresses, indent=2))

if __name__ == "__main__":
    main()
