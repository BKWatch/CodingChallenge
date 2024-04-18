# File: challenge.py

import sys
import json
import csv
import argparse
import xml.etree.ElementTree as ET


# Convert txt file records to standardized address format
def text_to_addresses(txt_file):
    addresses = []
    with open(txt_file, 'r') as file:
        lines = file.readlines()
        i = 0
        end = len(lines)
        lines = [line.strip() for line in lines]
        
        while i <= end - 3:
            #Skip blank lines
            if lines[i].strip() == '':
                i += 1
                continue
            
            name = lines[i]
            street = lines[i+1]
            county = ''
            city_state_zip = ''
            state_zip = ''
            city = ''
            state = ''
            zipcode = ''
            #Check for presence of county data    
            if lines[i+2].endswith('COUNTY'):
                county = lines[i+2].strip()
                city_state_zip = lines[i+3].strip('-')
                x = 4
                
            else:
                county = 'N/A'
                city_state_zip = lines[i+2].strip('-')
                x = 3
                
            city_state = city_state_zip.split(', ')
            
            if len(city_state) == 2:
                city = city_state[0]
                state_zip = city_state[1]
                state_zip = state_zip.rsplit(maxsplit=1)
                
            if len(state_zip) == 2:
                state = state_zip[0]
                zipcode = state_zip[1]
                   
            address = {
                'name': name,
                'street': street,
                'city': city,
                'county': county,
                'state': state,
                'zip': zipcode,
                }
            addresses.append(address)
            i += x     
    return addresses


# Convert tsv file records to standardized address format
def tsv_to_addresses(tsv_file):
    addresses = []
    with open(tsv_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            
            first = row.get('first')
            middle = row.get('middle')
            last = row.get('last')
            organization_name = row.get('organization')
            # Parsing for missing name data or mislabeled company names
            if first == '' and middle == '':
                if last.endswith('LLC') or last.endswith('Ltd.') or last.endswith('Inc.'):
                    organization_name = last
                    full_name = ''
 
            elif middle == '' or middle == 'N/M/N':
                full_name = first + ' ' + last
                
            else:
                full_name = first + ' ' + middle + ' ' + last
            
            address = {
                'name': full_name,
                'organization': organization_name,
                'street': row.get('address'),
                'city': row.get('city'),
                'county': row.get('county'),
                'state': row.get('state'),
                'zip': row.get('zip')
                }
            addresses.append(address)
    return addresses


# Convert xml file records to standardized address format
def xml_to_addresses(xml_file):
    addresses = []
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    for ent in root.findall('.//ENTITY/ENT'):
        name = ent.findtext('NAME')
        organization = ent.findtext('COMPANY')
        street = ent.findtext('STREET')
        city = ent.findtext('CITY')
        state = ent.findtext('STATE')
        postal_code = ent.findtext('POSTAL_CODE')
        zipcode = postal_code.split('-')[0].strip() if postal_code else ''
        
        address = {
            'name': name,
            'organization': organization,
            'street': street,
            'city': city,
            'state': state,
            'zip': zipcode
            }
        addresses.append(address)
    return addresses


#Sorts address list by zip code
def sort_addresses_by_zip(addresses):
    return sorted(addresses, key=lambda x: x['zip'])


#Checks that file arguments match expected types
def validate_files(files):
    for file in files:
        if not file.endswith(('.txt', '.tsv', '.xml')):
            sys.stderr.write(
                f"Error: Invalid file format for {file}\n"
                )
            return False
    return True


#Main function for converting file data to a list of addresses to JSON objects
def main(files):
    if not validate_files(files):
        sys.exit(1)

    all_addresses = []
    for file in files:
        if file.endswith('.txt'):
            all_addresses.extend(text_to_addresses(file))
            print(len(all_addresses))
            
        elif file.endswith('.tsv'):
            all_addresses.extend(tsv_to_addresses(file))
            print(len(all_addresses))
            
        elif file.endswith('.xml'):
            all_addresses.extend(xml_to_addresses(file))
            print(len(all_addresses))

    sorted_addresses = sort_addresses_by_zip(all_addresses)
    print(json.dumps(sorted_addresses, indent=4))

#Adds -help functionality
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse files containing addresses and output them in sorted order."
        )
    parser.add_argument(
        'files', nargs='+', help="List of files to parse."
        )
    args = parser.parse_args()

    main(args.files)

