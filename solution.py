import sys
import json
import xml.etree.ElementTree as ET
import argparse
from operator import itemgetter
import csv

def handle_xml(file_path):
    """This function parses .xml file and returns data as a list of dictionaries"""
    tree = ET.parse(file_path)
    root = tree.getroot()
    data = []
    for ent in root.findall('.//ENT'):
        # Gets individual entries
        entry = {}
        for element in ent:
            tag = element.tag.upper()
            if tag in ['NAME', 'COMPANY', 'STREET', 'CITY', 'STATE', 'POSTAL_CODE']:
                if tag == 'COMPANY':
                    entry['organization'] = element.text.strip() if element.text else ''
                else:
                    entry[tag.lower()] = element.text.strip() if element.text else ''
        # Bunch of if conditions that validate zip codes and deletes excess empty values created by above code
        if 'postal_code' in entry:
            entry['zip'] = entry.pop('postal_code').strip(' - ')
        if 'company' in entry and not entry['company']:
            del entry['company']
        if 'name' in entry and not entry['name']:
            del entry['name']
        if 'organization' in entry and not entry['organization']:
            del entry['organization']
        data.append(entry)
    return data



def handle_tsv(file_path):
    """This function parses .tsv file and returns data as a list of dictionaries"""
    data = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            # This gets individual data rows
            entry = {}
            for key, value in row.items():
                if key and value and value.strip() not in ['N/A','N/M/N','']:
                    key = key.strip().lower().replace(' ', '_')
                    if key == 'zip4' and entry.get('zip'):
                        entry['zip'] += f"-{value.strip()}"
                    elif key not in ['first', 'middle', 'last']:
                        entry[key] = value.strip()
                    elif key == 'last':
                        # This checks that if the organization name is N/A but the name is infact inside last name
                        if 'LLC' in value or 'Ltd' in value or 'Inc' in value:
                            entry['organization'] = value
                    else:
                        entry.setdefault('name', []).append(value.strip())
            if entry.get('name'):
                # Joins name:list (first + middle + last)
                entry['name'] = ' '.join(entry['name']).strip()
            data.append(entry)
    return data



def handle_txt(file_path):
    """This function parses .txt file and returns data as a list of dictionaries"""
    data = []
    with open(file_path, 'r') as file:
        entry = {}
        for line in file:
            line = line.strip()
            if line:
                # Assumes structure of the txt
                if not entry.get('name'):
                    entry['name'] = line
                elif 'street' not in entry:
                    entry['street'] = line
                elif 'city' not in entry and any(c.isdigit() for c in line):
                    # Runs when there exists numbers in the line
                    parts = line.split(', ')
                    city_state_zip = parts[-1].split(' ')
                    entry['city'] = ', '.join(parts[:-1])
                    entry['state'] = city_state_zip[0]
                    entry['zip'] = city_state_zip[-1].strip('-')
                elif 'county' not in entry and 'COUNTY' in line:
                    entry['county'] = line.replace(' COUNTY', '')
            else:
                if entry:
                    data.append(entry)
                entry = {}
        # To capture the last entry if the file does not end with a blank line
        if entry:
            data.append(entry)
    return data


def parse_file(file_path):
    """This function determinses the file type by its extension and then appropriately passes it to that function."""
    if file_path.endswith('.xml'):
        return handle_xml(file_path)
    elif file_path.endswith('.tsv'):
        return handle_tsv(file_path)
    elif file_path.endswith('.txt'):
        return handle_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")

def main(files):
    data = []
    for file_path in files:
        try:
            data.extend(parse_file(file_path))
        except Exception as e:
            sys.stderr.write(str(e) + '\n')
            sys.exit(1)

    # Sort data by ZIP code
    # print(json.dumps(data, indent=2))
    data_sorted = sorted(data, key=itemgetter('zip'))

    # Output the JSON data
    print(json.dumps(data_sorted, indent=4))
    sys.exit(0)    # Indicates success of the operation

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse and combine address data from multiple file formats.')
    parser.add_argument('files', nargs='+', help='File paths of the data files')
    args = parser.parse_args()
    
    if not args.files:
        sys.stderr.write("Error: No files provided.\n")
        sys.exit(1)

    main(args.files)
