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

        street1 = ent.find("STREET").text.strip()
        street2 = ent.find("STREET_2").text.strip()
        street3 = ent.find("STREET_3").text.strip()
        if street1:
            street = street1
        if street2:
            street += ", " + street2
        if street3:
            street += ", " + street3

        city = ent.find("CITY").text.strip()
        state = ent.find("STATE").text.strip()

        postal_code = ""
        if ent.find("POSTAL_CODE").text.strip():
            post_ary = ent.find("POSTAL_CODE").text.split(" - ")
            postal_code = post_ary[0].strip()
            if len(post_ary) >= 2 and post_ary[1].strip():
                postal_code += "-" + post_ary[1].strip()

        if name:
            entity['name'] = name
        if company:
            entity['organization'] = company
        if street:
            entity['street'] = street
        if city:
            entity['city'] = city
        if state:
            entity['state'] = state
        if postal_code:
            entity['zip'] = postal_code
        entities.append(entity)
    return entities

def parse_tsv(file_path):
    entities = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            entity = {}
            if row['first']:
                if row['middle'] == 'N/M/N':
                    entity['name'] = f"{row['first']} {row['last']}".strip()
                else:
                    entity['name'] = f"{row['first']} {row['middle']} {row['last']}".strip()

            if row['organization'] != 'N/A':
                entity['organization'] = row['organization'].strip() 
            elif row['last'] and not row['first']:
                entity['organization'] = row['last']

            if row['address']:
                entity['street'] = row['address'].strip()
            if row['city']:
                entity['city'] = row['city'].strip()
            if row['county']:
                entity['county'] = row['county'].strip()
            if row['state']:
                entity['state'] = row['state'].strip()
            if row['zip']:
                entity['zip'] = row['zip'].strip()
                if row['zip4']:
                    entity['zip'] = entity['zip'] + "-" + row['zip4'].strip()
            entities.append(entity)
    return entities

def parse_txt(file_path):
    entities = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        content_no = 0
        county = ""
        entity = {}
        for line in lines:
            line = line.strip()

            if len(line) == 0:
                content_no = 0
                county = ""
                if entity != {}:
                    entities.append(entity)
                entity = {}
                continue
            if content_no == 0:
                entity['name'] = line
            elif content_no == 1:
                entity['street'] = line
            elif line.find('COUNTY') != -1:
                county = line.replace(" COUNTY", "")
            else:
                dot_pos = line.find(", ")
                space_pos = line.rfind(" ")
                entity['city'] = line[: dot_pos]
                if county:
                    entity['county'] = county
                entity['state'] = line[dot_pos + 2: space_pos]
                zip_code = line[space_pos + 1: ]
                if zip_code.rfind("-") == len(zip_code) - 1:
                    entity['zip'] = zip_code[0: len(zip_code) - 1]
                else:
                    entity['zip'] = zip_code

            content_no += 1
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