#!/usr/bin/env python
# coding: utf-8

# In[100]:


import json
import re
import xml.etree.ElementTree as ET
from collections import OrderedDict
import csv
import sys



import xml.etree.ElementTree as ET
from collections import OrderedDict

def parse_xml(filepath):
    addresses = []
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    for entity in root.findall('.//ENT'):
        address = OrderedDict()
        name = entity.find('NAME').text
        company = entity.find('COMPANY').text.strip() if entity.find('COMPANY').text else ''
        street = entity.find('STREET').text
        city = entity.find('CITY').text
        state = entity.find('STATE').text
        postal_code = entity.find('POSTAL_CODE').text.strip() if entity.find('POSTAL_CODE').text else ''
        
        if name:
            name_parts = name.split()
            formatted_name = ' '.join(name_parts)
            if formatted_name.strip():  
                address['name'] = formatted_name
        if company:
            address['organization'] = company
        if street:  
            address['street'] = street
        if city:  
            address['city'] = city
        if state:  
            address['state'] = state
        if postal_code:  
            address['zip'] = postal_code
               
        if any(address.values()):
            addresses.append(address)
    return addresses


def clean_value(value):
    if value in ('N/A', 'N/M/N'):
        return ''
    return value.strip()

def parse_tsv(filepath):
    addresses = []
    with open(filepath, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        
        header = next(reader)
        column_mapping = {col: i for i, col in enumerate(header)}

        organization_keywords = ['LLC', 'Ltd', 'Corporation', 'Inc']

        for row in reader:
            address = OrderedDict()
            name_parts = []
            invalid_name = False
            
            for column in ['first', 'middle', 'last']:
                index = column_mapping.get(column, -1)
                value = clean_value(row[index]) if index != -1 and index < len(row) else ""
                if any(keyword in value for keyword in organization_keywords):
                    print(f"Error in row: {' '.join(row)}. '{column}' column contains organization name.", file=sys.stderr)
                    invalid_name = True
                    break
                if value:
                    name_parts.append(value)

            if invalid_name:
                continue
            
            if name_parts:
                address['name'] = ' '.join(name_parts)
            
            for column in ['organization', 'address', 'city', 'state', 'zip']:
                index = column_mapping.get(column, -1)
                value = clean_value(row[index]) if index != -1 and index < len(row) else ""
                if value:
                    address[column] = value

            if address:
                addresses.append(address)
    
    return addresses




def is_organization(line):
    organization_keywords = ['LLC', 'Ltd', 'Corporation', 'Inc']
    return any(keyword in line for keyword in organization_keywords)

def contains_county(line):
    return "county" in line.lower()

us_states = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
    "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
    "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
    "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
    "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
]

def parse_txt(filepath):
    addresses = []
    with open(filepath, 'r') as file:
        entries = file.read().strip().split('\n\n')
        for entry in entries:
            lines = entry.split('\n')
            address = OrderedDict()
            
            first_line = lines[0]
            if is_organization(first_line):
                address['organization'] = first_line
            else:
                address['name'] = first_line

            address['street'] = lines[1]
            
            city_index, county_index, state_zip_index = (2, None, -1)

            for i, line in enumerate(lines[2:], start=2):
                if contains_county(line):
                    county_index = i
                    address['county'] = line
                    city_index += 1  
                    
            address['city'] = lines[city_index].split(',')[0].strip()
            
            match = re.search(r'([A-Z]{2})[^\d]*(\d{5})(?:-\d{4})?.*$', lines[state_zip_index])
            if match:
                address['state'] = match.group(1)
                address['zip'] = match.group(2)
            else:
                state_zip_parts = re.split(r',\s*', lines[state_zip_index], maxsplit=1)[1]  
                state_zip_parts =re.split(r'(\d+-?.*)',state_zip_parts)           
                if state_zip_parts[0].strip() in us_states:
                    #print(state_zip_parts[0])
                    address['state'] = state_zip_parts[0]
                    address['zip'] = state_zip_parts[1]
                else:
                    print(f"Skipping entry in TXT due to malformed address: {entry}", file=sys.stderr)
                    continue

            addresses.append(address)
    return addresses



def aggregate_and_save_addresses(file_paths, output_files):
    all_addresses_xml = []
    all_addresses_tsv = []
    all_addresses_txt = []

    # Process each file and aggregate addresses by file type
    for file_path in file_paths:
        if file_path.endswith('.xml'):
            all_addresses_xml.extend(parse_xml(file_path))
        elif file_path.endswith('.tsv'):
            all_addresses_tsv.extend(parse_tsv(file_path))
        elif file_path.endswith('.txt'):
            all_addresses_txt.extend(parse_txt(file_path))
        else:
            print(f"Error: Unsupported file format for {file_path}")

    # Sort addresses by ZIP code for each file type
    sorted_addresses_xml = sorted(all_addresses_xml, key=lambda x: x.get('zip', ''))
    sorted_addresses_tsv = sorted(all_addresses_tsv, key=lambda x: x.get('zip', ''))
    sorted_addresses_txt = sorted(all_addresses_txt, key=lambda x: x.get('zip', ''))


    # Save the sorted addresses to different files
    for addresses, output_file_path in zip([sorted_addresses_xml, sorted_addresses_tsv, sorted_addresses_txt], output_files):
        json_output = json.dumps(addresses, indent=2)
        with open(output_file_path, 'w') as f:
            f.write(json_output)

# Example usage:
file_paths = ['input1.xml', 'input2.tsv', 'input3.txt']
output_files = ['output_xml.json', 'output_tsv.json', 'output_txt.json']  
aggregate_and_save_addresses(file_paths, output_files)


# In[ ]:




