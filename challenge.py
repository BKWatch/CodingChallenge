import sys
import json
import xml.etree.ElementTree as ET
import csv

def parse_xml(file):
    addresses = []
    tree = ET.parse(file)
    root = tree.getroot()
    for ent in root.findall('.//ENTITY/ENT'):
        address = {}
        name = ent.find('NAME').text.strip()
        company = ent.find('COMPANY').text.strip()
        if name:
            address['name'] = name
        else:
            address['organization'] = company
        address['street'] = ent.find('STREET').text.strip()
        address['city'] = ent.find('CITY').text.strip()
        address['state'] = ent.find('STATE').text.strip()
        address['zip'] = ent.find('POSTAL_CODE').text.strip().split(' ')[0]
        county = ent.find('COUNTRY').text.strip()
        if county:
            address['county'] = county
        addresses.append(address)
        #print("addresses - > " + addresses)
    return addresses

def parse_csv(file):
    addresses = []
    with open(file, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            address = {}
            name = ' '.join([row['first'].strip(), row['middle'].strip(), row['last'].strip()])
            if name:
                address['name'] = name
            else:
                address['organization'] = row['organization'].strip()
            address['street'] = row['address'].strip()
            address['city'] = row['city'].strip()
            address['state'] = row['state'].strip()
            address['zip'] = row['zip'].strip().split('-')[0]
            county = row['county'].strip()
            if county:
                address['county'] = county
            addresses.append(address)
    return addresses

def parse_text(file):
    addresses = []
    with open(file, 'r') as textfile:
        lines = textfile.readlines()
        i = 0
        while i < len(lines):
            address = {}
            name = lines[i].strip()
            if name:
                address['name'] = name
            else:
                address['organization'] = lines[i+1].strip()
            address['street'] = lines[i+2].strip()
            address['city'] = lines[i+3].strip().split(',')[0]
            state_zip = lines[i+3].strip().split(',')[1].strip().split(' ')
            address['state'] = state_zip[-2]
            address['zip'] = state_zip[-1]
            county = lines[i+2].strip().split(',')[1].strip()
            if county:
                address['county'] = county
            addresses.append(address)
            i += 5
    return addresses

def main(files):

    all_addresses = []
    for file in files:
        if file.endswith('.xml'):
            print('file-> ' + file)
            all_addresses.extend(parse_xml(file))
        elif file.endswith('.tsv'):
            all_addresses.extend(parse_csv(file))
        # elif file.endswith('.txt'):
        #     all_addresses.extend(parse_text(file))
    all_addresses.sort(key=lambda x: x['zip'])
    print(json.dumps(all_addresses, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python challenge.py file1 file2 ...")
        sys.exit(1)
    main(sys.argv[1:])
