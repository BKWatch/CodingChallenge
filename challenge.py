import argparse
import json
import csv
import sys
import os
import zipfile
from xml.etree import ElementTree as ET

def parse_xml(file_path):
    """ Parse XML files to extract address information. """
    try:
        tree = ET.parse(file_path)
    except ET.ParseError:
        raise ValueError("Invalid XML format.")
    root = tree.getroot()
    addresses = []
    for ent in root.findall('.//ENT'):
        name = ent.find('NAME').text.strip() if ent.find('NAME') is not None and ent.find('NAME').text.strip() else None
        company = ent.find('COMPANY').text.strip() if ent.find('COMPANY') is not None and ent.find('COMPANY').text.strip() else None
        addresses.append({
            "name": name,
            "organization": company,
            "street": ent.find('STREET').text,
            "city": ent.find('CITY').text,
            "state": ent.find('STATE').text,
            "zip": ent.find('POSTAL_CODE').text.strip('- ').strip()
        })
    return addresses

def parse_tsv(file_path):
    """ Parse TSV files to extract address information. """
    addresses = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter='\t', fieldnames=["first", "middle", "last", "organization", "street", "city", "state", "county", "zip", "zip4"])
        for row in reader:
            name = ' '.join(filter(None, [row['first'], row['middle'], row['last']])).strip()
            zip_code = row['zip'] + ('-' + row['zip4'].strip() if row['zip4'].strip() else '')
            addresses.append({
                "name": name if name else None,
                "organization": row['organization'].strip() if row['organization'].strip() else None,
                "street": row['street'],
                "city": row['city'],
                "state": row['state'],
                "zip": zip_code
            })
    return addresses

def parse_txt(file_path):
    """ Parse TXT files to extract address information. """
    addresses = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():
                fields = line.strip().split(',')
                addresses.append({
                    "name": fields[0].strip(),
                    "street": fields[1].strip(),
                    "city": fields[3].strip(),
                    "state": fields[4].strip().split(' ')[0],
                    "zip": fields[4].strip().split(' ')[1]
                })
    return addresses

def process_files(file_paths):
    """ Process each file and gather all addresses into a sorted list. """
    combined_addresses = []
    for path in file_paths:
        if not os.path.exists(path):
            sys.stderr.write(f"Error: File not found {path}\n")
            sys.exit(1)
        extension = path.split('.')[-1]
        if extension not in ['xml', 'tsv', 'txt']:
            sys.stderr.write(f"Error: Unsupported file type {extension}\n")
            sys.exit(1)
        try:
            if extension == 'xml':
                combined_addresses.extend(parse_xml(path))
            elif extension == 'tsv':
                combined_addresses.extend(parse_tsv(path))
            elif extension == 'txt':
                combined_addresses.extend(parse_txt(path))
        except Exception as e:
            sys.stderr.write(f"Error processing file {path}: {str(e)}\n")
            sys.exit(1)
    return sorted(combined_addresses, key=lambda x: x['zip'])


def main():
    """ Main function to handle command line arguments and initiate processing. """
    description = (
        "Processes multiple address files (XML, TSV, TXT) and outputs a sorted JSON in a ZIP archive. "
        "Each file should contain address information. The output JSON will be sorted by postal codes."
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        'files', nargs='+', help='List of file paths to process. At least one file must be specified.'
    )
    args = parser.parse_args()

    if not args.files:
        parser.error("No files provided. Please specify at least one file to process.")

    try:
        addresses = process_files(args.files)
        if addresses:
            # Create a JSON file from the processed addresses
            json_filename = 'addresses.json'
            with open(json_filename, 'w') as json_file:
                json.dump(addresses, json_file, indent=2)

            # Pack the JSON file into a ZIP archive
            zip_filename = 'addresses.zip'
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.write(json_filename, os.path.basename(json_filename))

            # Clean up the JSON file after zipping
            os.remove(json_filename)

            # Print a message to indicate successful processing
            print(f"Processed data has been packed into {zip_filename}")
    except Exception as e:
        sys.stderr.write(f"An error occurred: {str(e)}\n")
        sys.exit(1)

    # Return success status code
    sys.exit(0)

if __name__ == "__main__":
    main()