# Import libraries
from os import path
from xml.etree import ElementTree
import argparse
import csv
import json
import sys
import re


VALID_FILE_EXTENSIONS = ['xml', 'tsv', 'txt']
REQUIRED_ADDRESS_FIELDS = ['street', 'city', 'state', 'zip']
XML_TAGS = ['ENTITY', 'ENT', 'NAME', 'COMPANY', 'STREET', 'STREET_2', 'STREET_3', 'CITY', 'STATE', 'POSTAL_CODE', 'COUNTRY']
TSV_COLUMNS = ['first', 'middle', 'last', 'organization', 'address', 'city', 'state', 'county', 'zip', 'zip4']


def get_street(street1: str, street2: str, street3: str) -> str:
    '''
    Get full street address {street1 street2 street3}.
    '''
    street1 = street1.strip()
    street2 = street2.strip()
    street3 = street3.strip()

    street_parts = [street1, street2, street3]
    return '\n'.join([s for s in street_parts if len(s) > 0])


def get_name(first: str, middle: str, last: str) -> str:
    '''
    Get persons full name {first middel last}.
    '''
    first = first.strip()
    middle = middle.strip()
    last = last.strip()

    if middle == 'N/M/N':
        middle = ''

    name_parts = [first, middle, last]
    return ' '.join([s for s in name_parts if len(s) > 0])


def get_organization(organization: str, first: str, last: str) -> str:
    '''
    Get name of organization using first name, last name and organization.
    If the organization field is N/A, first name is empty, and the last name is not empty, then the last name represents the organization.
    '''
    organization = organization.strip()

    if organization != 'N/A' and len(organization) != 0:
        return organization
    elif len(first) == 0 and len(last) > 0:
        return last
    else:
        return ''


def get_city(city_state_zip: str) -> str:
    '''
    Get city from {city, state zip}.
    '''
    [city_and_state, _] = city_state_zip.rsplit(' ', 1)
    [city, _] = city_and_state.split(',')
    return city.strip()


def get_state(city_state_zip: str) -> str:
    '''
    Get state from {city, state zip}.
    '''
    [city_and_state, _] = city_state_zip.rsplit(' ', 1)
    [_, state] = city_and_state.split(',')
    return state.strip()


def get_zip(city_state_zip: str) -> str:
    '''
    Get zip from {city, state zip} and format.
    '''

    [_, zip] = city_state_zip.rsplit(' ', 1)
    return normalize_zip(zip)


def normalize_zip(zip: str) -> str:
    return zip.replace(' ', '').rstrip('-')


def validate_zip(zip: str) -> bool:
    '''
    Validate zip either 00000 or 00000-0000.
    '''
    zip_pattern = re.compile(r'^[0-9]{5}(?:-[0-9]{4})?$')
    if not re.match(zip_pattern, zip):
        exit_with_error('Zip not in right format')
    return True


def validate_address(address: dict) -> bool:
    '''
    Validate all the fields in the address.
    '''
    if 'name' not in address and 'organization' not in address:
        # At least one of name or organization is required.
        return False

    for field in REQUIRED_ADDRESS_FIELDS:
        if field not in address or len(address[field]) == 0:
            return False

    return validate_zip(address['zip'])


def validate_xml_tags(tree: ElementTree) -> bool:
    '''
    Vaildate xml tags of xml file
    '''
    tags = list({elem.tag for elem in tree.iter()})
    for tag in XML_TAGS:
        if tag not in tags:
            return False
    return True


def validate_tsv_columns(header: list[str], column_to_index_map: dict) -> bool:
    '''
    Vaildate tsv columns of tsv file
    '''
    if len(header) == 0:
        return False
    if len(header) < len(TSV_COLUMNS):
        return False
    else:
        for index, column in enumerate(header):
            if column not in TSV_COLUMNS:
                return False
            column_to_index_map[column] = index
    return True


def process_xml_file(file_name: str) -> list:
    '''
    Process xml file and returns a list of dictionaries.
    Each dictionary contains the address of a person or an organization.
    '''

    addresses = []
    tree = ElementTree.parse(file_name)
    if not validate_xml_tags(tree):
        exit_with_error(f'Tags not matching in file {file_name}')
    root = tree.getroot()
    for entity in root.findall('ENTITY/ENT'):
        def get_node_value(name: str) -> str:
            value = entity.find(name)
            if value is None:
                return ''
            return value.text.strip()

        address = {}

        # Extract name.
        name = get_node_value('NAME')
        if len(name) > 0:
            address['name'] = name

        # Extract organization.
        organization = get_node_value('COMPANY')
        if len(organization) > 0:
            address['organization'] = organization
            # If organization is present, then delete the name field because
            # each dict represents either an organization or a person.
            if 'name' in address:
                del address['name']

        # Extract street.
        street = get_node_value('STREET')
        street2 = get_node_value('STREET_2')
        street3 = get_node_value('STREET_3')
        address['street'] = get_street(street, street2, street3)

        # Extract city.
        address['city'] = get_node_value('CITY')

        # Extract county, if present.
        county = get_node_value('COUNTY')
        if len(county) > 0:
            address['county'] = county

        # Extract state.
        address['state'] = get_node_value('STATE')

        # Extract zip.
        zip = get_node_value('POSTAL_CODE')
        address['zip'] = normalize_zip(zip)

        if validate_address(address):
            # Append dictionary to the list.
            addresses.append(address)
        else:
            exit_with_error(f'Invalid address in file {file_name}')
    return addresses


