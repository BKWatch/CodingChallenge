"""
Created on Sat Apr 13 1:18:23 2024

@author: Esraa Aldreabi
"""
#import libraries 
import sys
import json
import xml.etree.ElementTree as ET
import csv
import os
import argparse
import re

def parse_xml_file(file_path):  #Parsing files with extension: .xml.
    tree = ET.parse(file_path)
    root = tree.getroot()
    addresses = []
    for ent in root.findall('.//ENT'):
        data = {}
        for element in ent:
            key = element.tag.lower()  
            if key == 'postal_code': 
                key = 'zip'
            data[key] = element.text.strip()
            if data[key].endswith('-'): # For cases where zip code ends with dash(-) example:12345-.
                data[key] = data[key][:-1].strip()
        addresses.append(data)
    return addresses

def parse_tsv_file(file_path):  #Parsing files with extension: .tsv.
    addresses = []
    with open(file_path, newline='') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            
            if not row['first'].strip() and not row['middle'].strip() and not row['last'].strip(): # Check if the entry should be treated as an organization or personal name.
                name = ''
                organization = row['organization'].strip() if row['organization'].strip() else row['last'].strip()
            else:
                
                name_parts = [row['first'], row['middle'], row['last']]
                cleaned_name_parts = [part for part in name_parts if part and part != "N/M/N"] # Remove N/M/N from middle name.
                name = ' '.join(cleaned_name_parts)
                organization = ''

            address = {
                'name': name,
                'organization': organization,
                'street': row['address'],
                'city': row['city'],
                'state': row['state'],
                'zip': row['zip'] + ('-' + row['zip4'] if row['zip4'] else ''),
                'county': row['county'] if row['county'] else None
            }
            addresses.append(address)
    return addresses




def parse_txt_file(file_path): #Parsing files with extension: .txt.
    addresses = []
    with open(file_path, 'r') as file:
        content = file.read().strip().split('\n\n')
        for block in content:
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            if len(lines) < 3:
                continue

            address = {'name': lines[0], 'street': lines[1], 'city': '', 'state': '', 'zip': '', 'county': ''}

            # Look for county in the line immediately before the city-state-zip
            city_state_zip_index = None
            for i, line in enumerate(lines[2:]):
                city_state_zip_pattern = re.compile(r'^(.*?),\s*([\w\s]+)\s+(\d{5}(?:-\d{4})?)-*$')
                match = city_state_zip_pattern.search(line)
                if match:
                    address['city'] = match.group(1).strip()
                    address['state'] = match.group(2).strip()
                    address['zip'] = match.group(3).strip() if match.group(3) else ''
                    city_state_zip_index = i + 2
                    break

            # Check if there's a line before the city-state-zip line that could be the county
            if city_state_zip_index and city_state_zip_index > 2:
                possible_county_line = lines[city_state_zip_index - 1]
                if 'county' in possible_county_line.lower():
                    address['county'] = possible_county_line.replace('County', '').replace('COUNTY', '').strip()

            addresses.append(address)
    return addresses





def format_and_sort_addresses(addresses): # Sort addresses by ZIP code in ascending order.
    formatted_addresses = []
    for address in addresses:
        
        formatted_address = {}
        if address.get('name'):
            formatted_address['name'] = address['name']
        if address.get('organization'):
            formatted_address['organization'] = address['organization']
        formatted_address['street'] = address['street']
        formatted_address['city'] = address['city']
        if address.get('county'):
            formatted_address['county'] = address['county']
        formatted_address['state'] = address['state']
        
        zip_code = address['zip']
        if len(zip_code) == 9 and '-' not in zip_code:
            zip_code = zip_code[:5] + '-' + zip_code[5:]
        formatted_address['zip'] = zip_code
        
        formatted_addresses.append(formatted_address)
    
    
    return sorted(formatted_addresses, key=lambda x: x['zip'])







def parse_arguments(): #To provide -help functionality and check one of errors cases.
    parser = argparse.ArgumentParser(description='Process address files (XML, TSV, TXT).')
    parser.add_argument('files', nargs='+', help='Files to process. Must end with .xml, .tsv, or .txt')
    args = parser.parse_args()


    valid_extensions = ('.xml', '.tsv', '.txt')
    for file in args.files:
        if (not file.endswith(valid_extensions) 
            or not os.path.exists(file)):
            sys.stderr.write(f"Error: File {file} is not found or has an unsupported type.\n")
            sys.exit(1)
    return args



def main():
    args = parse_arguments()
    all_addresses = []

    for file_path in args.files:
        if file_path.endswith('.xml'):
            addresses = parse_xml_file(file_path)
        elif file_path.endswith('.tsv'):
            addresses = parse_tsv_file(file_path)
        elif file_path.endswith('.txt'):
            addresses = parse_txt_file(file_path)
        else:
            sys.stderr.write(f"Error:Unsupported file type: {file_path}\n")
            sys.exit(1)

        if (addresses is None 
            or len(addresses) == 0):
            sys.stderr.write(f"Error processing file or no valid data found: {file_path}\n")
            sys.exit(1)
        all_addresses.extend(addresses)

    if not all_addresses:
        sys.stderr.write("Error: No valid addresses found in any of the provided files.\n")
        sys.exit(1)

    sorted_addresses = format_and_sort_addresses(all_addresses)
    print(json.dumps(sorted_addresses, indent=4))
    sys.exit(0)

if __name__ == "__main__":
    main()
