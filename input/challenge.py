import argparse
import json
import sys
import xml.etree.ElementTree as ET

def parse_xml(file_path):
    entries = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for entry in root.findall('entry'):
            data = {
                'name': entry.findtext('name'),
                'organization': entry.findtext('organization'),
                'street': entry.findtext('street'),
                'city': entry.findtext('city'),
                'state': entry.findtext('state'),
                'zip': entry.findtext('zip'),
                'county': entry.findtext('county')
            }
            entries.append(data)
    except Exception as e:
        raise RuntimeError(f"Error parsing XML file '{file_path}': {e}")
    return entries

def parse_tsv(file_path):
    entries = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split('\t')
                data = {
                    'organization': parts[0],
                    'street': parts[1],
                    'city': parts[2],
                    'state': parts[3],
                    'zip': parts[4],
                    'county': parts[5] if len(parts) > 5 else None
                }
                entries.append(data)
    except Exception as e:
        raise RuntimeError(f"Error parsing TSV file '{file_path}': {e}")
    return entries

def parse_txt(file_path):
    entries = []
    try:
        with open(file_path, 'r') as file:
            lines = file.read().split('\n\n')
            for line in lines:
                parts = line.split('\n')
                if len(parts) < 4:
                    continue
                name_or_org = parts[0]
                street = parts[1]
                city_state_zip = parts[3].split(',')
                state_zip = city_state_zip[-1].strip().split(' ')
                data = {
                    'name': name_or_org if ',' not in name_or_org else None,
                    'organization': None if ',' not in name_or_org else name_or_org,
                    'street': street,
                    'city': city_state_zip[0],
                    'state': state_zip[0],
                    'zip': state_zip[-1],
                    'county': parts[2] if len(parts) > 4 else None
                }
                entries.append(data)
    except Exception as e:
        raise RuntimeError(f"Error parsing TXT file '{file_path}': {e}")
    return entries

def parse_files(file_paths):
    entries = []
    for file_path in file_paths:
        try:
            if file_path.endswith('.xml'):
                entries.extend(parse_xml(file_path))
            elif file_path.endswith('.tsv'):
                entries.extend(parse_tsv(file_path))
            elif file_path.endswith('.txt'):
                entries.extend(parse_txt(file_path))
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
        except Exception as e:
            sys.stderr.write(str(e) + '\n')
            sys.exit(1)
    return sorted(entries, key=lambda x: x['zip'])

def main():
    parser = argparse.ArgumentParser(description='Parse and combine address data from multiple files.')
    parser.add_argument('files', metavar='FILE', type=str, nargs='+', help='List of file paths to process')
    args = parser.parse_args()

    try:
        entries = parse_files(args.files)
        print(json.dumps(entries, indent=4))
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
