import argparse
import sys
import json
import re
import xml.etree.ElementTree as ET
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="""challenge.py version 1.0.0 (c) Eli Hansen 2024
                                                    Program parses files containing address information, with the
                                                    following formats: .xml, .tsv and .txt and converts the address
                                                    info. to a JSON file.""",
                                     epilog='Example usage: challenge.py <input_file>')

    parser.add_argument('--version', action='version',
                        version='%(prog)s 1.0.0')

    parser.add_argument('input_file', metavar='input_file', type=str, help='Input file name and file path (i.e. '
                                                                           'c:/myfile.xml, c:/myfile.tsv, or c:/myfile.txt)')

    args = parser.parse_args()

    input_file = args.input_file

    # Determine the file format based on the file extension
    file_format = input_file.split('.')[-1]

    # Execute the appropriate code based on the file format
    if file_format == 'tsv':
        addresses = parse_tsv(input_file)
    elif file_format == 'txt':
        addresses = parse_txt(input_file)
    elif file_format == 'xml':
        addresses = parse_xml(input_file)
    else:
        sys.stderr.write(
            "Error: Unsupported file format.Please provide a file with .xml, .tsv, or .txt extension.")
        sys.exit(1)

    # Sort addresses by 'zip' in ascending order
    addresses.sort(key=lambda x: x['zip'])

    output_file = "addresses.json"
    save_to_json(addresses, output_file)
    print(f"Addresses saved to {output_file}")
    sys.exit(0)


