import os
import xml.etree.ElementTree as eleTree
import csv
import json
import argparse
from operator import itemgetter

"""
This program, challenge.py, accepts a list of file pathnames containing US names and addresses and combines them into a
JSON-encoded list.

The program assumes that the format of each file corresponds to its extension (xml, tsv, or txt). It parses each file 
and writes a JSON-encoded list of the combined addresses to standard output, sorted by ZIP code in ascending order.
The output is a pretty-printed JSON array of JSON objects, each having the following properties, serialized in the
given order:

- name: The person's full name, if present, consisting of one or more given names followed by the family name.
- organization: The company or organization name, if present.
- street: The street address, often just a house number followed by a direction indicator and a street name.
- city: The city name.
- county: The county name, if present.
- state: The US state name or abbreviation.
- zip: The ZIP code or ZIP+4, in the format 00000 or 00000-0000.

The program assumes that a personal name or organization name will always be present, but not both.

To run the program, provide a list of file pathnames as command line arguments.

Example:
    python challenge.py path_to_input1.xml path_to_input2.tsv path_to_input3.txt
    
@author Ashwin Sharan (ashwinsharan158@gmail.com)
"""


def parse_xml_to_json(xml_file):
    """
    Gets addresses for the XML file and puts the address field in a dictionary and
    adds each dictionary into a list, returning the list.

    :param xml_file: Location of the XML file.
    :return: list of addresses in dictionaries.
    """
    with open(xml_file, 'rb') as f:
        first_line = f.readline().decode('latin-1')
        # Check if the XML declaration specifies Latin-1 encoding.
        if '<?xml' in first_line and 'encoding=\'Latin-1\'' not in first_line:
            raise ValueError(f"File '{xml_file}' does not use Latin-1 encoding.")
        xml_data = f.read().decode('latin-1')
    root = eleTree.fromstring(xml_data)
    entities = []
    # Gets all address entries from the XML file.
    for ent in root.findall('.//ENT'):
        entity = {}
        for child in ent:
            if child.tag == 'NAME' and not child.text == " " and child.text:
                entity['name'] = child.text
            elif child.tag == 'COMPANY' and not child.text == " " and child.text:
                entity['organization'] = child.text
            elif child.tag in ['STREET', 'CITY', 'STATE']:
                # Makes sure each entry has the 3 compulsory fields.
                if not child.text == " " and child.text:
                    entity[child.tag.lower()] = child.text
                else:
                    raise ValueError(f"Parsing issue data missing fields of {xml_file}")
            elif child.tag == 'POSTAL_CODE':
                # Makes sure the zipcode is present with no extra spaces.
                if not child.text == " " and child.text:
                    entity['zip'] = child.text.replace(' ', '')
                else:
                    raise ValueError(f"Parsing issue data missing fields of {xml_file}")
        # Making sure there is a minimum of 5 field in the address.
        if len(entity.keys()) < 5:
            raise ValueError(f"Parsing issue data missing fields of {xml_file}")
        entities.append(entity)
    return entities


