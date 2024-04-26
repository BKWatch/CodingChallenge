# Finished by Jiacheng Zhao at 7:11 PM (CDT)
# on April 25, 2024 in Texas

import argparse
import json
import sys
import xml.etree.ElementTree as ET
import re
from csv import DictReader


def parse_xml(file_path):
    addresses = []
    tree = ET.parse(file_path)
    root = tree.getroot()
    for ent in root.findall('.//ENT'):
        name = ent.find('NAME').text.strip()
        company = ent.find('COMPANY').text.strip()
        street = ent.find('STREET').text.strip()
        street2 = ent.find('STREET_2').text.strip()
        if street2 != None:
            street = street + ' ' + street2
        if street[-1] == ' ':
            street = street[:-1]
        city = ent.find('CITY').text.strip()
        state = ent.find('STATE').text.strip()
        zipcode = ent.find('POSTAL_CODE').text.strip().split()

        address = {}
        if name:
            address['name'] = name
        if company:
            address['organization'] = company
        address['street'] = street
        address['city'] = city
        address['state'] = state
        address['zip'] = zipcode[0] if len(
            zipcode) == 2 else zipcode[0] + zipcode[1] + zipcode[2]
        addresses.append(address)
    return addresses


def parse_tsv(file_path):
    addresses = []
    with open(file_path, newline='') as file:
        tsv_file = DictReader(file, delimiter='\t')
        for row in tsv_file:

            # if the data represent a person
            if row['first'].strip() and row['middle'].strip() and row['last'].strip():
                if row['middle'] != 'N/M/N':
                    row['first'] = f"{row['first']} {row['middle']}"
                row.pop('middle')
                row['first'] = f"{row['first']} {row['last']}"
                if row['first'][-1] == ',':
                    row['first'] = row['first'][:-1]
                row.pop('last')
                row.pop('organization')

            # if the data represents an organization
            elif not row['first'].strip() and not row['middle'].strip():
                row.pop('first')
                row.pop('middle')
                if row['last'].strip():
                    # some organizations' names are in the 'last' tab in tsv file
                    row['organization'] = row['last']
                row.pop('last')

            if row['zip4'].strip():  # 9-digit zip code
                row['zip'] = f"{row['zip']}-{row['zip4']}"
            row.pop('zip4')

            if not row['county'].strip():
                row.pop('county')
            else:
                state = row.pop('state')
                county = row.pop('county')
                zipcode = row.pop('zip')
                row['county'] = county
                row['state'] = state
                row['zip'] = zipcode
            new_row = {{'first': 'name', 'address': 'street'}.get(
                key, key): value for key, value in row.items()}
            addresses.append(new_row)

    return addresses


def parse_txt(file_path):
    addresses = []
    with open(file_path, 'r') as textFile:
        content = textFile.read()
    blocks = re.split(r'\n\s*\n', content.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue  # Skip blocks that don't have enough lines
        name = lines[0].strip()
        street = lines[1].strip()
        if (len(lines) == 4):  # block contains county
            raw_county = lines[2].strip()
            county = raw_county.split()[0]
            city_state_zip = lines[3].strip()
        else:  # no county in the block
            county = None
            city_state_zip = lines[2].strip()
        csz = city_state_zip.split(',')
        city = csz[0]
        state_zip = csz[1].split()
        # scenarios like "New Jersey"
        state = state_zip[0] if len(
            state_zip) == 2 else state_zip[0] + ' ' + state_zip[1]
        zipcode = state_zip[1] if len(state_zip) == 2 else state_zip[2]
        if city[-1] == ',':
            city = city[:-1]
        if zipcode[-1] == '-':
            zipcode = zipcode[:-1]

        address = {'name': name, 'street': street, 'city': city}
        if (county != None):  # do not output county if no county is in this row of data
            address['county'] = county
        address['state'] = state
        address['zip'] = zipcode
        addresses.append(address)

    return addresses


def main():
    parser = argparse.ArgumentParser(
        description="Parse and combine address lists.\n Only .xml, .tsv and .txt files are allowed.")
    parser.add_argument("file_path", nargs='+', help="List of file paths")
    args = parser.parse_args()

    combined_addresses = []
    for file_path in args.file_path:
        if file_path.endswith('.xml'):
            combined_addresses.extend(parse_xml(file_path))
            print("\n\nParsed successfully from .xml file\n")
        elif file_path.endswith('.tsv'):
            combined_addresses.extend(parse_tsv(file_path))
            print("\n\nParsed successfully from .tsv file\n")
        elif file_path.endswith('.txt'):
            combined_addresses.extend(parse_txt(file_path))
            print("\n\nParsed successfully from .txt file\n")
        else:
            sys.stderr.write(f"Error: Unsupported file type {file_path}.\n")
            sys.exit(1)

    # Sort addresses by zip code
    combined_addresses.sort(key=lambda x: x['zip'])

    try:
        # Print JSON to stdout
        json.dump(combined_addresses, sys.stdout, indent=4)
        print("\n\nJson printed successfully")
        sys.exit(0)
    except Exception as e:
        # If an error occurs during JSON dumping or any other process
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

