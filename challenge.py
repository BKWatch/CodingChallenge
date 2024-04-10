# Import libraries
from os import path
from xml.etree import ElementTree
import argparse
import csv
import json
import sys


VALID_FILE_EXTENSIONS = ['xml', 'tsv', 'txt']


def get_street(street1: str, street2: str, street3: str) -> str:
    '''
    Combines the values of street1, street2 and street3 to get a single string
    for street.
    '''
    street1 = street1.strip()
    street2 = street2.strip()
    street3 = street3.strip()

    street_parts = [street1, street2, street3]
    return '\n'.join([s for s in street_parts if len(s) > 0])


def get_name(first: str, middle: str, last: str) -> str:
    '''
    Combines first, middle and last name to get the name of the person.
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
    Get name of organization using first name, last name and organization
    values extracted from the file.

    If the organization field is N/A, first name is empty, and the last name
    is not empty, then the last name represents the organization.
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
    Extract city from the variable, strips it, and returns it.

    city_state_zip contains data in the format `City, State ZIP`.
    Examples:
    Staten Island, New York 10314
    Detroit, MI 48235-4519
    '''
    [city_and_state, _] = city_state_zip.rsplit(' ', 1)
    [city, _] = city_and_state.split(',')
    return city.strip()


def get_state(city_state_zip: str) -> str:
    '''
    Extract state from the variable, strips it, and returns it.
    '''
    [city_and_state, _] = city_state_zip.rsplit(' ', 1)
    [_, state] = city_and_state.split(',')
    return state.strip()


def get_zip(city_state_zip: str) -> str:
    '''
    Extract zip code from the variable, formats it to the right format,
    and returns it.
    '''

    [_, zip] = city_state_zip.rsplit(' ', 1)
    return normalize_zip(zip)


def normalize_zip(zip: str) -> str:
    return zip.replace(' ', '').rstrip('-')


def process_xml_file(file_name: str) -> list:
    '''
    Processes an xml file and returns a list of dictionaries.

    Each dictionary contains the address of a person or an organization.
    '''

    addresses = []
    tree = ElementTree.parse(file_name)
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

        # Append dictionary to the list.
        addresses.append(address)

    return addresses


def process_tsv_file(file_name: str) -> list:
    '''
    Process the tsv file and extract relevant data.
    '''

    addresses = []
    # Read the file
    with open(file_name) as file:
        tsv_file = csv.reader(file, delimiter='\t')
        header = True

        for line in tsv_file:
            # Discard the header of the file.
            if header:
                header = False
                continue

            address = {}

            # Process name.
            first = line[0]
            middle = line[1]
            last = line[2]
            name = get_name(first, middle, last)
            if len(name) > 0:
                address['name'] = name

            # Process organization.
            organization = line[3]
            organization = get_organization(organization, first, last)
            if len(organization) > 0:
                address['organization'] = organization
                # If organization is present, then delete the name field from dicationary.
                if 'name' in address:
                    del address['name']

            # Process address and city
            address['street'] = line[4].strip()
            address['city'] = line[5].strip()

            # Process county, if present.
            county = line[7].strip()
            if len(county) > 0:
                address['county'] = county

            # Process state.
            address['state'] = line[6].strip()

            # Process zip code.
            zip = line[8].strip()
            zip4 = line[9].strip()
            if len(zip4) > 0:
                zip = zip + '-' + zip4
            address['zip'] = zip

            # Append dict to the list.
            addresses.append(address)

    return addresses


def process_txt_file(file_name: str) -> list:
    '''
    Process the text file, and extract relevant data.
    '''

    addresses = []
    new_address = []

    # Read the file.
    with open(file_name, 'r') as file:
        lines = file.readlines()
        for line in lines:
            # If the line is not empty, adding the data in the line so that it could be processed.
            if line.strip() != '':
                new_address.append(line)
                continue

            # Process all the data upto this new blank line.
            if len(new_address) > 0:
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

                # Add dictionary to the list.
                addresses.append(address)
            new_address = []

    return addresses


def exit_with_error(msg: str) -> None:
    sys.stderr.write(msg)
    sys.exit(1)


def main():
    # Get input file names using the command line
    parser = argparse.ArgumentParser(
        description='Process input files, and extract address of the user/organization.')
    parser.add_argument(
        'files',
        nargs='+',
        help='Name of all the files to parse, separated by space.')
    args = parser.parse_args()

    # Handle errors in processing the input files
    cleaned_addresses = []
    for file in args.files:
        if not path.exists(file):
            exit_with_error(f'File {file} does not exist')
        file_extension = file.split('.')[1]
        if file_extension not in VALID_FILE_EXTENSIONS:
            exit_with_error(f'{file_extension} is not a valid file type.')

    # Extract relevant data from all the files
    for file in args.files:
        file_extension = file.split('.')[1]
        try:
            if file_extension == 'xml':
                cleaned_addresses.extend(process_xml_file(file))
            elif file_extension == 'tsv':
                cleaned_addresses.extend(process_tsv_file(file))
            elif file_extension == 'txt':
                cleaned_addresses.extend(process_txt_file(file))
        except Exception:
            exit_with_error(f'Error parsing file {file}')

    # Sort all addresses by zip code
    cleaned_addresses.sort(key=lambda address: address['zip'])

    # Pretty print all the addresses
    print(json.dumps(cleaned_addresses, indent=2))

    # Exit the program
    sys.exit(0)


if __name__ == '__main__':
    main()
