import json
import sys
import os
import xml.etree.ElementTree as ET
import csv

def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    entities = []
    for ent in root.findall(".//ENT"):
        entity = {}
        name = ent.find("NAME").text.strip()
        company = ent.find("COMPANY").text.strip()
        entity['name'] = name if name else None
        entity['organization'] = company if company else None
        entity['street'] = ent.find("STREET").text.strip()
        entity['city'] = ent.find("CITY").text.strip()
        entity['state'] = ent.find("STATE").text.strip()
        entity['zip'] = ent.find("POSTAL_CODE").text.strip().split(" - ")[0]
        entities.append(entity)
    return entities

def parse_tsv(file_path):
    entities = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            entity = {}
            entity['name'] = f"{row['first']} {row['middle']} {row['last']}".strip() if row['first'] else None
            entity['organization'] = row['organization'].strip() if row['organization'] != 'N/A' else None
            entity['street'] = row['address'].strip()
            entity['city'] = row['city'].strip()
            entity['state'] = row['state'].strip()
            entity['zip'] = row['zip'].strip()
            entities.append(entity)
    return entities

def parse_txt(file_path):
    entities = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            parts = line.strip().split(', ')
            if len(parts) < 6:
                print(f"Warning: Skipping malformed line: {line.strip()}", file=sys.stderr)
                continue
            entity = {}
            entity['name'] = parts[0] if parts[0] != 'N/A' else None
            entity['organization'] = parts[1] if parts[1] != 'N/A' else None
            entity['street'] = parts[2]
            entity['city'] = parts[3]
            entity['state'] = parts[4]
            entity['zip'] = parts[5].split(' - ')[0]
            entities.append(entity)
    return entities

def main():
    if '--help' in sys.argv:
        print("Usage: python challenge.py <file1> <file2> ... <fileN>")
        sys.exit(0)

    input_files = sys.argv[1:]
    if not input_files:
        print("Error: No input files provided", file=sys.stderr)
        sys.exit(1)

    all_entities = []
    for file_path in input_files:
        if not os.path.isfile(file_path):
            print(f"Error: File not found - {file_path}", file=sys.stderr)
            sys.exit(1)
        
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.xml':
            all_entities.extend(parse_xml(file_path))
        elif file_extension == '.tsv':
            all_entities.extend(parse_tsv(file_path))
        elif file_extension == '.txt':
            all_entities.extend(parse_txt(file_path))
        else:
            print(f"Error: Unsupported file format - {file_path}", file=sys.stderr)
            sys.exit(1)

    sorted_entities = sorted(all_entities, key=lambda x: x['zip'])
    print(json.dumps(sorted_entities, indent=2))

if __name__ == '__main__':
    main()