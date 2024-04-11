import csv
import xml.etree.ElementTree as ET
import sys
import argparse
import json


# Get city, state and zip from line
def city_state_zip_parse(line):
    # Split into city, state and zip
    parts = line.split(',')
    city = parts[0].strip()
    state_zip = parts[1].strip()

    # Find space to separate state from zip
    last_space_index = state_zip.rfind(' ')
    state = state_zip[:last_space_index].strip()
    zip_code = state_zip[last_space_index + 1:].strip()

    # Remove '-' from zip code if there is no zip4 section
    if zip_code.endswith('-'):
        zip_code = zip_code[:-1]

    return city, state, zip_code


def parse_txt(txt_file):
    try:
        records = []
        with open(txt_file, 'r') as file:
            lines = file.readlines()
            i = 0
            # Removes any whitespace above first record
            while i < len(lines) and not lines[i].strip():
                i += 1
            while i < len(lines):
                record = {}

                # Get Person/Company name
                if any(keyword in lines[i] for keyword in ['LLC', 'Ltd.', 'Inc.']):
                    record["organization"] = lines[i].strip()
                    i += 1
                else:
                    record["name"] = lines[i].strip()
                    i += 1

                # Get Street
                record["street"] = lines[i].strip()
                i += 1

                # Get County (if available), if not parse city,state,zip
                if lines[i].strip().isupper():
                    city, state, zip_code = city_state_zip_parse(lines[i + 1])
                    record["city"] = city
                    record["county"] = lines[i].strip().split(' ')[0]
                    record["state"] = state
                    record["zip"] = zip_code
                    # skip to next record, not city,state,zip since we already covered it.
                    i += 2
                else:
                    city, state, zip_code = city_state_zip_parse(lines[i])
                    record["city"] = city
                    record["state"] = state
                    record["zip"] = zip_code
                    i += 1
                i += 1
                records.append(record)
        return records
    except Exception as e:
        sys.stderr.write(f"Error parsing TXT file: {e}\n")
        sys.exit(1)


def parse_tsv(tsv_file):
    try:
        with open(tsv_file) as file:
            records = []
            for line in file:
                fields = line.strip().split('\t')
                record = {}
                # Get Company name (if conditions met), set index to read rest of data
                if any(keyword in fields[0] for keyword in ['LLC', 'Ltd.', 'Inc.']):
                    record["organization"] = fields[0]
                    if fields[1] == "N/A":
                        name_index = 2
                    else:
                        name_index = 1
                # Get personal name (exclude middle name is there isn't one), set index to read rest of data
                else:
                    # .rstip(',') is to take out any commas (ex. "Arnulfo Hernandez Dacanay,")
                    name = [field.rstrip(',') for field in fields[:3] if field and field != 'N/M/N']
                    record["name"] = " ".join(name) if name else None
                    name_index = 4

                # Get street and city name
                street_index = name_index
                record["street"] = fields[street_index]
                record["city"] = fields[street_index + 1]

                # Get state and county index (switch order for preferred results)
                state_index = street_index + 2
                county_index = state_index + 1
                # If county index isn't empty
                if fields[county_index]:
                    record["county"] = fields[state_index]
                    record["state"] = fields[county_index]
                else:
                    record["state"] = fields[state_index]

                # Check if there is a zip4 code
                if fields[-2].isdigit():
                    zip_code = fields[-2]
                    zip4_code = fields[-1]
                    record["zip"] = f"{zip_code}-{zip4_code}"
                else:
                    record["zip"] = fields[-1]
                records.append(record)
            # first item in tsv file is column headers, removes this from the results
            return records[1:]
    except Exception as e:
        sys.stderr.write(f"Error parsing TSV file: {e}\n")
        sys.exit(1)


'''
Note: In every tsv file, if first, middle or last name are empty. List begins with company name, however if county is
empty, there is a gap '' between state and zip. My code is based on the assumption that the only possible empty value
in the list is county. Empty (first, middle, last and zip 4) values all will not return a '' value.
'''


def parse_xml(xml_file):
    try:
        records = []
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for ent in root.findall('.//ENT'):
            record = {}

            # Get name or company (insert the non-empty variable)
            name = ent.find('NAME').text.strip()
            company = ent.find('COMPANY').text.strip()
            if name:
                record["name"] = name
            else:
                record["organization"] = company

            # Get street address
            street = ent.find('STREET').text.strip()
            # If <STREET> is empty, check <STREET_2>. If not, return street
            if not street:
                street_2 = ent.find('STREET_2').text.strip()
                # IF <STREET_2> is empty, return <STREET_3>
                if not street_2:
                    record["street"] = ent.find('STREET_3').text.strip()
                else:
                    record["street"] = street_2
            record["street"] = street

            # Get city and state
            record["city"] = ent.find('CITY').text.strip()
            record["state"] = ent.find('STATE').text.strip()

            # Get Postal Code
            postal_code = ent.find('POSTAL_CODE').text.strip()

            # If there is only first portion of zip code (first 5 digits)
            if postal_code[-1] == "-":
                record["zip"] = postal_code[:5]
            elif postal_code[-1].isdigit():
                record["zip"] = postal_code
            records.append(record)

        return records
    except Exception as e:
        sys.stderr.write(f"Error parsing XML file: {e}\n")
        sys.exit(1)


def main():
    # Create argument parser
    parser = argparse.ArgumentParser(
        description='''A script to parse various file formats and output addresses as JSON sorted by ZIP code.''')
    parser.add_argument('files', nargs='+', help='list of file(s) to parse')
    args = parser.parse_args()

    # If not files were given
    if not args.files:
        parser.print_help(sys.stderr)
        sys.exit(1)

    addresses = []
    # Iterate through each given file and parse through data
    for file_path in args.files:
        if file_path.endswith('.txt'):
            parsed_data = parse_txt(file_path)
        elif file_path.endswith('.tsv'):
            parsed_data = parse_tsv(file_path)
        elif file_path.endswith('.xml'):
            parsed_data = parse_xml(file_path)
        else:
            sys.stderr.write(f"Unsupported file format: {file_path}\n")
            sys.exit(1)
        addresses.extend(parsed_data)

    # Make sure there was data to be parsed
    if addresses:
        # Sort addresses by ZIP code
        addresses.sort(key=lambda x: x.get('zip', ''))
        # Output JSON
        print(json.dumps(addresses, indent=4))
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
