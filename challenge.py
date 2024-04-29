import argparse
import xml.etree.ElementTree as ET
import csv
import json
import sys

def clean_text(text):
    # Strip, remove spaces, and trailing hyphens from the text.
    return text.strip().replace(' ', '').rstrip('-')

def parse_xml(file, errors):
    # Parse XML file and return a list of dictionaries with parsed data, handling errors.
    try:
        tree = ET.parse(file)
        root = tree.getroot()
    except ET.ParseError as e:
        sys.stderr.write(f"Error parsing XML file {file}: {str(e)}\n")
        errors[0] = True
        return []

    return [{
        child.tag.lower(): clean_text(child.text)
        for child in ent if child.tag != 'COUNTRY' and child.text.strip()
    } for ent in root.findall('.//ENT')]

def parse_tsv(file, errors):
    # Parse TSV file and return a list of dictionaries with parsed data, handling errors.
    try:
        with open(file, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            return [{
                k: clean_text(v) for k, v in row.items() if v.strip() and k != 'zip4'
            } for row in reader]
    except csv.Error as e:
        sys.stderr.write(f"Error reading TSV file {file}: {str(e)}\n")
        errors[0] = True
        return []

def parse_txt(file, errors):
    # Parse TXT file and return a list of dictionaries with parsed data, handling errors.
    try:
        with open(file, 'r') as f:
            content = f.read().strip()
        records = content.split('\n\n')
        return [{
            k: v.strip() for k, v in zip(['name', 'street', 'city', 'state', 'zip'], record.split('\n')) if v.strip()
        } for record in records]
    except IOError as e:
        sys.stderr.write(f"Error reading TXT file {file}: {str(e)}\n")
        errors[0] = True
        return []

def main():
    # Main function to parse specified files and output JSON formatted addresses.
    parser = argparse.ArgumentParser(description='Parse address files and output JSON.')
    parser.add_argument('--files', nargs='+', required=True, help='List of files to parse')
    args = parser.parse_args()

    data_list = []
    errors = [False]  # Use a list to hold the boolean flag to allow modification in other functions
    for file in args.files:
        extension = file.rsplit('.', 1)[-1].lower()
        parse_func = globals().get(f'parse_{extension}', None)
        if parse_func:
            data_list.extend(parse_func(file, errors))
        else:
            sys.stderr.write(f"Skipping unrecognized file type: {file}\n")
            errors[0] = True

    if data_list and not errors[0]:
        sorted_data = sorted(data_list, key=lambda x: x.get('zip', ''))
        print(json.dumps(sorted_data, indent=2))
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
