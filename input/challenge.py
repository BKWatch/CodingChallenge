import json
import xml.etree.ElementTree as ET
import csv
import sys
import argparse
import os

file_path1 = 'input1.xml'
file_path2 = 'input2.tsv'
file_path3 = 'input3.txt'


def parse_xml(file_path):
    addresses = []

    tree = ET.parse(file_path)
    root = tree.getroot()
    for ent in root.findall('.//ENT'):
        address_info = {}

        name = ent.find('NAME').text.strip() if ent.find('NAME').text else ""
        company = ent.find('COMPANY').text.strip() if ent.find('COMPANY').text else ""
        if name:
            address_info['name'] = name
        elif company:
            address_info['organization'] = company
        address_info['street'] = ent.find('STREET').text.strip() if ent.find('STREET').text else ""
        address_info['city'] = ent.find('CITY').text.strip() if ent.find('CITY').text else ""
        address_info['state'] = ent.find('STATE').text.strip() if ent.find('STATE').text else ""
        postal_code = ent.find('POSTAL_CODE').text.strip() if ent.find('POSTAL_CODE').text else ""
        address_info['zip'] = postal_code.split('-')[0].strip()
        addresses.append(address_info)
    return addresses

def parse_tsv(file_path):
    addresses = []
    expected_columns = 10  
    with open(file_path, 'r', encoding='utf-8') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')

        next(reader, None)
        for row in reader:
            if len(row) < expected_columns:
                print(f"Skipping row with missing columns: {row}")
                continue

            address_info = {}
            name_parts = [row[0].strip(), row[1].strip(), row[2].strip()]
            name = ' '.join(part for part in name_parts if part)
            if name: 
                address_info['name'] = name

            if row[3].strip():  
                address_info['organization'] = row[3].strip()

            address_info['street'] = row[4].strip()
            address_info['city'] = row[5].strip()
            address_info['county'] = row[6].strip()
            address_info['state'] = row[7].strip()
            zip_code = row[8].strip()
            zip_plus4 = row[9].strip()
            address_info['zip'] = f"{zip_code}-{zip_plus4}" if zip_plus4 else zip_code

            addresses.append(address_info)
    return addresses

def parse_txt(file_path):
    addresses = []
    address_info = {}
    state_abbreviation_map = {"Florida": "FL", "California": "CA", "Arizona": "AZ", "Michigan": "MI", "Georgia": "GA", "Alabama": "AL", "Texas": "TX", "New Jersey": "NJ", "New York": "NY", "Illinois": "IL", "Wisconsin": "WI", "Ohio": "OH", "Pennsylvania": "PA", "South Carolina": "SC"}

    with open(file_path, 'r', encoding='utf-8') as file:
        entries = file.read().strip().split('\n\n')
        
        for entry in entries:
            lines = entry.split('\n')
            address_info['name'] = lines[0].strip()
            address_info['street'] = lines[1].strip()

            city_state_zip = lines[-1].strip()
            parts = city_state_zip.split(',')
            city = parts[0].strip()
            state_zip = parts[1].strip().split(' ')
            state = state_zip[0]
            zip_code = state_zip[1] if len(state_zip) > 1 else ""

            state = state_abbreviation_map.get(state, state)
            address_info['city'] = city
            address_info['state'] = state
            address_info['zip'] = zip_code.strip('-') 

            if 'COUNTY' in lines[-3].upper():
                address_info['county'] = lines[-3].split(' ')[0].strip()
            else:
                address_info['county'] = ""  

            addresses.append(address_info)
            address_info = {}

    return addresses

def main(files):
    combined_data = []
    for file in files:
        if file.endswith('.xml'):
            combined_data.extend(parse_xml(file))
        elif file.endswith('.tsv'):
            combined_data.extend(parse_tsv(file))
        elif file.endswith('.txt'):
            combined_data.extend(parse_txt(file))
        else:
            sys.stderr.write(f"Error: Unsupported file type for {file}\n")
            sys.exit(1)
    combined_data.sort(key=lambda x: x['zip'])
    print(json.dumps(combined_data, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Combine and sort addresses from different file formats.')
    parser.add_argument('files', metavar='F', type=str, nargs='+',help='an input file path')
    args = parser.parse_args()

    main(args.files)
