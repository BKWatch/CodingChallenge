
import argparse
import json
from typing import Dict, List
from xml.etree import ElementTree as ET
from csv import reader
from collections import namedtuple
from pandas import DataFrame
import sys
import re

def parse_xml(file_name: str) -> List[Dict]:
    """Parses XML file and returns a list of address dictionaries."""
    addresses_list = []
    tree = ET.parse(file_name)
    root = tree.getroot()
    for ent_element in root.iter(tag='ENT'):
        address_dict = {'name': '', 'organization': '', 'street': '', 'city': '', 'county': '', 'state': '', 'zip': ''}
        for subchild in ent_element.iter():
            
            # name: The person's full name, if present, consisting of a list of one or more given names followed by the family name
            if subchild.tag == 'NAME':
                address_dict['name'] = subchild.text.strip()
            
            # organization: The company or organization name, if present
            if subchild.tag == 'COMPANY':
                address_dict['organization'] = subchild.text.strip()
            
            # street: The street address, often just a house number followed by a direction indicator and a street name
            if subchild.tag == 'STREET':
                address_dict['street'] = subchild.text.strip()
            if subchild.tag == 'STREET_2':
                street2_str = subchild.text.strip()
                if street2_str:
                    address_dict['street'] += ', ' + street2_str
            if subchild.tag == 'STREET_3':
                street3_str = subchild.text.strip()
                if street3_str:
                    address_dict['street'] += ', ' + street3_str
            
            # city: The city name
            if subchild.tag == 'CITY':
                address_dict['city'] = subchild.text.strip()
            
            # county: The county name, if present
            if subchild.tag == 'COUNTY':
                address_dict['county'] = subchild.text.strip()
            
            # state: The US state name or abbreviation
            if subchild.tag == 'STATE':
                address_dict['state'] = subchild.text.strip()
            
            # zip: The ZIP code or ZIP+4, in the format 00000 or 00000-0000
            if subchild.tag == 'POSTAL_CODE':
                address_dict['zip'] = subchild.text.strip()
        
        addresses_list.append(address_dict)
    
    return addresses_list


def parse_tsv(file_name: str) -> List[Dict]:
    """Parses TSV file and returns a list of address dictionaries."""
    addresses_list = []
    with open(file_name, 'r') as file:
        reader_obj = reader(file, delimiter='\t')
        headers = next(reader_obj)
        for row in reader_obj:
            address_dict = dict(zip(headers, row))
            addresses_list.append(address_dict)
    
    # Convert it to a data frame for cleanup
    df = DataFrame(addresses_list)
    
    # Clean up the off-by-one-column error
    mask_series = (df['first'] == '') & (df.middle == '') & (df['last'] != '')
    df.loc[mask_series, 'organization'] = df.loc[mask_series, 'last']
    df.loc[mask_series, 'last'] = ''
    
    # name: The person's full name, if present, consisting of a list of one or more given names followed by the family name
    df['name'] = df.apply(lambda srs: ' '.join([srs['first'], srs.middle, srs['last']]).strip(), axis='columns')
    
    # organization: The company or organization name, if present
    
    # street: The street address, often just a house number followed by a direction indicator and a street name
    df = df.rename(columns={'address': 'street'})
    
    # city: The city name
    
    # county: The county name, if present
    
    # state: The US state name or abbreviation
    
    # zip: The ZIP code or ZIP+4, in the format 00000 or 00000-0000
    df.zip = df.apply(lambda srs: srs.zip + '-' + srs.zip4 if srs.zip4 else srs.zip, axis='columns')
    
    # Convert the properly ordered columns back into a row dictionary list
    columns_list = ['name', 'organization', 'street', 'city', 'county', 'state', 'zip']
    addresses_list = df[columns_list].to_dict('records')
    
    return addresses_list


def parse_txt(file_name: str) -> List[Dict]:
    """Parses TXT file (assuming one address per line) and returns a list of address dictionaries."""
    address_regex = re.compile('\n\n  ([^\r\n]+)\n  ([^\r\n]+)\n  ([^\r\n]+)(?:\n  ([^\r\n]+))?')
    addresses_list = []
    with open(file_name, 'r') as f:
        data_str = f.read()
        for match_obj in address_regex.finditer(data_str):
            full_name = match_obj.group(1)
            street_address = match_obj.group(2)
            county_or_city_state_zip = match_obj.group(3)
            city_state_zip = match_obj.group(4)
            if ('COUNTY' not in county_or_city_state_zip) and ((city_state_zip == '') or (city_state_zip is None)):
                city_state_zip = county_or_city_state_zip
                county_or_city_state_zip = ''
            zip_parts_list = re.split(r'\D+', city_state_zip, 0)
            address_dict = {
                'name': full_name,
                'organization': '',
                'street': street_address,
                'city': city_state_zip.split(',')[0],
                'county': county_or_city_state_zip,
                'state': re.split(r'\d+', city_state_zip.split(',')[1].strip(), 0)[0],
                'zip': '-'.join(zip_parts_list[1:])
            }
            addresses_list.append(address_dict)
    
    return addresses_list


def parse_address_file(file_name: str) -> List[Dict]:
    """Parses a file based on its extension and returns a list of address dictionaries."""
    parsers = {'xml': parse_xml, 'tsv': parse_tsv, 'txt': parse_txt}
    extension = file_name.split('.')[-1].lower()
    if extension not in parsers:
        raise ValueError(f"Unsupported file format: {file_name}")
    
    return parsers[extension](file_name)


def validate_address(address: Dict) -> bool:
    """Checks if required fields (name/organization and ZIP code) are present."""
    
    return ('name' in address or 'organization' in address) and 'zip' in address


def main():
    parser = argparse.ArgumentParser(description="Parse addresses_list from files and output JSON")
    parser.add_argument('files', nargs='+', help="Paths to address files (XML, TSV, TXT)")
    args = parser.parse_args()

    all_addresses = []
    errors = False
    Address = namedtuple('Address', ['name', 'organization', 'street', 'city', 'county', 'state', 'zip'])
    
    for file_name in args.files[0].split('=')[1].split(','):
        try:
            addresses_list = parse_address_file(file_name)
            for address in addresses_list:
                if validate_address(address):
                    
                    # Convert to namedtuple for easier sorting
                    all_addresses.append(Address(**address))
                    
                else:
                    print(f"Error: Invalid address format in {file_name}", file=sys.stderr)
                    errors = True
        except (FileNotFoundError, ValueError) as e:
            print(f"Error processing {file_name}: {e}", file=sys.stderr)
            errors = True

    if errors:
        sys.exit(1)

    # Sort by ZIP code
    sorted_addresses = sorted(all_addresses, key=lambda a: a.zip)

    # Convert back to dictionaries for JSON output
    address_dicts = [a._asdict() for a in sorted_addresses]
    json.dump(address_dicts, sys.stdout, indent=4)

if __name__ == "__main__":
    main()