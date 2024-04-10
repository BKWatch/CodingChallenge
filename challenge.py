'''
    challenge.py is a command line base application that takes in xml, tsv, txt file and print out a pretty version of the json format sorted by zip code.
    written by Titus Cheng
'''
import sys
import os
import json
import csv
import re
import xml.etree.ElementTree as ET
import argparse

# a list of all us state abbreviated
state_abbreviations = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
}

# a list of all us states
us_states = {
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'Florida',
    'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine',
    'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska',
    'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio',
    'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas',
    'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'
}

# Field class is used to map tags in an xml file to the corresponding fields in json
class Field:
    def __init__(self, tag, name):
        self.tag = tag
        self.name = name

class Name:
    def __init__(self, first, middle, last):
        self._first = first
        self._middle = middle
        self._last = last

    @classmethod
    def from_string(cls, string):
        components = string.split(" ")
        if len(components) == 3:
            return cls(components[0], components[1], components[2])
        elif len(components) == 2:
            return cls(components[0], components[1], "")
        else:
            return cls(string, "", "")

    def has_content(self):
        return len(self._first) > 0 and len(self._middle) > 0 and len(self._last) > 0

    def _sanitize(self, text):
        return text.strip()

    def _is_valid(self, text):
        return False if "/" in text else True

    def string(self):
        name = []
        if self._is_valid(self._first):
            name.append(self._sanitize(self._first))
        if self._is_valid(self._middle):
            name.append(self._sanitize(self._middle))
        if self._is_valid(self._last):
            name.append(self._sanitize(self._last))
        return " ".join(name).strip()

class Company:
    def __init__(self, company):
        self._company = company

    def string(self):
        return self._company

class Organization:
    def __init__(self, organization):
        self._organization = organization

    def string(self):
        return self._organization

class Street:
    def __init__(self, street):
        self._street = street

    def string(self):
        return self._street

class City:
    def __init__(self, city):
        self._city = city

    def _sanitize(self, text):
        if "," in text:
            return text.replace(",", "")
        return text

    def string(self):
        return self._sanitize(self._city)

class County:
    def __init__(self, county):
        self._county = county

    def string(self):
        return self._county

class State:
    def __init__(self, state):
        self._state = state

    def _sanitize(self, text):
        return text.strip()

    def string(self):
        return self._sanitize(self._state)

class Zip:
    def __init__(self, zip):
        self._zip = zip

    def _sanitize(self, text):
        if " " in text:
            text = text.replace(" ", "")
        if text.endswith("-"):
            text = text.replace("-", "")
        return text

    def string(self):
        return self._sanitize(self._zip)

class Zip4:
    def __init__(self, zip4):
        self._zip4 = zip4

    def string(self):
        return self._zip4

class Contact:
    def __init__(self):
        self._name = None
        self._company = None
        self._organization = None
        self._street = None
        self._city = None
        self._county = None
        self._state = None
        self._zip = None
        self._zip4 = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_value):
        if not isinstance(new_value, Name):
            raise ValueError("Value must be a Name")
        self._name = new_value

    @property
    def company(self):
        return self._company

    @company.setter
    def company(self, new_value):
        if not isinstance(new_value, Company):
            raise ValueError("Value must be a Company")
        self._company = new_value

    @property
    def organization(self):
        return self._organization

    @organization.setter
    def organization(self, new_value):
        if not isinstance(new_value, Organization):
            raise ValueError("Value must be an Organization")
        self._organization = new_value

    @property
    def street(self):
        return self._street

    @street.setter
    def street(self, new_value):
        if not isinstance(new_value, Street):
            raise ValueError("Value must be a Street")
        self._street = new_value

    @property
    def city(self):
        return self._city

    @city.setter
    def city(self, new_value):
        if not isinstance(new_value, City):
            raise ValueError("Value must be a City")
        self._city = new_value

    @property
    def county(self):
        return self._county

    @county.setter
    def county(self, new_value):
        if not isinstance(new_value, County):
            raise ValueError("Value must be a County")
        self._county = new_value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_value):
        if not isinstance(new_value, State):
            raise ValueError("Value must be a State")
        self._state = new_value

    @property
    def zip(self):
        return self._zip

    @zip.setter
    def zip(self, new_value):
        if not isinstance(new_value, Zip):
            raise ValueError("Value must be a Zip")
        self._zip = new_value

    @property
    def zip4(self):
        return self._zip4

    @zip4.setter
    def zip4(self, new_value):
        if not isinstance(new_value, Zip4):
            raise ValueError("Value must be a Zip")
        self._zip4 = new_value

    def to_json(self):
        object = {}
        if self._name is not None:
            object["name"] = self._name.string()
        if self._organization is not None:
            object["organization"] = self._organization.string()
        if self._company is not None:
            object["company"] = self._company.string()
        if self._street is not None:
            object["street"] = self._street.string()
        if self._city is not None:
            object["city"] = self._city.string()
        if self._county is not None:
            object["county"] = self._county.string()
        if self._state is not None:
            object["state"] = self._state.string()
        if self._zip is not None and self._zip4 is None:
            object["zip"] = self._zip.string()
        if self._zip is not None and self._zip4 is not None:
            object["zip"] = self._zip.string() + "-" + self._zip4.string()

        return object

