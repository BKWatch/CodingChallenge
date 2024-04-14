import xml.etree.ElementTree as ET
import argparse
import json
import os
import sys
import csv

# Function to parse XML files
def parse_xml(file):
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        data = []

        for ent in root.findall('.//ENT'):
            entry = {}
            for child in ent:
                tag = child.tag.lower()
                if tag == 'name':
                    if child.text.strip():
                        entry['name'] = child.text.strip()
                    else:
                        entry['organization'] = ent.find('COMPANY').text.strip()
                elif tag == 'street' or tag == 'city' or tag == 'state':
                    entry[tag] = child.text.strip()
                elif tag == 'country':
                    if child.text.strip():
                        entry['county'] = child.text.strip()
                elif tag == 'postal_code':
                    entry['zip'] = child.text.strip()
            data.append(entry)

        return data
    except ET.ParseError as e:
        print(f"Error parsing XML file {file}: {str(e)}", file=sys.stderr)
        return []

# Function to parse TSV files
def parse_tsv(file):
    try:
        data = []
        with open(file, 'r', newline='') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                entry = {}
                name = " ".join([row.get("first", ""), row.get("middle", ""), row.get("last", "")]).strip()
                if name:
                    entry['name'] = name
                else:
                    entry['organization'] = row['organization'].strip() if 'n/a' not in row['organization'].lower() else ''
                entry['street'] = row['address'].strip()
                entry['city'] = row['city'].strip()
                entry['state'] = row['state'].strip()
                entry['zip'] = f"{row['zip'].strip()}-{row['zip4'].strip()}" if row['zip4'].strip() else row['zip'].strip()
                data.append(entry)
        return data
    except csv.Error as e:
        print(f"Error reading TSV file {file}: {str(e)}", file=sys.stderr)
        return []

# Function to parse TXT files
def parse_txt(file):
    try:
        data = []
        with open(file, 'r') as f:
            lines = f.read().split('\n\n')
            for line in lines:
                parts = line.strip().split('\n')
                if len(parts) >= 3:
                    entry = {
                        'name': parts[0].strip() if not any(x in parts[0].lower() for x in ['llc', 'inc', 'ltd']) else '',
                        'organization': parts[0].strip() if any(x in parts[0].lower() for x in ['llc', 'inc', 'ltd']) else '',
                        'street': parts[1].strip(),
                        'city': parts[-1].split(',')[0].strip(),
                        'state': parts[-1].split(',')[1].split()[0].strip(),
                        'zip': parts[-1].split()[-1].replace(" ", "").rstrip('-')
                    }
                    data.append({k: v for k, v in entry.items() if v.strip()})
        return data
    except IOError as e:
        print(f"Error reading TXT file {file}: {str(e)}", file=sys.stderr)
        return []

# Function to parse input files
def parse_input_files(files):
    data = []
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext == '.xml':
            data.extend(parse_xml(file))
        elif ext == '.tsv':
            data.extend(parse_tsv(file))
        elif ext == '.txt':
            data.extend(parse_txt(file))
        else:
            print(f"Skipping unrecognized file type: {file}", file=sys.stderr)
    return data

# Function to print JSON formatted entries sorted by ZIP code
def print_sorted_entries(entries):
    return sorted(entries, key=lambda x: x['zip'])

def main():
    parser = argparse.ArgumentParser(description='Parse address files and output JSON.')
    parser.add_argument('--files', nargs='+', required=True, help='a list of files to parse')
    args = parser.parse_args()

    data_list = parse_input_files(args.files)

    if data_list:
        json_data = json.dumps(print_sorted_entries(data_list), indent=2)
        print(json_data)
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
