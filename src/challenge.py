import argparse
import os
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET


def parse_xml(file: str):
    """
        Parses an XML file containing entity information and returns a list of dictionaries
        with parsed data.

        Args:
            file (str): The path to the XML file to parse.

        Returns:
            list: A list of dictionaries containing parsed entity information.
                  Each dictionary represents one entity with the following keys:
                  - 'name': Name of the entity (if available).
                  - 'organization': Organization/company of the entity (if available).
                  - 'street': Street address of the entity (if available).
                  - 'city': City of the entity (if available).
                  - 'county': County of the entity (if available).
                  - 'state': State of the entity (if available).
                  - 'zip': Postal code of the entity (if available).

        Example:
            XML structure:
            <ENTITY>
                <ENT>
                    <NAME>John Doe</NAME>
                    <COMPANY>ABC Inc</COMPANY>
                    <STREET>123 Main St</STREET>
                    <CITY>Anytown</CITY>
                    <STATE>California</STATE>
                    <POSTAL_CODE>12345</POSTAL_CODE>
                </ENT>
                <ENT>
                    ...
                </ENT>
                ...
            </ENTITY>

            Resulting output:
            [
                {
                    'name': 'John Doe',
                    'organization': 'ABC Inc',
                    'street': '123 Main St',
                    'city': 'Anytown',
                    'state': 'California',
                    'zip': '12345'
                },
                ...
            ]
        """
    result = []
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        if root.find('ENTITY'):
            for ent in root.find('ENTITY').findall('ENT'):
                row = {}
                if ent.find('NAME') is not None:
                    name = ent.find('NAME').text.strip()
                    if name:
                        row['name'] = name
                if ent.find('COMPANY') is not None:
                    company = ent.find('COMPANY').text.strip()
                    if company:
                        row['organization'] = company
                street = []
                if ent.find('STREET') is not None:
                    street0 = ent.find('STREET').text.strip()
                    if street0:
                        street.append(street0)
                if ent.find('STREET1') is not None:
                    street1 = ent.find('STREET1').text.strip()
                    if street1:
                        street.append(street1)
                if ent.find('STREET2') is not None:
                    street2 = ent.find('STREET2').text.strip()
                    if street2:
                        street.append(street2)
                if street:
                    row['street'] = ', '.join(street)
                if ent.find('CITY') is not None:
                    city = ent.find('CITY').text.strip()
                    if city:
                        row['city'] = city
                if ent.find('COUNTY') is not None:
                    county = ent.find('COUNTY').text.strip()
                    if county:
                        row['county'] = county
                if ent.find('STATE') is not None:
                    state = ent.find('STATE').text.strip()
                    if state:
                        row['state'] = state
                if ent.find('POSTAL_CODE') is not None:
                    code = ent.find('POSTAL_CODE').text.strip()
                    if code:
                        row['zip'] = code

                result.append(row)
    except ET.ParseError as e:
        err = f"Error: parse exception while parsing '{file}': {e}."
        sys.stderr.write(err + "\n")
        sys.exit(1)

    return result


def parse_txt(file: str):
    """
        Parses a text file containing address information and returns a list of dictionaries
        with parsed data.

        Args:
            file (str): The path to the text file to parse.

        Returns:
            list: A list of dictionaries containing parsed address information.
                  Each dictionary represents an address with the following keys:
                  - 'name': Name associated with the address.
                  - 'street': Street address.
                  - 'city': City.
                  - 'county': County (if available).
                  - 'state': State.
                  - 'zip': Zip code.

        Example:
            Text file content:
            David Scherrep
            12014 Cobblewood Lane North
            DUVAL COUNTY
            Jacksonville, Florida 32225

            Sonji S Dixon-McCoy
            1222 East 146th Street
            Dolton, Illinois 60419-

            Resulting output:
            [
                {
                    'name': 'David Scherrep',
                    'street': '12014 Cobblewood Lane North',
                    'county': 'DUVAL COUNTY',
                    'city': 'Jacksonville',
                    'state': 'Florida',
                    'zip': '32225'
                },
                {
                    'name': 'Sonji S Dixon-McCoy',
                    'street': '1222 East 146th Street',
                    'city': 'Dolton',
                    'state': 'Illinois',
                    'zip': '60419-'
                }
            ]
    """
    json_output = []
    try:
        with open(file, 'r', encoding='utf-8') as f:
            row = {}
            for line in f:
                line = line.strip()
                if line:
                    if 'name' not in row:
                        row['name'] = line.strip()
                    elif 'street' not in row:
                        row['street'] = line.strip()
                    elif 'county' not in row and 'county' in line.lower():
                        county = line.strip().split("//s+")[0]
                    elif 'state' not in row:
                        parts = re.split(r'\s+', line.strip())
                        row['city'] = parts[0][:-1]
                        if county: row['county'] = county
                        row['state'] = parts[1]
                        row['zip'] = parts[2]
                else:
                    if row:
                        json_output.append(row)
                        row = {}
    except Exception as e:
        err = f"Error: parse exception while parsing '{file}': '{e}."
        sys.stderr.write(err + "\n")
        sys.exit(1)

    return json_output


