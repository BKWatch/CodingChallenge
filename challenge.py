# -*- coding: utf-8 -*-
"""challenge.ipynb"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
import csv


def parse_xml(xml_file):
    """
    Parses an XML file and extracts address information.

    Args:
        xml_file (str): Path to the XML file.

    Returns:
        list: List of dictionaries containing address information.
    """
    with open(xml_file, 'r') as f:
        data = f.read()
        root = ET.fromstring(data)
        addresses = []
        # Extract relevant information from each row
        for ent in root.findall(".//ENT"):
            address = {}
            name = ent.find("NAME").text.strip()
            company = ent.find("COMPANY").text.strip()
            street = ent.find("STREET").text.strip()
            city = ent.find("CITY").text.strip()
            state = ent.find("STATE").text.strip()
            zip_code = ent.find("POSTAL_CODE").text.strip().split()[0]

            # Populate address dictionary
            if name:
                address["name"] = name
            else:
                address["organization"] = company
        
            address["street"] = street
            address["city"] = city
            address["state"] = state
            address["zip"] = zip_code

            addresses.append(address)

    return addresses


def parse_tsv(tsv_file):
    """
    Parses a TSV file and extracts address information.

    Args:
        tsv_file (str): Path to the TSV file.

    Returns:
        list: List of dictionaries containing address information.
    """
    addresses = []
    with open(tsv_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            # Extract relevant information from each row
            address = {}
            first = row.get('first', '').strip()
            middle = row.get('middle', '').strip()
            last = row.get('last', '').strip()
            organization = row.get('organization', '').strip()
            street = row.get('address', '').strip()
            city = row.get('city', '').strip()
            county = row.get('county', '').strip()
            state = row.get('state', '').strip()
            zip_code = row.get('zip', '').strip()

            # Populate address dictionary
            if last[-3:] == 'LLC' or last[-4:] == 'Inc.' or last[-4:] == 'Ltd.':
                address["organization"] = last
            elif organization != 'N/A':
                address["organization"] = organization
            elif middle == 'N/M/N':
                address["name"] = f"{first} {last}"
            else:
                address["name"] = f"{first} {middle} {last}"

            # Populate address dictionary
            address["street"] = street
            address["city"] = city
            if county != '':
                address["county"] = county
            address["state"] = state
            address["zip"] = zip_code

            addresses.append(address)
    return addresses


def parse_txt(txt_file):
    """
    Parses a TXT file and extracts address information.

    Args:
        txt_file (str): Path to the TXT file.

    Returns:
        list: List of dictionaries containing address information.
    """
    addresses = []
    with open(txt_file, 'r', encoding='utf-8') as file:
        # Skip empty lines at the beginning of the file
        lines = file.readlines()
        i = 0
        while lines[i] == '\n':
            i += 1
        lines = lines[i:]
        # Parse address information
        #Line1: Name or Organization
        #Line2: Street
        #Line3: County (optional)
        #Line4/3: City, State, ZIP
        people = []
        person = []
        for line in lines:
            line = line.strip()
            if line == '':
                people.append(person)
                person = []
            else:
                person.append(line)
        # Extract relevant information from each person
        for person in people:
            if person[0][-3:] == 'LLC' or person[0][-4:] == 'Inc.' or person[0][-4:] == 'Ltd.':
                address = {'organization': person[0], 'street': person[1]}
            else:
                address = {'name': person[0], 'street': person[1]}

            #csz stands for city, state, zip which is then split into city, state, zip
            
            if len(person) == 4:
                county = person[2]
                csz = person[3].split(',')
            else:
                csz = person[2].split(',')

            address['city'] = csz[0]
            if county:
                address['county'] = county

            #sz stands for state, zip which is then split into state, zip
            sz = csz[1].split(' ')

            if len(sz) > 3:
                address['state'] = sz[-2] + sz[-3]
            else:
                address['state'] = sz[-2]

            address['zip'] = sz[-1]
            if address['zip'][-1] == '-':
                address['zip'] = address['zip'][:-1]

            addresses.append(address)

    return addresses


def main(files):
    """
    Main function to orchestrate the address parsing process.

    Args:
        files (list): List of input file paths.

    Returns:
        list: List of dictionaries containing address information.
    """
    final_addresses = []
    for file in files:
        if file.endswith('.xml'):
            addresses = parse_xml(file)
        elif file.endswith('.tsv'):
            addresses = parse_tsv(file)
        elif file.endswith('.txt'):
            addresses = parse_txt(file)
        else:
            raise ValueError(f"Unsupported file format: {file}")
        final_addresses.extend(addresses)

    # Sort addresses by ZIP code
    final_addresses.sort(key=lambda x: x["zip"])

    return final_addresses


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BankruptcyWatch Coding Challenge")
    parser.add_argument("files", nargs="+", help="List of input files. example: input1.xml input2.tsv input3.txt")
    args = parser.parse_args()

    try:
        # Main function call
        addresses = main(args.files)

        # Output JSON-encoded list of addresses sorted by ZIP code
        print(json.dumps(addresses, indent=2))

        sys.exit(0)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)