def parse_tsv_to_json(tsv_file):
    """
    Gets addresses for the XML file and puts the address field in a dictionary and
    adds each dictionary into a list, returning the list.

    :param tsv_file: Location of the TSV file.
    :return: list of addresses in dictionaries.
    """
    data = []
    with open(tsv_file, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        header = None
        for row in reader:
            if not header:
                header = reader
                continue
            if not row:
                continue
            # When the first name is absent it is an organization.
            if not row[0]:
                # When the organization field is empty it is usually listed in the field for last name .
                if row[3] == 'N/A':
                    # In case there is no last name.
                    if not row[2]:
                        raise ValueError(f"Parsing issue data missing fields of {tsv_file}")
                    # In case there is a middle name and a last name.
                    if row[2] and row[1] and not row[1] == 'N/M/N':
                        raise ValueError(f"Parsing issue data missing fields of {tsv_file}")
                    entry = {"organization": row[2]}
                else:
                    if not row[3]:
                        raise ValueError(f"Parsing issue data missing fields of {tsv_file}")
                    entry = {"organization": row[3]}
            else:
                # In case there is no middle name.
                if not row[1] or row[1] == 'N/M/N':
                    if not row[0] or not row[2]:
                        raise ValueError(f"Parsing issue data missing fields of {tsv_file}")
                    entry = {"name": f"{row[0]} {row[2]}"}
                else:
                    if not row[0] or not row[2]:
                        raise ValueError(f"Parsing issue data missing fields of {tsv_file}")
                    entry = {
                        "name": f"{row[0]} {row[1]} {row[2]}"}
            # Making street, city and state fields are present.
            if row[4] and row[5] and row[6]:
                entry["street"] = row[4]
                entry["city"] = row[5]
                if row[7]:
                    entry["county"] = row[7]
                entry["state"] = row[6]
            else:
                raise ValueError(f"Parsing issue data missing fields of {tsv_file}")
            # Making sure there is a zipcode.
            if row[8] and row[9]:
                entry["zip"] = row[8] + '-' + row[9]
            elif row[8]:
                entry["zip"] = row[8]
            else:
                raise ValueError(f"Parsing issue data missing fields of {tsv_file}")
            # Making sure there is a minimum of 5 field in the address.
            if len(entry.keys()) < 5:
                raise ValueError(f"Parsing issue data missing fields of {tsv_file}")
            data.append(entry)
        return data


def parse_txt_to_json(txt_file):
    """
    Gets addresses for the txt file and puts the address field in a dictionary and
    adds each dictionary into a list, returning the list.

    :param txt_file: Location of the txt file.
    :return: list of addresses in dictionaries.
    """
    with open(txt_file, "r") as fp:
        data = fp.read()
    entries = data.strip().split("\n\n")
    entities = []
    for entry in entries:
        county = None
        lines = entry.strip().splitlines()
        # Makes sure the address have 3-4 lines.
        if len(lines) < 3 or len(lines) > 4:
            raise ValueError(f"Parsing issue data missing fields of {txt_file}")
        name = lines[0].strip()
        street = lines[1].strip()
        # Check for a presence of county name.
        if lines[2].isupper():
            county_line = lines[2].strip().split(" ")
            county = county_line[0]
        # Checking for a city name after the comma.
        address = lines[-1].split(",")
        if len(address) > 2:
            raise ValueError(f"Parsing issue data missing fields of {txt_file}")
        city = address[0].strip()
        temp = address[-1].strip().split(" ")
        # Making sure a zipcode and a state is present.
        if len(temp) < 2:
            raise ValueError(f"Parsing issue data missing fields of {txt_file}")
        zip_code = temp[-1]
        state = " ".join(temp[:-1])
        entity = {"name": name, "street": street, "city": city}
        if county:
            entity["county"] = county
        entity["state"] = state
        entity["zip"] = zip_code
        entities.append(entity)
    return entities


def parse_file(filename):
    """
    To choose the correct method for extracting addresses depending on the file type.

    :param filename: file path
    :return: list of addresses in dictionaries.
    """
    extension = filename.split('.')[-1].lower()
    if extension == 'xml':
        return parse_xml_to_json(filename)
    elif extension == 'tsv':
        return parse_tsv_to_json(filename)
    elif extension == 'txt':
        return parse_txt_to_json(filename)
    else:
        raise ValueError(f"Unsupported file format: {filename}")


def is_empty_file(file_path):
    """
    To check if the file path is valid or the file is empty.

    :param file_path: File path
    """
    if not os.path.isfile(file_path):
        raise ValueError(f"File invalid file path: {file_path}")
    if os.stat(file_path).st_size == 0:
        raise ValueError(f"File is empty: {file_path}")


def main():
    """
    This is the main method, it is responsible for retrieving the file path's from the user and creates a json dump.
    """
    parser = argparse.ArgumentParser(
        description="This program parse address from file in .txt, .tsv and xml formats, then output a JSON containing"
                    " the addresses in ascending order of the zip codes. Example: challenge.py input/input1.xml "
                    "input/input2.tsv input/input3.txt ")
    parser.add_argument("filenames", nargs="+", type=str, help="Paths to files containing addresses")
    args = parser.parse_args()
    addresses = []
    for filename in args.filenames:
        is_empty_file(filename)
        addresses.extend(parse_file(filename))

    addresses.sort(key=itemgetter("zip"))
    print(json.dumps(addresses, indent=2))


if __name__ == "__main__":

    try:
        main()
        exit(0)
    except SystemExit:
        exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
