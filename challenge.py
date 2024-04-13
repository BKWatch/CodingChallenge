#!/usr/bin/env python3
import sys
import json
import csv
import xml.etree.ElementTree as ET
import argparse

def parse_xml(file_path):
    try:
        tree = ET.parse(file_path)
    except ET.ParseError as e:
        sys.stderr.write(f"XML parse error: {str(e)}\n")
        return []
    root = tree.getroot()
    addresses = []
    for element in root.findall('.//address'):
        data = {child.tag: child.text for child in element}
        if 'zip' in data:
            addresses.append(data)
    return addresses

def parse_tsv(file_path):
    try:
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            return [row for row in reader if 'zip' in row]
    except Exception as e:
        sys.stderr.write(f"TSV parse error: {str(e)}\n")
        return []

def parse_txt(file_path):
    addresses = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) < 5:
                    continue
                address = { 'name': parts[0], 'street': parts[1], 'city': parts[2], 'state': parts[3], 'zip': parts[4] }
                addresses.append(address)
    except Exception as e:
        sys.stderr.write(f"TXT parse error: {str(e)}\n")
        return []
    return addresses

def parse_files(file_paths):
    addresses = []
    for file_path in file_paths:
        if file_path.endswith('.xml'):
            addresses.extend(parse_xml(file_path))
        elif file_path.endswith('.tsv'):
            addresses.extend(parse_tsv(file_path))
        elif file_path.endswith('.txt'):
            addresses.extend(parse_txt(file_path))
        else:
            sys.stderr.write(f"Unsupported file format: {file_path}\n")
    return sorted(addresses, key=lambda x: x['zip'])

def main():
    parser = argparse.ArgumentParser(description="Parse address files and output JSON sorted by ZIP code.")
    parser.add_argument('files', nargs='+', help="List of file paths to parse")
    args = parser.parse_args()

    if not args.files:
        sys.stderr.write("No input files provided.\n")
        sys.exit(1)

    try:
        addresses = parse_files(args.files)
        print(json.dumps(addresses, indent=2))
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"An error occurred: {str(e)}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
