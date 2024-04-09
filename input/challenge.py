import argparse
import json
import os
import sys
import xml.etree.ElementTree as ETree
import csv

#Function to parse the XML file
def XML_parse(file_path):
    addresses = []
    try:
        tree = ETree.parse(file_path)
        root = tree.getroot()
        for record in root.findall('record'):
            address = {}
            for child in record:
                address[child.tag] = child.text.strip()
            addresses.append(address)
        return addresses
    except ETree.ParseError:
        sys.stderr.write(f"Error parsing XML file: {file_path}\n")
        return None

#Function to parse the TSV file
def TSV_parse(file_path):
    addresses = []
    try:
        with open(file_path, 'r', newline='') as tsvfile:
            reader = csv.DictReader(tsvfile, delimiter='\t')
            for row in reader:
                addresses.append(row)
        return addresses
    except csv.Error:
        sys.stderr.write(f"Error parsing TSV file: {file_path}\n")
        return None

#Function to parse the TXT file
def TXT_parse(file_path):
    addresses = []
    try:
        with open(file_path, 'r') as txtfile:
            for line_num, line in enumerate(txtfile, start=1):
                parts = line.strip().split(',')
                if len(parts) >= 4:
                    address = {
                        'name': parts[0].strip(),
                        'street': parts[1].strip(),
                        'city': parts[2].strip(),
                        'state': parts[3].strip()
                    }
                    if len(parts) >= 5:
                        address['zip'] = parts[4].strip()
                    if len(parts) == 6:
                        address['county'] = parts[5].strip()
                    addresses.append(address)
        return addresses
    except IOError:
        sys.stderr.write(f"Error reading TXT file: {file_path}\n")
        return None


#Function to parse given file
def FILE_parse(file_path):
    _, file_extension = os.path.splitext(file_path)
    if file_extension == '.xml':
        return XML_parse(file_path)
    elif file_extension == '.tsv':
        return TSV_parse(file_path)
    elif file_extension == '.txt':
        return TXT_parse(file_path)
    else:
        sys.stderr.write(f"Unsupported file format: {file_path}\n")
        return None

#Function to combine addresses
def combine_addresses(files):
    combined_addresses = []
    for file_path in files:
        addresses = FILE_parse(file_path)
        if addresses is None:
            return None
        combined_addresses.extend(addresses)
    return sorted(combined_addresses, key=lambda x: x.get('zip', ''))

#Main function to handle arguments and print JSON formatted addresses
def main():
    parser = argparse.ArgumentParser(description="Combine US addresses from files and output as JSON sorted by ZIP code.")
    parser.add_argument('files', metavar='FILE', nargs='+', help='input files containing addresses in various formats')
    
    args = parser.parse_args()

    addresses = combine_addresses(args.files)
    if addresses is None:
        sys.exit(1)
    
    print(json.dumps(addresses, indent=2))

if __name__ == "__main__":
    main()