def parse_tsv(file: str):
    """
        Parses a TSV (Tab-Separated Values) file containing address information and
        returns a list of dictionaries with parsed data.

        Args:
            file (str): The path to the TSV file to parse.

        Returns:
            list: A list of dictionaries containing parsed address information.
                  Each dictionary represents an address with the following keys:
                  - 'name': Name associated with the address.
                  - 'organization': Organization/company associated with the address.
                  - 'street': Street address.
                  - 'city': City.
                  - 'county': County.
                  - 'state': State.
                  - 'zip': Zip code.

        Example:
            TSV file content:
            first	middle	last	organization	address	city	county	state	zip	zip4
            John		Doe	ABC Inc	123 Main St	Anytown	Any County	CA	12345	6789
            Jane		Smith	XYZ Co	456 Elm St	Sometown	Another County	NY	54321

            Resulting output:
            [
                {
                    'name': 'John Doe',
                    'organization': 'ABC Inc',
                    'street': '123 Main St',
                    'city': 'Anytown',
                    'county': 'Any County',
                    'state': 'CA',
                    'zip': '12345',
                    'zip4': '6789'
                },
                {
                    'name': 'Jane Smith',
                    'organization': 'XYZ Co',
                    'street': '456 Elm St',
                    'city': 'Sometown',
                    'county': 'Another County',
                    'state': 'NY',
                    'zip': '54321',
                    'zip4': ''
                }
            ]
    """
    json_output = []
    try:
        with open(file, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for curr in reader:
                row = {}
                # parse name
                name = ''
                if 'first' in curr:
                    name += curr['first']
                if 'middle' in curr:
                    name = name + " " + curr['middle']
                if 'last' in curr:
                    name = name + " " + curr['last']
                if name.strip():
                    row['name'] = name.strip()
                # parse org
                org = ''
                if 'organization' in curr and curr['organization'] != 'N/A':
                    name += curr['organization']
                if org.strip():
                    row['organization'] = org.strip()
                # parse address
                if 'address' in curr and curr['address'].strip():
                    row['street'] = curr['address'].strip()
                # parse city
                if 'city' in curr and curr['city'].strip():
                    row['city'] = curr['city'].strip()
                # parse county
                if 'county' in curr and curr['county'].strip():
                    row['county'] = curr['county'].strip()
                # parse state
                if 'state' in curr and curr['state'].strip():
                    row['state'] = curr['state'].strip()
                # parse zip
                zip_add = ''
                if 'zip' in curr and curr['zip'].strip():
                    zip_add = curr['zip'].strip()
                if 'zip4' in curr and curr['zip4'].strip():
                    zip_add = curr['zip4'].strip()
                if zip_add.strip():
                    row['zip'] = zip_add.strip()
                json_output.append(row)
    except Exception as e:
        err = f"Error: parse exception while parsing '{file}': '{e}."
        sys.stderr.write(err + "\n")
        sys.exit(1)

    return json_output


def parse(file: str):
    file_type = file.split(".")[-1]

    if file_type == 'tsv':
        return parse_tsv(file)
    elif file_type == 'txt':
        return parse_txt(file)
    elif file_type == 'xml':
        return parse_xml(file)


# read filenames
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse tsv, txt and xml files and extract addresses')
    parser.add_argument('files', metavar='SOURCE_FILE', type=str, nargs='+', help='file path to process')
    args = parser.parse_args()

    file_names = args.files
    if not file_names:
        print("Missing required parameter filenames")
    else:
        output_file = 'output/output.json'
        output_json = []
        for file_name in file_names:
            if not os.path.exists(file_name):
                error_message = f"Error: File '{file_name}' does not exist or is not accessible."
                sys.stderr.write(error_message + "\n")
                sys.exit(1)

        for file_name in file_names:
            output_json += parse(file_name)

        with open(output_file, 'w') as json_file:
            json.dump(output_json, json_file, indent=4)
    sys.exit(0)
