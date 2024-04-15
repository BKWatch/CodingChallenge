import argparse
import csv
import json
import xml.etree.ElementTree as ET
from sys import stderr, stdout
import os

def validate_file(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    if not os.path.isfile(filepath):
        raise IsADirectoryError(f"Expected a file, but it's a directory: {filepath}")
    if not filepath.endswith(('.xml', '.tsv', '.txt')):
        raise ValueError(f"Unsupported file type: {filepath}")
    return True

def parse_xml(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()

    entries = []
    for ent in root.findall('./ENTITY/ENT'):
        entry = {}
        name = ent.find('NAME').text
        company = ent.find('COMPANY').text
        street = ent.find('STREET').text
        city = ent.find('CITY').text
        state = ent.find('STATE').text
        zip_code = ent.find('POSTAL_CODE').text.strip(' -')
        zip_code = zip_code.replace(" ", "")
        entry['name' if name.strip() else 'organization'] = name.strip() or company.strip()
        entry['street'] = street.strip()
        entry['city'] = city.strip()
        entry['state'] = state.strip()
        entry['zip'] = zip_code.strip()

        entries.append(entry)

    return entries

def parse_tsv(filepath):
    entries = []
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            entry = {}
            name_parts = [row['first'], row['middle'], row['last']]
            name = ' '.join(part for part in name_parts if part and part != 'N/M/N')
            company = row['organization']
            entry['name' if name else 'organization'] = name or company
            entry['street'] = row['address'].strip()
            entry['city'] = row['city'].strip()
            entry['state'] = row['state'].strip()
            entry['zip'] = row['zip'].strip() + ('-' + row['zip4'].strip() if row['zip4'] else '')

            entries.append(entry)

    return entries

def parse_txt(filepath):
    entries = []
    with open(filepath, 'r') as file:
        entry = {}
        for line in file:
            line = line.strip()
            if 'COUNTY' in line or 'INC.' in line:
                continue
            if not line:
                if entry:
                    entry.setdefault('name', '')
                    entry.setdefault('street', '')
                    entry.setdefault('city', '')
                    entry.setdefault('state', '')
                    entry.setdefault('zip', '')
                    entries.append(entry)
                    entry = {}
            elif any(char.isdigit() for char in line):
                if ',' in line:
                    city_state_zip = line.split(', ')
                    if len(city_state_zip) > 1:
                        entry['city'] = city_state_zip[0].strip()
                        state_zip_parts = city_state_zip[1].split(' ')
                        entry['state'] = ' '.join(state_zip_parts[:-1]).strip()
                        entry['zip'] = state_zip_parts[-1].strip().rstrip('-')
                else:
                    entry['street'] = line
            else:
                entry['name'] = line
        if entry:
            entry.setdefault('name', '')
            entry.setdefault('street', '')
            entry.setdefault('city', '')
            entry.setdefault('state', '')
            entry.setdefault('zip', '')
            entries.append(entry)
    return entries

def main(filepaths):
    entries = []
    for path in filepaths:
        try:
            validate_file(path)
            if path.endswith('.xml'):
                entries.extend(parse_xml(path))
            elif path.endswith('.tsv'):
                entries.extend(parse_tsv(path))
            elif path.endswith('.txt'):
                entries.extend(parse_txt(path))
        except Exception as e:
            print(f"Error processing {path}: {e}", file=stderr)
            exit(1)
    sorted_entries = sorted(entries, key=lambda x: x['zip'])
    json.dump(sorted_entries, stdout, indent=4)
    exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse and combine address information from multiple files')
    parser.add_argument('filepaths', nargs='+', help='The file paths to parse')
    args = parser.parse_args()

    main(args.filepaths)
