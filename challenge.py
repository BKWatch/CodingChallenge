import xml.etree.ElementTree as ET
import csv
import json
import argparse
import sys


def parse_xml(file_path):
    """
    Parse an XML file containing address data and return a list of addresses.

    Parameters:
    - file_path (str): The path to the XML file.

    Returns:
    - list: A list of dictionaries containing parsed address data.
    """
    addresses = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for ent in root.findall('ENTITY/ENT'):
            address = {}
            name = ent.find('NAME').text.strip()
            company = ent.find('COMPANY').text.strip()
            street = ent.find('STREET').text.strip()
            city = ent.find('CITY').text.strip()
            county = ent.find('COUNTY').text.strip() if ent.find(
                'COUNTY') is not None else None
            state = ent.find('STATE').text.strip()
            postal_code = ent.find(
                'POSTAL_CODE').text.strip().replace(" -", "")

            if name:
                address['name'] = name
            elif company:
                address['organization'] = company

            address['street'] = street
            address['city'] = city
            if county:
                address['county'] = county
            address['state'] = state
            address['zip'] = postal_code

            addresses.append(address)

        return addresses
    except Exception as e:
        print(f"Error parsing XML file {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def parse_tsv(file_path):
    """
    Parse a TSV file containing address data and return a list of addresses.

    Parameters:
    - file_path (str): The path to the TSV file.

    Returns:
    - list: A list of dictionaries containing parsed address data.
    """
    addresses = []
    try:
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                address = {}
                name_parts = [row['first'], row['middle'], row['last']]
                name = ' '.join(filter(None, name_parts)).strip()
                company = row['organization'].strip()
                street = row['address'].strip()
                city = row['city'].strip()
                county = row['county'].strip() if 'county' in row else ""
                state = row['state'].strip()
                zip_code = row['zip'].strip(
                ) + "-" + row['zip4'].strip() if row['zip4'] else row['zip'].strip()

                if name:
                    address['name'] = name
                elif company:
                    address['organization'] = company

                address['street'] = street
                address['city'] = city
                if county:
                    address['county'] = county
                address['state'] = state
                address['zip'] = zip_code

                addresses.append(address)

        return addresses
    except Exception as e:
        print(f"Error parsing TSV file {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def parse_txt(file_path):
    """
    Parse a TXT file containing address data and return a list of addresses.

    Parameters:
    - file_path (str): The path to the TXT file.

    Returns:
    - list: A list of dictionaries containing parsed address data.
    """
    addresses = []
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

            # Trim leading whitespace and filter out empty lines
            lines = [line.strip() for line in lines if line.strip()]

            i = 0
            while i < len(lines):
                address = {}
                name = lines[i].strip()
                street = lines[i + 1].strip()

                # Check if "county" exists in line 3
                if "county" in lines[i + 2].lower():
                    county = lines[i + 2].strip()
                    city_zip = lines[i + 3].strip()
                    i += 4  # Increase the range to 4 lines
                else:
                    county = ""
                    city_zip = lines[i + 2].strip()
                    i += 3  # Keep the range to 3 lines

                city_state_zip = city_zip.split(',')
                city = city_state_zip[0].strip()

                if len(city_state_zip) > 1:
                    # Extract state and zip code
                    parts = city_state_zip[1].strip().split()
                    state = ' '.join(parts[:-1]).strip()
                    zip_code = parts[-1].strip() if parts[-1].isdigit() else ""
                else:
                    state = ""
                    zip_code = ""

                address['name'] = name
                address['street'] = street
                address['city'] = city
                address['county'] = county
                address['state'] = state
                address['zip'] = zip_code

                addresses.append(address)

        return addresses
    except Exception as e:
        print(f"Error parsing TXT file {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def main(file_paths, output_file=None):
    """
    Main function to parse input files and combine addresses.

    Parameters:
    - file_paths (list): List of input file paths.
    - output_file (str, optional): Output file path. If None, output is displayed on console.
    """
    combined_addresses = []

    for file_path in file_paths:
        if file_path.endswith('.xml'):
            combined_addresses.extend(parse_xml(file_path))
        elif file_path.endswith('.tsv'):
            combined_addresses.extend(parse_tsv(file_path))
        elif file_path.endswith('.txt'):
            combined_addresses.extend(parse_txt(file_path))

    combined_addresses.sort(key=lambda x: x['zip'])

    if output_file:
        with open(output_file, 'w') as outfile:
            json.dump(combined_addresses, outfile, indent=2)
    else:
        print(json.dumps(combined_addresses, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Parse input files and combine addresses.')
    parser.add_argument('file_paths', nargs='+',
                        help='List of input file paths')
    parser.add_argument('--output', '-o', default=None,
                        help='Output file path')

    args = parser.parse_args()

    if not all(path.endswith(('.xml', '.tsv', '.txt')) for path in args.file_paths):
        print("Error: Invalid file format. Supported formats are .xml, .tsv, .txt", file=sys.stderr)
        sys.exit(1)

    main(args.file_paths, args.output)