import re
import argparse
import json
import csv
import sys
import os
import xml.etree.ElementTree as ET

information = []

def clean_zip(zip):
    zip = re.sub(r'^[^0-9]*|[^0-9]*$', '', zip)
    zip = re.sub(r'\s', '', zip)
    return zip


def clean_name(name):
    name = name.replace(",", " , ")
    suffixes = {"II", "III", "IV", "VI"}
    processed_parts = []

    for part in name.split():
        # special capitalization case for names that start with Mc
        if part.startswith("Mc"):
            part = "Mc" + part[2:].capitalize()
        else:
            # keep suffixes uppercase
            part = part.title() if part not in suffixes else part.upper()

        processed_parts.append(part)

    # format comma properly
    return " ".join(processed_parts).replace(" ,", ",")


def is_organization(string):
    substrings = ['Inc.', 'LLC', 'LTD', 'Company', 'Corp.']
    return any(substring.lower() in string.lower() for substring in substrings)


def parse_address(address_str):
    parts = [part.strip() for part in address_str.split(',')]
    city_state_zip = parts[-1].split()
    city = parts[0].title()
    state = ' '.join(city_state_zip[:-1])
    state = state.upper() if len(state) == 2 else state.title()
    zip = clean_zip(city_state_zip[-1])
    return city, state, zip


def combine_strs(a, b, c):
    # combines addresses and names
    parts = [part.strip().title() for part in (a, b, c) if part.strip() and part.strip().lower() != 'n/m/n']
    return ' '.join(parts)


def add_to_information_list(entry):
    entry_info = {'name': '', 'organization': '', 'street': '', 'city': '', 'county': '', 'state': '', 'zip': ''}
    entry_info['organization'] = entry[0].strip().title() if is_organization(entry[0]) else ''
    entry_info['name'] = clean_name(entry[0].strip()) if not entry_info['organization'] else ''
    entry_info['street'] = entry[1].strip().title()
    # process county if it exists
    if 'COUNTY' in entry[2].upper():
        entry_info['county'] = entry[2].replace('COUNTY', '').strip().upper()
        entry_info['city'], entry_info['state'], entry_info['zip'] = parse_address(entry[3])
    else:
        entry_info['city'], entry_info['state'], entry_info['zip'] = parse_address(entry[2])
    information.append(entry_info)


def parse_text_file(file_name):
    with open(file_name, "r") as file:
        lines = file.read().splitlines()
    entry = []
    for line in lines:
        if not line.strip():
            if entry:
                add_to_information_list(entry)
                entry = []
        else:
            entry.append(line.strip())
    if entry:
        add_to_information_list(entry)


def parse_tsv_file(file_name):
    with open(file_name, 'r', newline='', encoding='utf-8') as tsvfile:
        tsvreader = csv.DictReader(tsvfile, delimiter='\t')
        for row in tsvreader:
            entry_info = {'name': '', 'organization': '', 'street': '', 'city': '', 'county': '', 'state': '', 'zip': ''}
            name = combine_strs(row['first'], row['middle'], row['last'])
            organization = row['organization'].strip()
            entry_info['street'] = row['address'].strip().title()
            entry_info['city'] = row['city'].strip().title()
            entry_info['state'] = row['state'].strip()
            entry_info['county'] = row['county'].strip().upper()
            entry_info['zip'] = clean_zip(row['zip'])
            # check if string under 'name' is a name or orgnanization
            if name and is_organization(name):
                entry_info['organization'] = name
            elif organization and not name:
                entry_info['organization'] = organization
            elif name and organization.strip() == 'N/A':
                entry_info['name'] = clean_name(name)
            else:
                print("Duplicate organization and name:", organization, " and ", name, file=sys.stderr)
            information.append(entry_info)


def parse_xml_file(file_name):
    tree = ET.parse(file_name)
    root = tree.getroot()
    for entity in root.findall('./ENTITY/ENT'):
        entry_info = {'name': '', 'organization': '', 'street': '', 'city': '', 'county': '', 'state': '', 'zip': ''}
        entry_info['name'] = clean_name(entity.find('NAME').text.strip())
        entry_info['organization'] = entity.find('COMPANY').text.strip().title()
        entry_info['street'] = combine_strs(entity.find('STREET').text, entity.find('STREET_2').text,
                                            entity.find('STREET_3').text)
        entry_info['city'] = entity.find('CITY').text.strip().title()
        entry_info['state'] = entity.find('STATE').text.strip()
        entry_info['zip'] = clean_zip(entity.find('POSTAL_CODE').text.strip())
        information.append(entry_info)


def main():
    parser = argparse.ArgumentParser(description="Parse and combine .xml, .tsv, and .txt file(s) into a JSON-encoded list of the combined addresses, sorted by ZIP code in ascending order.")
    parser.add_argument("files", metavar="FILE", nargs='+', help="Input files containing addresses in text format.")
    args = parser.parse_args()
    for file in args.files:
        file = os.path.join("input", file)
        try:
            if file.endswith('.txt'):
                parse_text_file(file)
            elif file.endswith('.tsv'):
                parse_tsv_file(file)
            elif file.endswith('.xml'):
                parse_xml_file(file)
            else:
                print(file + " is not a valid file type.", file=sys.stderr)
                sys.exit(1)
        except FileNotFoundError:
            print(f"File not found: {file}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error parsing {file}: {e}", file=sys.stderr)
            sys.exit(1)

    # sort data by zip code
    sorted_data = sorted(information, key=lambda x: x['zip'])
    cleaned_data = [{k: v for k, v in d.items() if v} for d in sorted_data]
    if cleaned_data:
        output = json.dumps(cleaned_data, indent=4)
        print(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
