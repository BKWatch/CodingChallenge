import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET


def parse_xml(file_path):
    try:
        addresses = []
        tree = ET.parse(file_path)
        root = tree.getroot()

        for ent in root.findall('./ENTITY/ENT'):
            name = ent.find('NAME').text.strip()
            company = ent.find('COMPANY').text.strip()
            street = ent.find('STREET').text.strip()
            city = ent.find('CITY').text.strip()
            state = ent.find('STATE').text.strip()
            country = ent.find('COUNTRY').text.strip()
            postal_code_text = ent.find('POSTAL_CODE').text.strip()
            postal_code = postal_code_text.split('-')[0].strip()  # Extract only postal code

            # Append address to the list
            address = {
                'name': name,
                'organization': company,
                'street': street,
                'city': city,
                'state': state,
                'country': country,
                'zip': postal_code
            }
            addresses.append(address)

        return addresses

    except (FileNotFoundError, IOError, ET.ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return []


def parse_tsv(file_path):
    """
    Parse TSV file containing addresses.

    Args:
        file_path (str): Path to the TSV file.

    Returns:
        list: List of dictionaries containing parsed addresses.
    """
    try:
        addresses = []
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split('\t')
                # Ensure correct number of fields
                if len(parts) >= 6:
                    address = {
                        'name': parts[0],
                        'street': parts[1],
                        'city': parts[2],
                        'county': parts[3],
                        'state': parts[4],
                        'zip': parts[5]
                    }
                else:
                    # If any field is missing, set it to an empty string
                    address = {
                        'name': parts[0] if len(parts) > 0 else '',
                        'street': parts[1] if len(parts) > 1 else '',
                        'city': parts[2] if len(parts) > 2 else '',
                        'county': parts[3] if len(parts) > 3 else '',
                        'state': parts[4] if len(parts) > 4 else '',
                        'zip': parts[5] if len(parts) > 5 else ''
                    }
                addresses.append(address)
        return addresses
    except FileNotFoundError:
        print(f"Error: TSV file {file_path} not found.", file=sys.stderr)
        return []


def parse_txt(file_path):
    try:
        addresses = []
        malformed_entries = 0  # Counter for malformed entries
        with open(file_path, 'r') as file:
            lines = file.readlines()
            current_entry = []
            for line_index, line in enumerate(lines, start=1):
                if line.strip():  # If the line is not empty
                    current_entry.append(line.strip())
                else:  # Empty line indicates end of current entry
                    if len(current_entry) >= 4:
                        name = current_entry[0].strip()
                        # Extracting city, state, and zip code from the last line
                        city_state_zip = current_entry[-1].strip().split(',')
                        city = city_state_zip[0].strip()
                        state_zip = city_state_zip[-1].strip().split(' ')
                        state = ' '.join(state_zip[:-1])
                        zip_code = state_zip[-1]
                        # Checking if county is mentioned
                        county = current_entry[2].strip() if len(current_entry) >= 5 else ''
                        street = current_entry[1].strip()
                        # If county contains 'COUNTY', use the city as the county
                        if 'COUNTY' in county:
                            county = ''
                        address = {
                            'name': name,
                            'organization': '',
                            'street': street,
                            'city': city,
                            'county': county,
                            'state': state,
                            'zip': zip_code
                        }
                        addresses.append(address)
                    else:
                        malformed_entries += 1
                        print(f"Warning: Malformed address entry found in entry {line_index}. Skipping...",
                              file=sys.stderr)
                    # Reset current entry list for the next entry
                    current_entry = []
            if malformed_entries > 0:
                print(f"Total {malformed_entries} malformed address entries found.", file=sys.stderr)
        return addresses
    except FileNotFoundError:
        print(f"Error: TXT file {file_path} not found.", file=sys.stderr)
        return []


def combine_and_sort_addresses(file_paths):
    """
    Combine addresses from multiple files and sort them by zip code.

    Args:
        file_paths (list): List of file paths.

    Returns:
        list: Combined and sorted list of addresses.
    """
    all_addresses = []
    for file_path in file_paths:
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.xml':
            all_addresses.extend(parse_xml(file_path))
        elif file_extension == '.tsv':
            all_addresses.extend(parse_tsv(file_path))
        elif file_extension == '.txt':
            all_addresses.extend(parse_txt(file_path))
        else:
            print(f"Error: Unsupported file format for {file_path}", file=sys.stderr)
    sorted_addresses = sorted(all_addresses, key=lambda x: x.get('zip', ''))
    return sorted_addresses


def main():
    parser = argparse.ArgumentParser(description='Combine and sort addresses from XML, TSV, and TXT files.')
    parser.add_argument('files', nargs='+', help='List of file paths to process')
    args = parser.parse_args()

    if not args.files:
        parser.print_usage()
        sys.exit(1)

    addresses = combine_and_sort_addresses(args.files)
    if addresses:
        output_file_path = os.path.join(os.getcwd(), 'addresses.json')  # JSON file path in current directory
        with open(output_file_path, 'w') as json_file:
            json.dump(addresses, json_file, indent=2)
        print(f"Output JSON file successfully generated at {output_file_path}")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
