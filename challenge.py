import argparse
import json
import xml.etree.ElementTree as ET
import csv
import re
import sys

def parse_xml(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        entries = []
        
        for ent in root.findall('.//ENT'):
            name = ent.findtext('NAME', '').strip()
            organization = ent.findtext('COMPANY', '').strip()
            street = ent.findtext('STREET', '').strip()
            city = ent.findtext('CITY', '').strip()
            state = ent.findtext('STATE', '').strip()
            zip_code = ent.findtext('POSTAL_CODE', '').strip()
            
            entry = {
                "name": name,
                "organization": organization,
                "street": street,
                "city": city,
                "state": state,
                "zip": zip_code
            }
            
            entries.append(entry)
        
        return entries
    except Exception as e:
        raise ValueError(f"Failed to parse XML file '{filepath}': {e}")

def parse_tsv(filepath):
    try:
        entries = []

        with open(filepath, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')

            for row in reader:
                name = ' '.join(row[field].strip() for field in ['first', 'middle', 'last']).strip()
                organization = row['organization'].strip() if row['organization'] != 'N/A' else ''
                street = row['address'].strip()
                city = row['city'].strip()
                state = row['state'].strip()
                zip_code = row['zip'].strip()

                entry = {
                    "name": name,
                    "organization": organization,
                    "street": street,
                    "city": city,
                    "state": state,
                    "zip": zip_code
                }

                entries.append(entry)

        return entries
    except Exception as e:
        raise ValueError(f"Failed to parse TSV file '{filepath}': {e}")

def parse_txt(filepath):
    try:
        entries = []
        pattern = re.compile(r'^(.*),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)$')

        with open(filepath, 'r') as file:
            file_content = file.read().strip()
            entries_raw = file_content.split('\n\n')
            
            for entry_raw in entries_raw:
                lines = entry_raw.split('\n')
                name = lines[0].strip()
                street = lines[1].strip()
                match = pattern.match(lines[-1].strip())
                if match:
                    city, state, zip_code = match.groups()
                else:
                    raise ValueError(f"Error parsing TXT file '{filepath}': Unable to extract city, state, and ZIP from: {entry_raw}")
                
                entry = {
                    "name": name,
                    "organization": '',
                    "street": street,
                    "city": city,
                    "state": state,
                    "zip": zip_code
                }
                entries.append(entry)
        return entries

    except Exception as e:
        raise ValueError(f"Failed to parse TXT file '{filepath}': {e}")

def consolidate_and_sort(entries):
    return sorted(entries, key=lambda x: x['zip'])

def main():
    parser = argparse.ArgumentParser(description='Process some files.')
    parser.add_argument('xml_file', help='The XML file path')
    parser.add_argument('tsv_file', help='The TSV file path')
    parser.add_argument('txt_file', help='The TXT file path')

    args = parser.parse_args()

    try:
        xml_entries = parse_xml(args.xml_file)
        tsv_entries = parse_tsv(args.tsv_file)
        txt_entries = parse_txt(args.txt_file)
        
        all_entries = xml_entries + tsv_entries + txt_entries
        sorted_entries = consolidate_and_sort(all_entries)
        print(json.dumps(sorted_entries, indent=4))

    except ValueError as ve:
        sys.stderr.write(f"Error: {ve}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
