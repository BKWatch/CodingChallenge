import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from csv import reader


def parse_xml(file_path):
    addresses = []
    tree = ET.parse(file_path)
    root = tree.getroot()
    for entity in root.findall('.//ENTITY/ENT'):
        name = entity.find('NAME').text.strip()
        organization = entity.find('COMPANY').text.strip()
        street = entity.find('STREET').text.strip()
        city = entity.find('CITY').text.strip()
        county = entity.find('COUNTY').text.strip() if entity.find('COUNTY') is not None else ''
        state = entity.find('STATE').text.strip()
        zip_code = entity.find('POSTAL_CODE').text.strip()
        if ' - ' in zip_code:
            zip_code = zip_code.replace(' - ', '-')
        else:
            zip_code = zip_code.replace(' -', '')

        address = {}
        if name:
            address['name'] = name
        if organization:
            address['organization'] = organization
        address['street'] = street
        address['city'] = city
        if county:
            address['county'] = county
        address['state'] = state
        address['zip'] = zip_code

        addresses.append(address)

    return addresses


def parse_tsv(file_path):
    addresses = []
    with open(file_path, 'r') as tsvfile:
        tsvreader = reader(tsvfile, delimiter='\t')
        next(tsvreader)
        for row in tsvreader:
            name = ' '.join(row[:3]).strip()
            if 'N/M/N' in name:
                name = name.replace(' N/M/N ', ' ')
            organization = row[3].strip()
            street = row[4].strip()
            city = row[5].strip()
            state = row[6].strip()
            county = row[7].strip()
            zip_code = row[8].strip()
            if row[9]:
                zip_code += '-' + row[9].strip()

            address = {}
            if name:
                address['name'] = name
            if organization != 'N/A':
                address['organization'] = organization
            address['street'] = street
            address['city'] = city
            if county:
                address['county'] = county
            address['state'] = state
            address['zip'] = zip_code

            addresses.append(address)

    return addresses


def parse_txt(file_path):
    addresses = []
    with open(file_path, 'r') as txtfile:
        lines = [line.strip() for line in txtfile.readlines()]
        address = {}
        county = ''
        for line in lines:
            if not line:
                if address:
                    addresses.append(address)
                address = {}
                county = ''
                continue

            try:
                address['name']
            except KeyError:
                address['name'] = line
                continue

            try:
                address['street']
            except KeyError:
                address['street'] = line
                continue

            if 'COUNTY' in line:
                county = line.replace(' COUNTY', '')
                continue

            city_state = line.split(', ')
            state, zip_code = city_state[1].rsplit(' ', 1)
            address['city'] = city_state[0]
            if county:
                address['county'] = county
            address['state'] = state
            address['zip'] = zip_code.strip('-')

    return addresses


def parse_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.xml':
        return parse_xml(file_path)
    if ext == '.tsv':
        return parse_tsv(file_path)
    if ext == '.txt':
        return parse_txt(file_path)

    sys.stderr.write(f"Error: Unsupported file format for {file_path}\n")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Parse US addresses from various file formats and output as JSON.')
    parser.add_argument('files', metavar='file', type=str, nargs='+', help='input file paths')
    args = parser.parse_args()

    all_addresses = []
    for file_path in args.files:
        all_addresses.extend(parse_file(file_path))

    sorted_addresses = sorted(all_addresses, key=lambda x: x['zip'])
    print(json.dumps(sorted_addresses, indent=2))


if __name__ == "__main__":
    main()