def process_tsv_file(file_name: str) -> list:
    '''
    Process the tsv file.
    '''

    addresses = []
    column_to_index_map = {}
    # Read the file.
    with open(file_name) as file:
        tsv_file = csv.reader(file, delimiter='\t')
        header = True

        for line in tsv_file:
            if header:
                if validate_tsv_columns(line, column_to_index_map):
                    header = False
                    continue
                else:
                    exit_with_error(f'Column mismatch in {file_name}')

            address = {}

            # Process name.
            first = line[column_to_index_map['first']]
            middle = line[column_to_index_map['middle']]
            last = line[column_to_index_map['last']]
            name = get_name(first, middle, last)
            if len(name) > 0:
                address['name'] = name

            # Process organization.
            organization = line[column_to_index_map['organization']]
            organization = get_organization(organization, first, last)
            if len(organization) > 0:
                address['organization'] = organization
                # If organization is present, then delete the name field from dictionary.
                if 'name' in address:
                    del address['name']

            # Process address and city.
            address['street'] = line[column_to_index_map['address']].strip()
            address['city'] = line[column_to_index_map['city']].strip()

            # Process county, if present.
            county = line[column_to_index_map.get('county', '')].strip()
            if len(county) > 0:
                address['county'] = county

            # Process state.
            address['state'] = line[column_to_index_map['state']].strip()

            # Process zip code.
            zip = line[column_to_index_map['zip']].strip()
            zip4 = line[column_to_index_map.get('zip4', '')].strip()
            if len(zip4) > 0:
                zip = zip + '-' + zip4
            address['zip'] = zip

            if validate_address(address):
                # Append dictionary to the list.
                addresses.append(address)
            else:
                exit_with_error(f'Invalid address in file {file_name}')

    return addresses


def process_txt_file(file_name: str) -> list:
    '''
    Process text file.
    '''

    addresses = []
    new_address = []

    # Read the file.
    with open(file_name, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if line.strip() != '':
                new_address.append(line)
                continue
            if len(new_address) > 0:
                if len(new_address) < 3:
                    exit_with_error(f'Missing fields in file {file_name}')
                address = {}
                address['name'] = new_address[0].strip()
                address['street'] = new_address[1].strip()
                # Add county field if there are more than 3 lines to be processed.
                if len(new_address) > 3:
                    city_state_zip = new_address[3].strip()
                    address['city'] = get_city(city_state_zip)
                    address['county'] = new_address[2].strip()
                    address['state'] = get_state(city_state_zip)
                    address['zip'] = get_zip(city_state_zip)
                else:
                    city_state_zip = new_address[2].strip()
                    address['city'] = get_city(city_state_zip)
                    address['state'] = get_state(city_state_zip)
                    address['zip'] = get_zip(city_state_zip)

                if validate_address(address):
                    # Append dictionary to the list.
                    addresses.append(address)
                else:
                    exit_with_error(f'Invalid address in file {file_name}')
            new_address = []

    return addresses


def exit_with_error(msg: str) -> None:
    sys.stderr.write('Error: ' + msg + '\n')
    sys.exit(1)


def main():
    # Get input file names using the command line.
    parser = argparse.ArgumentParser(description='Process input files, and extract address of the user/organization.')
    parser.add_argument('files', nargs='+', help='Name of all the files to parse, separated by space.')
    args = parser.parse_args()

    cleaned_addresses = []
    for file in args.files:
        # Handle errors in processing the input files
        if not path.exists(file):
            exit_with_error(f'File {file} does not exist')
        file_extension = file.split('.')[1]
        if file_extension not in VALID_FILE_EXTENSIONS:
            exit_with_error(f'{file_extension} is not a valid file type.')
        else:
            try:
                if file_extension == 'xml':
                    cleaned_addresses.extend(process_xml_file(file))
                elif file_extension == 'tsv':
                    cleaned_addresses.extend(process_tsv_file(file))
                elif file_extension == 'txt':
                    cleaned_addresses.extend(process_txt_file(file))
            except Exception:
                exit_with_error(f'Error parsing file {file}')

    # Sort all addresses by zip code.
    cleaned_addresses.sort(key=lambda address: address['zip'])

    # Print all addresses.
    print(json.dumps(cleaned_addresses, indent=2))

    # Exit the program.
    sys.exit(0)


if __name__ == '__main__':
    main()
