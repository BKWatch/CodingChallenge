import argparse
import json
import xml.etree.ElementTree as ET
import csv
import argparse
import re
import sys

def parse_xml(filepath):
    try:
        # Load the XML file and get the root element
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Initialize a list to hold all parsed entries
        entries = []
        
        # Iterate through each entry in the XML file
        for ent in root.findall('.//ENT'):
            # Extract required information from each entry
            name = ent.find('NAME').text if ent.find('NAME') is not None else ''
            organization = ent.find('COMPANY').text if ent.find('COMPANY') is not None else ''
            street = ent.find('STREET').text if ent.find('STREET') is not None else ''
            city = ent.find('CITY').text if ent.find('CITY') is not None else ''
            state = ent.find('STATE').text if ent.find('STATE') is not None else ''
            zip_code = ent.find('POSTAL_CODE').text.strip() if ent.find('POSTAL_CODE') is not None else ''
            
            # Consolidate the extracted data into a dictionary
            entry = {
                "name": name.strip(),
                "organization": organization.strip(),
                "street": street.strip(),
                "city": city.strip(),
                "state": state.strip(),
                "zip": zip_code
            }
            
            # Add the dictionary to the list of entries
            entries.append(entry)
        
        return entries
    except Exception as e:
        sys.stderr.write(f"Failed to parse XML: {e}\n")
        sys.exit(1)


def parse_tsv(filepath):
    try:
        entries = []  # Initialize a list to hold all parsed entries

        with open(filepath, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')

            for row in reader:
                # Extract and clean data for each entry
                name = f"{row['first'].strip()} {row['middle'].strip()} {row['last'].strip()}".strip()
                organization = row['organization'].strip() if row['organization'] != 'N/A' else ''
                street = row['address'].strip()
                city = row['city'].strip()
                state = row['state'].strip()
                zip_code = row['zip'].strip()

                # Create a dictionary for the entry
                entry = {
                    "name": name,
                    "organization": organization,
                    "street": street,
                    "city": city,
                    "state": state,
                    "zip": zip_code
                }

                # Add the entry to the list
                entries.append(entry)

        return entries
    except Exception as e:
        sys.stderr.write(f"Failed to parse TSV: {e}\n")
        sys.exit(1)

def parse_txt(filepath):
    try:
        entries = []  # Initialize a list to hold all parsed entries

        # Define a regular expression pattern to match city, state, and ZIP code
        pattern = re.compile(r'^(.*),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)$')

        with open(filepath, 'r') as file:
            # Split the file into entries based on double newlines
            file_content = file.read().strip()
            entries_raw = file_content.split('\n\n')
            
            for entry_raw in entries_raw:
                lines = entry_raw.split('\n')
                name = lines[0].strip()
                street = lines[1].strip()
                # Match the last line against the pattern to extract city, state, and ZIP
                match = pattern.match(lines[-1].strip())
                if match:
                    city, state, zip_code = match.groups()
                else:
                    # Handle cases where the pattern does not match
                    city, state, zip_code = ('', '', '')
                
                entry = {
                    "name": name,
                    "organization": '',  # Assume empty unless format specifies otherwise
                    "street": street,
                    "city": city,
                    "state": state,
                    "zip": zip_code
                }
                # Optionally, adjust for missing data or cleanup
                
                entries.append(entry)
        return entries

    except Exception as e:
        sys.stderr.write(f"Failed to parse TXT: {e}\n")
        sys.exit(1)


def consolidate_and_sort(entries):
    # Sort entries by ZIP code, accounting for ZIP+4 format
    return sorted(entries, key=lambda x: x['zip'])

def main():
    parser = argparse.ArgumentParser(description='Process some files.')
    parser.add_argument('xml_file', help='The XML file path')
    parser.add_argument('tsv_file', help='The TSV file path')
    parser.add_argument('txt_file', help='The TXT file path')

    args = parser.parse_args()

    xml_entries = parse_xml(args.xml_file)
    tsv_entries = parse_tsv(args.tsv_file)
    txt_entries = parse_txt(args.txt_file)
    
    # Continue with the consolidation, sorting, and JSON output as before
    
    all_entries = xml_entries + tsv_entries + txt_entries
    sorted_entries = consolidate_and_sort(all_entries)
    print(json.dumps(sorted_entries, indent=4))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"An error occurred: {e}\n")
        sys.exit(1)
    else:
        sys.exit(0)