def parse_xml(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        return elem_to_dict(root)
    except ET.ParseError as e:
        sys.stderr.write(f"Error parsing XML file: {e}\n")
        sys.exit(1)


def elem_to_dict(elem):
    entries = []
    for child in elem.findall('.//ENT'):
        entry_dict = {}
        for sub_elem in child:
            # Lowercase the keys and replace 'company' with 'organization' and 'postal_code' with 'zip'
            key = sub_elem.tag.lower()
            if key == 'company':
                key = 'organization'
            if key == 'postal_code':
                key = 'zip'
                # Remove spaces around hyphen
                zip_code = sub_elem.text.strip().replace(" ", "")
                # Check for hyphen and adjust zip code format accordingly
                if '-' in zip_code:
                    # Remove the hyphen if there are no digits or characters after it
                    zip_code = re.sub(r'\s*-\s*$', '', zip_code)
                    # Remove the space around the hyphen if there are digits or characters after it
                    zip_code = re.sub(r'\s*-\s*(\d)', r'-\1', zip_code)
                entry_dict[key] = zip_code
            else:
                # Capitalize first letter of each word in the name
                if key == 'name':
                    entry_dict[key] = ' '.join(
                        word.capitalize() for word in sub_elem.text.strip().split())
                else:
                    entry_dict[key] = sub_elem.text.strip(
                    ) if sub_elem.text else None
        entries.append(entry_dict)
    return entries


def parse_tsv(input_file):
    try:
        data = pd.read_csv(input_file, sep="\t", dtype=str)
    except pd.errors.ParserError as e:
        sys.stderr.write(
            "Error: Input file is not a valid TSV file. Please check the file format.\n")
        sys.exit(1)

    expected_columns = {'first', 'middle', 'last', 'organization',
                        'address', 'city', 'county', 'state', 'zip', 'zip4'}
    if not set(data.columns) == expected_columns:
        sys.stderr.write(
            "Error: Input file does not conform to the expected format.\n")
        sys.exit(1)

    data.fillna('', inplace=True)  # Replace NaN values with empty strings

    parsed_data_list = data.apply(check_name, axis=1).to_list()
    data['zip'] = data.apply(lambda row: construct_zip_code(row), axis=1)

    parsed_data_list.sort(key=lambda x: x['zip'])

    return parsed_data_list


def check_name(row):
    org_keywords = ['llc', 'inc', 'ltd']
    org_name = str(row['organization'] or row['last'])
    is_organization = any(keyword in org_name.lower()
                          for keyword in org_keywords)

    full_name = f"{row['first']} {row['middle']} {row['last']}" \
        if row['middle'] != 'N/M/N' else f"{row['first']} {row['last']}"

    return {
        'name': "" if is_organization else full_name,
        'organization': org_name if is_organization else "",
        'street': row['address'],
        'city': row['city'],
        'county': "" if pd.isna(row['county']) else row['county'],
        'state': row['state'],
        'zip': construct_zip_code(row)
    }


def construct_zip_code(row):
    # Remove leading and trailing space and check if zip is 9-digit zip or 5-digit zip
    main_zip = str(row['zip'])
    zip4 = str(row['zip4']).strip().split('.')[
        0] if pd.notna(row['zip4']) else ""

    if zip4:
        zip4 = zip4.zfill(4)

    if zip4:
        return f"{main_zip}-{zip4}"
    else:
        return main_zip


def parse_txt(input_file):
    addresses = []
    try:
        with open(input_file, 'r') as file:
            lines = file.readlines()
            i = 0

            # Iterate over each line until the end of the file and create a dictionary
            while i < len(lines):
                entry = {}

                # Initializes counter 'j' to start on the next line after 'i' and checks if the line contains digits or 'P.O.'
                name_or_org = lines[i].strip()
                j = i + 1
                while j < len(lines) and not any(c.isdigit() for c in lines[j]) and not lines[j].startswith('P.O.'):
                    name_or_org += " " + lines[j].strip()
                    j += 1

                # Check if the line contains typical keywords associated with an organization
                keywords = ['ltd', 'llc', 'inc']
                if any(keyword.lower() in name_or_org.lower() for keyword in keywords):
                    # Capitalize first letter of each word
                    entry['organization'] = name_or_org.title()
                else:
                    # Capitalize first letter of each word
                    entry['name'] = name_or_org.title()

                i = j

                # Check if 'i' is within the bounds of the 'lines' list
                if i < len(lines):
                    # Remove leading and trailing space and assign the street address to the key 'street'
                    entry['street'] = lines[i].strip()
                    i += 1

                    # If 'i' is still within the bounds of the 'lines' list
                    if i < len(lines):
                        county = lines[i].strip()
                        if 'county' in county.lower():
                            # Capitalize the first letter of each word in the county name
                            county = ' '.join(word.capitalize()
                                              for word in county.split())
                            entry['county'] = county
                            i += 1
                        else:
                            # Initialize county with an empty string if not present
                            entry['county'] = ''

                    # If 'i' is still within the bounds of the 'lines' list
                    if i < len(lines):
                        # Removes leading and trailing space, splits by ',' and assigns to the variable city_state_zip
                        city_state_zip = lines[i].strip().split(', ')
                        if len(city_state_zip) >= 2:
                            # Extract city, state, and zip code
                            # Capitalize the first letter of each word
                            city = city_state_zip[0].title()
                            state_zip = city_state_zip[-1]
                            # Find the last space, which separates the state and zip code
                            zip_start = state_zip.rfind(' ')
                            if zip_start != -1:
                                state = state_zip[:zip_start].strip()
                                zip_code = state_zip[zip_start + 1:].strip()
                            else:
                                # If no space is found, assume the entire string is the state and zip code
                                state = state_zip.strip()
                                zip_code = ''

                            # Remove hyphen if the zip code is five characters followed by a hyphen
                            if len(zip_code) == 6 and zip_code[5] == '-':
                                zip_code = zip_code[:5]

                            # Assign city, state, and zip values to keys
                            entry['city'] = city
                            entry['state'] = state
                            entry['zip'] = zip_code

                            addresses.append(entry)

                            i += 1
                        else:
                            # Raise ValueError if city_state_zip has fewer than 2 elements
                            raise ValueError(
                                "Insufficient elements in city_state_zip")

                # Increment 'i' only if 'i' is still within the bounds of the 'lines' list
                if i < len(lines):
                    i += 1

    except (FileNotFoundError, ValueError, IndexError) as error:
        sys.stderr.write(f"Error: {error}\n")
        sys.exit(1)
    return addresses


def save_to_json(addresses, output_file):
    with open(output_file, 'w') as file:
        json.dump(addresses, file, indent=4)


if __name__ == "__main__":
    main()
