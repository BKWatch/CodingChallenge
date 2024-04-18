import argparse
import collections
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET

# Define a named tuple for Address
Address = collections.namedtuple('Address',
                                'name,organization,street,city,county,state,zip')


def parse_xml(filename):
    """
    Parse XML file and extract addresses.

    Args:
        filename (str): Path to the XML file.

    Returns:
        list: List of Address named tuples.
    """
    addresses = []

    tree = ET.parse(filename)
    root = tree.getroot()

    for ent in root.findall('.//ENT'):
        name = ent.find('.//NAME').text.strip() if ent.find('.//NAME') is not None else ''
        organization = ent.find('.//COMPANY').text.strip() if ent.find('.//COMPANY') is not None else ''
        street = ent.find('.//STREET').text.strip()
        city = ent.find('.//CITY').text.strip()
        state = ent.find('.//STATE').text.strip()
        postal_code = ent.find('.//POSTAL_CODE').text.strip()
        zip, zip4 = re.match(r'(\d{5}) ?(-?\d{4})?', postal_code).groups()
        county = ent.find('.//COUNTY')
        county_text = county.text.strip() if county is not None else ''
        addresses.append(Address(name, organization, street, city, county_text, state, zip))

    return addresses


def parse_tsv(filename):
    """
    Parse TSV file and extract addresses.

    Args:
        filename (str): Path to the TSV file.

    Returns:
        list: List of Address named tuples.
    """
    addresses = []

    with open(filename, newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            name = ' '.join([row['first'], row['middle'], row['last']]).strip() if 'first' in row else ''
            organization = row['organization'].strip() if 'organization' in row else ''
            street = row['address'].strip()
            city = row['city'].strip()
            state = row['state'].strip()
            zip = row['zip'].strip()
            zip4 = row['zip4'].strip() if 'zip4' in row else ''
            county = row['county'].strip() if 'county' in row else ''

            if name and organization:
                # Check if the last column contains LLC, Inc, or Ltd, indicating an organization
                if 'LLC' in row['last'] or 'Inc' in row['last'] or 'Ltd' in row['last']:
                    organization = row['last'].strip()
                    name = ''
                else:
                    organization = ''
            elif not name:
                del row['first']
                del row['middle']
                del row['last']
            elif not organization:
                del row['organization']

            addresses.append(Address(name, organization, street, city, county, state, zip))

    return addresses


def parse_txt(filename):
    """
    Parse TXT file and extract addresses.

    Args:
        filename (str): Path to the TXT file.

    Returns:
        list: List of Address named tuples.
    """
    addresses = []

    with open(filename) as f:
        lines = f.readlines()

        i = 0
        while i < len(lines):
            # Skip empty lines or lines starting with '#'
            if not lines[i].strip() or lines[i].startswith('#'):
                i += 1
                continue

            # Extract name
            name = lines[i].strip()
            i += 1

            # Extract street address
            street = lines[i].strip()
            i += 1

            # Extract county (if present)
            county_match = re.match(r'^([A-Z ]+?) COUNTY$', lines[i].strip())
            if county_match:
                county = county_match.group(1).strip()
                i += 1
            else:
                county = ''

            # Extract city, state, and zip code
            if i < len(lines) and ',' in lines[i]:
                city_state_zip = lines[i].strip().split(',')
                city = city_state_zip[0].strip()
                state_zip = city_state_zip[1].strip().rsplit(' ', 1)
                if len(state_zip) >= 2:
                    state = state_zip[0].strip()
                    zip_code = state_zip[1].strip().rstrip('-')  # Remove dash from zip code
                else:
                    state = state_zip[0].strip()
                    zip_code = ''
                i += 1
            else:
                city = ''
                state = ''
                zip_code = ''

            addresses.append(Address(name, '', street, city, county, state, zip_code))

    return addresses


def main():
    """
    Main function to parse address files and output JSON.
    """
    UI = argparse.ArgumentParser(description='Parse address files and output JSON')
    UI.add_argument('filenames', metavar='filename', type=str, nargs='+',
                    help='filename to parse, extension determines format (XML, TSV, TXT)')
    UI.add_argument('--helpreject', action='store_true', help='show this help message and exit')

    Args = UI.parse_args()

    if Args.helpreject:
        UI.print_help()
        sys.exit(0)

    addresses = []
    for filename in Args.filenames:
        ext = filename.split('.')[-1]
        if ext == 'xml':
            addresses += parse_xml(filename)
        elif ext == 'tsv':
            addresses += parse_tsv(filename)
        elif ext == 'txt':
            addresses += parse_txt(filename)
        else:
            sys.stderr.write(f'Error: Unknown file format for {filename}\n')
            sys.exit(1)

    # Convert Address objects to dictionaries
    addresses_dict = []
    for address in addresses:
        address_dict = address._asdict()
        if address_dict['name'] and address_dict['organization']:
            address_dict['organization'] = ''
        elif not address_dict['name']:
            del address_dict['name']
        elif not address_dict['organization']:
            del address_dict['organization']
        addresses_dict.append(address_dict)

    # Sort addresses by zip code and state
    addresses_sorted = sorted(addresses_dict, key=lambda x: (x['zip'], x['state']))

    json_str = json.dumps(addresses_sorted, indent=2)
    print(json_str)


if __name__ == "__main__":
    main()
