#!/usr/bin/env python3

import argparse
import sys
import json
import xml.etree.ElementTree as ET
import re
import csv
from csv import reader

def parse_xml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        entries = []

        for ent in root.findall('.//ENT'):
            name = ent.find('NAME').text.strip() if ent.find('NAME').text else None
            company = ent.find('COMPANY').text.strip() if ent.find('COMPANY').text else None
            street = ent.find('STREET').text.strip() if ent.find('STREET').text else None
            city = ent.find('CITY').text.strip() if ent.find('CITY').text else None
            state = ent.find('STATE').text.strip() if ent.find('STATE').text else None
            postal_code = ent.find('POSTAL_CODE').text.strip() if ent.find('POSTAL_CODE').text else None

            # remove dashes and spaces from zipcode
            if postal_code:
                postal_code = postal_code.split('-')[0].strip()

            entry = {}
            if name:
                entry['name'] = name
            if company:
                entry['organization'] = company
            if street:
                entry['street'] = street
            if city:
                entry['city'] = city
            if state:
                entry['state'] = state
            if postal_code:
                entry['zip'] = postal_code

            entries.append(entry)

        return entries
    except Exception as e:
        print(f"Error parsing XML file: {str(e)}", file=sys.stderr)
        return None

def parse_tsv(file_path):
    try:
        with open(file_path, 'r') as file:
            tsv_reader = csv.DictReader(file, delimiter='\t')
            entries = []
            
            for row in tsv_reader:
                # combine first, middle, last into a full name if organization is not provided
                if row['organization'].strip() == 'N/A' or row['organization'].strip() == '':
                    name_parts = [row['first'], row['middle'], row['last']]
                    name = ' '.join(part for part in name_parts if part != 'N/A' and part.strip() != '')
                    entry = {
                        'name': name,
                        'street': row['address'].strip(),
                        'city': row['city'].strip(),
                        'state': row['state'].strip(),
                        'zip': row['zip'].strip() + ('-' + row['zip4'].strip() if row['zip4'].strip() != '' else '')
                    }
                    if row['county'].strip() != '':
                        entry['county'] = row['county'].strip()
                else:
                    entry = {
                        'organization': row['organization'].strip(),
                        'street': row['address'].strip(),
                        'city': row['city'].strip(),
                        'state': row['state'].strip(),
                        'zip': row['zip'].strip() + ('-' + row['zip4'].strip() if row['zip4'].strip() != '' else '')
                    }
                    if row['county'].strip() != '':
                        entry['county'] = row['county'].strip()

                entries.append(entry)

            return entries
    except Exception as e:
        print(f"Error parsing TSV file: {str(e)}", file=sys.stderr)
        return None

def parse_txt(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read().strip()
            # split into entries based on two or more newline characters which seem to separate entries
            entries = re.split(r'\n{2,}', content)
            parsed_entries = []

            for entry in entries:
                lines = entry.split('\n')
                lines = [line.strip() for line in lines if line.strip()]

                if len(lines) < 3:
                    continue  # skip entries that don't have enough lines

                # name is always the first line
                name = lines[0]

                # last line should be the city, state, and zip
                city_state_zip = lines[-1]
                zip_code_search = re.search(r'(\d{5}(?:-\d{4})?)', city_state_zip)
                zip_code = zip_code_search.group(1) if zip_code_search else None

                # extract city and state
                city_state = re.sub(r'\d.*', '', city_state_zip).strip()
                city, state = map(str.strip, city_state.split(','))

                # add address to second line and check for county presence
                street = lines[1]
                county = None
                if 'COUNTY' in street.upper():
                    county = street.replace('COUNTY', '').strip()
                    street = lines[2]  # if there's a county, street address moves to the next line

                parsed_entries.append({
                    'name': name,
                    'street': street,
                    'city': city,
                    'state': state,
                    'zip': zip_code,
                    **({'county': county} if county else {})
                })

            return parsed_entries
    except Exception as e:
        print(f"Error parsing TXT file: {str(e)}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description='Process US names and addresses.')
    parser.add_argument('files', metavar='FILE', type=str, nargs='+',
                        help='Path to the file containing US names and addresses.')
    args = parser.parse_args()

    entries = []
    for file_path in args.files:
        if file_path.endswith('.xml'):
            result = parse_xml(file_path)
        elif file_path.endswith('.tsv'):
            result = parse_tsv(file_path)
        elif file_path.endswith('.txt'):
            result = parse_txt(file_path)
        else:
            print(f"Unsupported file format: {file_path}", file=sys.stderr)
            sys.exit(1)

        if result is None:
            sys.exit(1)
        entries.extend(result)

    entries.sort(key=lambda x: x['zip'])
    print(json.dumps(entries, indent=4))

if __name__ == "__main__":
    main()
