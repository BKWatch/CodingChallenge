import xml.etree.ElementTree as ET
import csv
import json
import re
import argparse
import sys


def parse_xml_to_json(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    data = []
    clean_data = []
    for entity in root.findall('.//ENT'):
        item = {}
        for child in entity:
            if child.tag == 'NAME':
                item['name'] = child.text.strip()
            if child.tag == 'COMPANY':
                item['organization'] = child.text.strip()
            if child.tag == 'STREET':
                item['street'] = child.text.strip()
            if child.tag == 'STREET_2':
                item['street'] += ' ' + child.text.strip()
            if child.tag == 'STREET_3':
                item['street'] += ' ' + child.text.strip()
            if child.tag == 'CITY':
                item['city'] = child.text.strip()
            if child.tag == 'STATE':
                item['state'] = child.text.strip()
            if child.tag == 'POSTAL_CODE':
                item['zip'] = child.text.strip(' -')
                
               
                
        data.append(item)
        
    for item in data:
        keys_to_remove = [key for key, value in item.items() if value in ['', ' ','   ',"  ", "N/A",None]]
        for key in keys_to_remove:
                item.pop(key) 
        clean_data.append(item)
    return clean_data


def parse_tsv_to_json(tsv_file):
    data = []
    clean_data = []
    with open(tsv_file, 'r', newline='', encoding='utf-8') as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter='\t')
        for row in reader:
            item = {}
            if row['middle'] == 'N/M/N':
                if row['last'].strip().lower()[-3:] in ['llc', 'nc.', 'td.']:
                    item['organization'] = row['last']
                    item['name'] = row['first']
                else:
                    item['organization'] = row['organization']
                    item['name'] = f"{row['first']} {row['last']}"
            else:
                if row['last'].strip().lower()[-3:] in ['llc', 'nc.', 'td.']:
                    item['name'] = f"{row['first']} {row['middle']}"
                    item['organization'] = row['last']
                else:
                    item['organization'] = row['organization']
                    item['name'] = f"{row['first']} {row['middle']} {row['last']}"

            item['street'] = row['address']
            item['city'] = row['city'].capitalize()
            item['zip'] = f"{row['zip']}-{row['zip4']}".strip('-')
            
            
            data.append(item)
        for item in data:
            keys_to_remove = [key for key, value in item.items() if value in ['', ' ','   ',"  ", "N/A",None]]
            for key in keys_to_remove:
                    item.pop(key) 
            clean_data.append(item)
    return clean_data
    


def parse_txt_to_json(txt_file):
    data = []
    clean_data = []
    pattern = re.compile(r'^(.*),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)$')
    with open(txt_file, 'r') as file:
        file_content = file.read().strip()
        entries_raw = file_content.split('\n\n')
        
        for entry_raw in entries_raw:
            lines = entry_raw.split('\n')
            name = lines[0].strip()
            street = lines[1].strip()
            if len(lines) == 4:
                if 'county' in lines[2].lower():
                    county = lines[2].strip().capitalize()
                else:
                    county = None
            else:
                county = None
            
            city_zip_state_parts = lines[-1].split(', ')
            city = city_zip_state_parts[0].strip().capitalize()
            zip_code = city_zip_state_parts[-1].split()[-1].strip('-')
            state = ' '.join(city_zip_state_parts[-1].split()[:-1]).strip()
            
            
            if name.strip() and street.strip() and city.strip() and zip_code.strip() and state.strip():
                item = {
                    "name": name,
                    "street": street,
                    "city": city,
                    "state": state,
                    "zip": zip_code
                }
                if county:
                    item['county'] = county
                
                
                   
                
                data.append(item)
        
        for item in data:
            keys_to_remove = [key for key, value in item.items() if value in ['', ' ','   ',"  ", "N/A",None]]
            for key in keys_to_remove:
                item.pop(key) 
            clean_data.append(item)
    return clean_data    
                
            
    


def main():
    parser = argparse.ArgumentParser(description='Parse and combine addresses from different file formats')
    parser.add_argument('files', nargs='+', help='List of pathnames of files to be parsed')
    
    args = parser.parse_args()

    combined_data = []
    for file in args.files:
        file_type = file.split('.')[-1].lower()
        if file_type == 'xml':
            combined_data.extend(parse_xml_to_json(file))
        elif file_type == 'tsv':
            combined_data.extend(parse_tsv_to_json(file))
        elif file_type == 'txt':
            combined_data.extend(parse_txt_to_json(file))
        else:
            print(f"Error: Unsupported file format for file '{file}'", file=sys.stderr)
            sys.exit(1)
    
    combined_data.sort
    print(json.dumps(combined_data, indent=2))

if __name__ == "__main__":
    main()