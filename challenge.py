"""
Script to generate JSON array of addresses from given files

Usage:
    To get help: python challenge.py -h
    To run the program: python challenge.py -f ./input/input1.xml ./input/input2.tsv ./input/input3.txt
"""

import os
import sys
import csv
import json
import argparse
import xml.etree.ElementTree as ET

class AddressParser:

    @staticmethod
    def parse_xml(file_path):
        """Method to parse .xml file

        Args:
            file_path (str): Path to the xml file

        Raises:
            ValueError: Raise error if the formatting is different

        Returns:
            List[Dict]: List of dictionaries of parsed addresses from given xml file
        """
        xml_tree = ET.parse(file_path)
        root = xml_tree.getroot()
        addresses = []
        
        # Loop all entities
        for ent in root.findall('.//ENT'):
            address = {}
            node_address_map = {
                'NAME': 'name',
                'COMPANY': 'organization',
                'STREET': 'street',
                'CITY': 'city',
                'STATE': 'state',
                'POSTAL_CODE': 'zip'
            }
            # Loop all fields
            for node_field, address_key in node_address_map.items():
                node_element = ent.find(node_field)
                if node_element is not None and node_element.text and node_element.text.strip():
                    address[address_key] = node_element.text.strip()
                    if address_key == 'zip':
                        address[address_key] = '-'.join(
                            [
                                el for el in address[address_key].replace(' ', '').split('-') \
                                if el != ''
                            ]
                        )
            if address:
                addresses.append(address)

        return addresses

    @staticmethod
    def parse_tsv(file_path):
        """Method to parse .tsv file

        Args:
            file_path (str): Path to the tsv file

        Raises:
            ValueError: Raise error if the formatting is different

        Returns:
            List[Dict]: List of dictionaries of parsed addresses from given tsv file
        """
        addresses = []
        with open(file_path, 'r') as f:
            content = csv.DictReader(f, delimiter='\t')
            for row in content:
                address = {}
                
                # Handle name
                first_name = row.get('first', '').strip()
                middle_name = row.get('middle', '').strip()
                last_name = row.get('last', '').strip()
                if middle_name != "N/M/N":
                    name = ' '.join([el for el in [first_name, middle_name, last_name] if el])
                else:
                    name = ' '.join([el for el in [first_name, last_name] if el])
                if name:
                    address['name'] = name
                
                # Handle organization
                organization = row.get('organization', '').strip()
                if organization and organization != "N/A":
                    address['organization'] = organization
                
                # Handle address, city, and state
                for field in ['address', 'city', 'county', 'state']:
                    if row.get(field, '').strip():
                        if field == 'address':
                            address['street'] = row[field].strip()
                        else:
                            address[field] = row[field].strip()

                # Handle zip code
                zip_code = row.get('zip', '').strip()
                zip_code4 = row.get('zip4', '').strip()
                if zip_code:
                    if zip_code4:
                        zip_code += '-' + zip_code4
                    address['zip'] = zip_code

                # Append dictionary
                if any(value for value in address.values()):
                    addresses.append(address)

        return addresses

    @staticmethod
    def parse_txt(file_path):
        """Method to parse .txt file

        Args:
            file_path (str): Path to the txt file

        Raises:
            ValueError: Raise error if the formatting is different

        Returns:
            List[Dict]: List of dictionaries of parsed addresses from given txt file
        """
        addresses = []
        with open(file_path, 'r') as f:
            content = f.read().strip().split('\n\n')

        for row in content:
            address = {}
            components = [component.strip() for component in row.split('\n')]

            if len(components) == 4:
                name, street, county, city_state_zip = components
            elif len(components) == 3:
                name, street, city_state_zip = components
                county = None
            else:
                raise ValueError('Unsupported txt address formatting')
            
            # Handle city, state, and zip
            splitted = city_state_zip.strip().split(',')
            city = splitted[0]
            state_zip = ','.join(splitted[1:])

            splitted = state_zip.strip().split(' ')
            state = ' '.join(splitted[:-1])
            zip = splitted[-1]
            if zip.strip().endswith('-') or zip.strip().endswith('- '):
                zip = zip.split('-')[0]

            # Add to dictionary
            address['name'] = name.strip()
            address['street'] = street.strip()
            address['city'] = city.strip()
            if county:
                address['county'] = county.replace('COUNTY', '').strip()
            address['state'] = state.strip()
            address['zip'] = zip.strip()
            
            addresses.append(address)
            
        return addresses

    @staticmethod
    def parse(file_path):
        """Static method to parse addresses from a given file path

        Args:
            file_path (str): Path to the file

        Raises:
            ValueError: Raise error if the file type is not one of the [xml, tsv, txt]

        Returns:
            List[Dict]: List of dictionaries of parsed addresses from the file path
        """
        extension = os.path.splitext(file_path)[-1]
        if extension == ".xml":
            return AddressParser.parse_xml(file_path=file_path)
        elif extension == ".tsv":
            return AddressParser.parse_tsv(file_path=file_path)
        elif extension == ".txt":
            return AddressParser.parse_txt(file_path=file_path)
        else:
            raise TypeError("Unsupported file path.")

def sort_address(addresses):
    """Sorts addresses by ZIP code in ascending order.

    Args:
        addresses (List[Dict]): List of dictionaries of addresses

    Returns:
        addresses (List[Dict]): Sorted list of dictionaries of addresses
    """
    return sorted(addresses, key=lambda x: x['zip'])

def process_files(file_paths):
    """Process addresses from files and output JSON array.

    Args:
        file_paths (List[str]): List of file paths to process
    """
    addresses = []
    for file_path in file_paths:
        address_dict = AddressParser.parse(file_path)
        addresses.extend(address_dict)

    addresses = sort_address(addresses=addresses)
    output = json.dumps(addresses, indent=4)
    print(output)
    with open('output.json', 'w') as f:
        f.write(output)

def validate_files(file_paths):
    """Validate file paths.
    
    The function will check two things:
     1. The existance of the files
     2. The valid extension (xml, tsv, or txt)

    Any fail check resulted in termination with status code 1

    Args:
        file_paths (List[str]): List of file paths
    """
    ACCEPTED_EXT = [".xml", ".tsv", ".txt"]
    for file_path in file_paths:
        if not os.path.isfile(file_path):
            sys.stderr.write(f"Error: File does not exist - {file_path}\n")
            sys.exit(1)

        if os.path.splitext(file_path)[-1].lower() not in ACCEPTED_EXT:
            sys.stderr.write(f"Error: File extension not allowed - {file_path}\n")
            sys.exit(1)

def parse_args():
    """Function to parse user inputs.

    Returns:
        List: List of file paths from the user input.
    """
    parser = argparse.ArgumentParser(
        description='Program to parse addresses from a list of xml, tsv, and txt files'
    )
    parser.add_argument('-f','--files', nargs='+', help='List of file paths', required=True)
    return parser.parse_args()

def main():
    """Entry point for executing the program."""
    try:
        args = parse_args()
        validate_files(args.files)
        process_files(args.files)
    except Exception as e:
        sys.stderr.write(f"Error: {str(e)}\n")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()