def parse_xml_file(arg):
    # Load xml file
    tree = ET.parse(arg)

    # Get the root element
    root = tree.getroot()

    output = []

    # targeted fields in xml file
    field_names = [
        Field("NAME", "name"),
        Field("COMPANY", "company"),
        Field("STREET", "street"),
        Field("CITY", "city"),
        Field("STATE", "state"),
        Field("POSTAL_CODE", "zip")
    ]

    # Iterate each ENT tag and it's children
    for entity in root.iter("ENT"):
        contact = Contact()
        for field_name in field_names:
            field_tag = entity.find(field_name.tag)
            if field_tag is not None and len(field_tag.text.strip()) > 0:
                value = field_tag.text
                if field_name.name == "name":
                    contact.name = Name.from_string(value)
                elif field_name.name == "company":
                    contact.company = Company(value)
                elif field_name.name == "street":
                    contact.street = Street(value)
                elif field_name.name == "city":
                    contact.city = City(value)
                elif field_name.name == "state":
                    contact.state = State(value)
                elif field_name.name == "zip":
                    contact.zip = Zip(value)

        output.append(contact)

    return output




def parse_tsv_file(arg):
    with open(arg, "r", newline="") as file:
        reader = csv.reader(file, delimiter="\t")

        # Skip the first line
        next(reader)

        output = []

        # Specify tab ('\t') as the delimiter
        for row in reader:
            contact = Contact()

            # handle parsing of name and company
            firstNameIndex, middleNameIndex, lastNameIndex = 0, 1, 2
            name = Name(row[firstNameIndex], row[middleNameIndex], row[lastNameIndex])
            if name.has_content():
                contact.name = name

            # iterate through each field
            for index, item in enumerate(row):
                # handle city and states
                # Using state as a reference, check for other fields if there are data
                # Except for state index, do boundary check for other indexes
                if item in state_abbreviations or item in us_states:

                    # initiate all the indexing
                    streetIndex, cityIndex, countyIndex = index - 2, index - 1, index + 1

                    # handle street
                    if streetIndex >= 0:
                        contact.street = Street(row[streetIndex])
                    # handle city
                    if cityIndex >= 0:
                        contact.city = City(row[cityIndex])

                    #handle state
                    contact.state = State(row[index])

                    # handle county
                    if countyIndex <= len(row) - 1 :
                        if len(row[countyIndex]) > 0:
                            contact.county = County(row[countyIndex])


                # handle zip
                if item.isdigit():
                    if len(item) == 5:
                        contact.zip = Zip(item)
                    elif len(item) == 4:
                        contact.zip4 = Zip4(item)

                # handle company name
                lowered = item.lower()
                if "llc" in lowered or "ltd" in lowered or "inc" in lowered:
                    contact.organization = Organization(item)

            output.append(contact)

        return output


def parse_txt_file(arg):
    def is_street_name(string):
        # Regular expression pattern for a potential street name
        pattern = r'^[A-Za-z0-9\s\-\'&\.\#]+$'
        # Check if the string matches the pattern
        return bool(re.match(pattern, string))

    with open(arg, 'r') as file:
        file_content = file.read()
        groups = file_content.split("\n\n")
        output = []
        for group in groups:
            if group == "":
                continue

            contact = Contact()
            fields = group.split("\n")

            # name field is always the first one
            for fieldIndex, field in enumerate(fields):
                # parse name
                if fieldIndex == 0:
                    contact.name = Name.from_string(field.strip())
                    continue
                elif "county" in field.lower():
                    contact.county = County(field.strip())
                    continue
                elif is_street_name(field):
                    contact.street = Street(field.strip())
                    continue
                elif field == "":
                    continue
                else:
                    components = field.split(",")
                    city_pattern = r',\s*([A-Za-z\s]+)\s+[A-Za-z]{2}\s'
                    state_pattern = r'([A-Za-z\s]+)'
                    zip_code_pattern = r'\b\d{5}(?:-\d{4})?\b'

                    city_match = re.search(city_pattern, components[0])
                    state_match = re.search(state_pattern, components[1])
                    zip_code_match = re.search(zip_code_pattern, components[1])

                    if city_match:
                        contact.city = City(city_match.group(1))
                    if state_match:
                        contact.state = State(state_match.group(1))
                    if zip_code_match:
                        contact.zip = Zip(zip_code_match.group())

            output.append(contact)
        return output

def process_arguments(args):
    if len(args) < 1:
        print("Usage: python challenge.py <arg1> <arg2")
        return

    contacts = []

    files_to_process = []
    for index, arg in enumerate(args):
        if os.path.exists(arg):
            files_to_process.append(arg)
            continue
        else:
            print(f"input file '{arg}' does not exists", file=sys.stderr)
            sys.exit(1)

    for file in files_to_process:
        contacts.extend(process_file(file))

    output = [object.to_json() for object in contacts]

    # handle error when zip code is not found in any of the contact
    for object in output:
        if "zip" not in object:
            raise LookupError("zip not found in object")

    sorted_output = sorted(output, key=lambda x: x['zip'])

    # requirement: sort the output by zip code
    pretty_json = json.dumps(sorted_output, indent=2)
    print(pretty_json)

def process_file(arg):
    def get_file_extension(file_path):
        _, file_extension = os.path.splitext(file_path)
        return file_extension

    extension = get_file_extension(arg)
    if extension == ".xml":
        return parse_xml_file(arg)
    elif extension == ".tsv":
        return parse_tsv_file(arg)
    elif extension == ".txt":
        return parse_txt_file(arg)
    else:
        print(f"Extension {extension} not known")
        return []

def main():
    parser = argparse.ArgumentParser(description="A command line application that takes xml, tsv, txt file and outputs json")
    parser.add_argument('files', nargs='+', metavar='<file1, ...>', type=str, help="list all the files for parsing")
    args = parser.parse_args()

    files = args.files

    process_arguments(files)
    sys.exit(0)

if __name__ == "__main__":
    main()
