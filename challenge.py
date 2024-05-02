import argparse
import collections
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET

Address = collections.namedtuple('Address', 'name, organization, street, city, county, state, zip')


def parse_xml(filename):
    """
    This function parses an XML file and retrieves addresses using streaming XML parsing.
    Parameters:
    filename (str): The path to the XML file.
    Returns:
    list: A list containing Address named tuples.
    """
    addresses = []

    try:
        # Create an iterator for parsing the XML file incrementally
        context = ET.iterparse(filename, events=('start', 'end'))

        # Variables to store address fields
        name, organization, street, city, county, state, zip_code = '', '', '', '', '', '', ''

        for event, elem in context:
            if event == 'start' and elem.tag == 'ENT':
                # Reset address fields for each new entity
                name, organization, street, city, county, state, zip_code = '', '', '', '', '', '', ''
            elif event == 'end' and elem.tag == 'ENT':
                # Add parsed address to the list
                addresses.append(Address(name, organization, street, city, county, state, zip_code))
            elif event == 'end':
                # Extract address fields
                if elem.tag == 'NAME':
                    name = elem.text.strip() if elem.text else ''
                elif elem.tag == 'COMPANY':
                    organization = elem.text.strip() if elem.text else ''
                elif elem.tag == 'STREET':
                    street = elem.text.strip() if elem.text else ''
                elif elem.tag == 'CITY':
                    city = elem.text.strip() if elem.text else ''
                elif elem.tag == 'STATE':
                    state = elem.text.strip() if elem.text else ''
                elif elem.tag == 'POSTAL_CODE':
                    postal_code = elem.text.strip() if elem.text else ''
                    zip_code, _ = re.match(r'(\d{5}) ?(-?\d{4})?', postal_code).groups()
                elif elem.tag == 'COUNTY':
                    county = elem.text.strip() if elem.text else ''

                # Remove processed element from memory to conserve memory
                elem.clear()

        del context  # Delete the iterator to free up memory

    except (ET.ParseError, AttributeError) as e:
        sys.stderr.write(f'Error parsing XML file {filename}: {str(e)}\n')
        sys.exit(1)

    return addresses

def parse_tsv(filename, chunk_size=10): 
    """
    This function parses a TSV file in batches, extracting addresses.
    Parameters:
    filename (str): The path to the TSV file.
    chunk_size (int): The number of lines to process in each batch.
    Returns:
    list: A list containing Address named tuples.
    """
    addresses = []

    try:
        with open(filename, newline='') as f:
            reader = csv.DictReader(f, delimiter='\t')

            # Process the TSV file in batches
            while True:
                try:
                    # Read a chunk of lines from the TSV file
                    batch = [next(reader) for _ in range(chunk_size)]
                except StopIteration:
                    # No more lines to read, break the loop
                    break

                # Process each line in the batch
                for row in batch:
                    name = ' '.join([row['first'], row['middle'], row['last']]).strip() if 'first' in row else ''
                    organization = row['organization'].strip() if 'organization' in row else ''
                    street = row['address'].strip()
                    city = row['city'].strip()
                    state = row['state'].strip()
                    zip_code = row['zip'].strip()
                    county = row['county'].strip() if 'county' in row else ''

                    if name and organization:
                        # Check if the last column contains LLC, Inc, or Ltd, indicating an organization
                        if any(keyword in row['last'] for keyword in ['LLC', 'Inc', 'Ltd']):
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

                    addresses.append(Address(name, organization, street, city, county, state, zip_code))

    except FileNotFoundError as e:
        sys.stderr.write(f'Error parsing TSV file {filename}: {str(e)}\n')
        sys.exit(1)
    except csv.Error as e:
        sys.stderr.write(f'Error reading TSV file {filename}: {str(e)}\n')
        sys.exit(1)

    return addresses

def parse_txt(filename, batch_size=1000):
    """
    Parse TXT file in batches and extract addresses.
    Args:
        filename (str): Path to the TXT file.
        batch_size (int): Number of lines to process in each batch.
    Returns:
        list: List of Address named tuples.
    """
    addresses = []

    try:
        with open(filename) as f:
            lines = f.readlines()

            i = 0
            while i < len(lines):
                # Process a batch of lines
                batch = lines[i:i+batch_size]
                addresses.extend(parse_txt_batch(batch))
                i += batch_size

    except FileNotFoundError as e:
        sys.stderr.write(f'Error parsing TXT file {filename}: {str(e)}\n')
        sys.exit(1)

    return addresses

def parse_txt_batch(batch):
    """
    This function parses a batch of lines from a TXT file, extracting addresses.
    Parameters:
    batch (list): A list containing lines from the TXT file.
    Returns:
    list: A list containing Address named tuples.
    """
    addresses = []

    i = 0
    while i < len(batch):
        # Skip empty lines or lines starting with '#'
        if not batch[i].strip() or batch[i].startswith('#'):
            i += 1
            continue

        # Extract name
        name = batch[i].strip()
        i += 1

        # Extract street address
        street = batch[i].strip()
        i += 1

        # Extract county (if present)
        county_match = re.match(r'^([A-Z ]+?) COUNTY$', batch[i].strip())
        if county_match:
            county = county_match.group(1).strip()
            i += 1
        else:
            county = ''

        # Extract city, state, and zip code
        if i < len(batch) and ',' in batch[i]:
            city_state_zip = batch[i].strip().split(',')
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


def parse_addresses(filenames):
    """
    This function parses address files and retrieves addresses.
    Parameters:
    filenames (list): A list of filenames to parse.
    Returns:
    list: A list containing Address named tuples.
    """
    addresses = []

    for filename in filenames:
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

    return addresses


def convert_to_json(addresses):
    """
    This function converts addresses to JSON format.
    Parameters:
    addresses (list): A list containing Address named tuples.
    Returns:
    str: A JSON string representation of addresses.
    """
    addresses_dict = []

    for address in addresses:
        address_dict = address._asdict()
        if address_dict['name'] and address_dict['organization']:
            address_dict['organization'] = ''
        elif not address_dict['name']:
            del address_dict['name']
        elif not address_dict['organization']:
            del address_dict['organization']

        # Remove 'county' key if its value is an empty string
        if address_dict.get('organization') and 'county' in address_dict and not address_dict['county']:
            del address_dict['county']

        addresses_dict.append(address_dict)

    addresses_sorted = sorted(addresses_dict, key=lambda x: (x['zip'], x['state']))
    json_str = json.dumps(addresses_sorted, indent=2)

    return json_str


def main():
    """
    Primary function for parsing address files and generating JSON output.
    """
    parser = argparse.ArgumentParser(description='Parse address files and output JSON')
    parser.add_argument('filenames', metavar='filename', type=str, nargs='+',
                        help='filename to parse, extension determines format (XML, TSV, TXT)')
    parser.add_argument('--helpreject', action='store_true', help='show this help message and exit')

    args = parser.parse_args()

    if args.helpreject:
        parser.print_help()
        sys.exit(0)

    addresses = parse_addresses(args.filenames)
    json_str = convert_to_json(addresses)
    print(json_str)


if __name__ == "__main__":
    main()
