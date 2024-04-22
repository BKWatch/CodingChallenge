import json
import sys
import os
import csv
import xml.etree.ElementTree as ET
import argparse
import spacy


nlp = spacy.load('en_core_web_sm')

def is_person_or_organization(text):
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == 'PERSON':
            return 1
        elif ent.label_ == 'ORG':
            return 2
    return 0

def parse_xml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        addresses = []
        for elem in root.findall('.//ENT'):
            address = {
                'name': elem.find('NAME').text if elem.find('NAME')!="" else "",
                'organization': elem.find('COMPANY').text if elem.find('COMPANY')!="" else "",
                'street': elem.find('STREET').text,
                'city': elem.find('CITY').text,
                'state': elem.find('STATE').text,
                'zip': elem.find('POSTAL_CODE').text
            }
            addresses.append(address)
        return addresses
    except ET.ParseError: #handle error in parsing
        sys.stderr.write(f"Sorry, we could not parse XML file {file_path}\n, please check your file")
        return []


def parse_tsv(file_path):
    try:
        with open(file_path, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t') # read file into dictionaries
            addresses = []
            for row in reader:
                first = row['first'].strip()
                middle = None if row['middle'].strip() == 'N/M/N' else row['middle'].strip()
                last = row['last'].strip()
                name = ' '.join(filter(None, [first, middle, last]))
                if is_person_or_organization(name) == 2:
                    row['organization'] = name
                    name = ""
                if is_person_or_organization(name) == 1:
                    name = row['organization']
                    row["organization"] = ""
                output_row = {
                    'name': "" if name == "N/A" else name,
                    'organization': "" if row['organization'] == "N/A" else row['organization'],
                    'address': row['address'],
                    'city': row['city'],
                    'state': row['state'],
                    'county': row['county'],
                    'zip': f"{row['zip']} - {row['zip4']}" if 'zip4' in row and row['zip4'].strip() else row['zip'],
                    'zip4': row['zip4']
                }
                addresses.append(output_row)
            return addresses
    except csv.Error:
        sys.stderr.write(f"Sorry, we could not parse tsv file {file_path}\n, please check your file")
        return []


def parse_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            addresses = []
            address = []
            for line in file:
                record = line.strip()
                if record:
                    address.append(record)
                else:
                    if address:
                        addresses.append({
                            "name": address[0] if is_person_or_organization(address[0]) == 1 else "",
                            "organization": address[0] if is_person_or_organization(address[0]) == 2 else "",
                            "street": address[1],
                            "county": address[2] if len(address) == 4 else "",
                            "city": address[-1].split(",")[0],
                            "state": address[-1].split(" ")[1],
                            "zip": address[-1].split(" ")[2],
                        })
                        address = []
            return addresses
    except IOError:
        sys.stderr.write(f"Sorry, we could not parse txt file {file_path}\n, please check your file")
        return []

def remove_empty_fields(records):
    cleaned_records = []
    for record in records:
        cleaned_record = {key: value for key, value in record.items() if value.strip()}
        cleaned_records.append(cleaned_record)
    return cleaned_records

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse three types of files and store information.')
    parser.add_argument('files', metavar='FILE', type=str, nargs='+',
                        help='file format must be xml, tsv or txt')
    args = parser.parse_args()

    all_addresses = []
    for file_path in args.files:
        if not os.path.exists(file_path):
            sys.stderr.write(f"Sorry, the fail doesn't exist {file_path}\n")
            sys.exit(1)
        filename, ext = os.path.splitext(file_path)
        if ext.lower() == '.xml':
            all_addresses.extend(parse_xml(file_path))
        elif ext.lower() == '.tsv':
            all_addresses.extend(parse_tsv(file_path))
        elif ext.lower() == '.txt':
            all_addresses.extend(parse_txt(file_path))
        else:
            sys.stderr.write(f"The file {file_path}'s format is wrong, file format must be xml, tsv or txt\n")
            sys.exit(1)
    all_addresses = remove_empty_fields(all_addresses)
    sorted_addresses = sorted(all_addresses, key=lambda x: x['zip'])
    print(json.dumps(sorted_addresses))
    sys.exit(0)

