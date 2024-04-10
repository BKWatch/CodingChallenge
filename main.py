import json
import os
import sys
from csv import DictReader
from xml.etree import ElementTree as ET


def parse_xml(file_path):
    addresses = []
    tree = ET.parse(file_path)
    root = tree.getroot()
    for ent in root.findall('.//ENT'):
        name = ent.findtext('NAME', '').strip()
        company = ent.findtext('COMPANY', '').strip()
        street = ent.findtext('STREET', '').strip()
        city = ent.findtext('CITY', '').strip()
        state = ent.findtext('STATE', '').strip()
        postal_code = ent.findtext('POSTAL_CODE', '').strip()
        if postal_code.endswith('-'):
            postal_code = postal_code[:-1]
        addresses.append({
            'name': name if name else None,
            'organization': company if company else None,
            'street': street if street else None,
            'city': city if city else None,
            'state': state if state else None,
            'zip': postal_code if postal_code else None
        })
    return addresses


def parse_tsv(file_path):
    addresses = []
    with open(file_path, 'r', encoding='utf-8') as tsvfile:
        reader = DictReader(tsvfile, delimiter='\t')
        for row in reader:
            name = row.get('first', '').strip()
            street = row.get('address', '').strip()
            city = row.get('city', '').strip()
            state = row.get('state', '').strip()
            postal_code = row.get('zip', '').strip()
            if postal_code.endswith('-'):
                postal_code = postal_code[:-1]
            addresses.append({
                'name': name if name else None,
                'organization': None,
                'street': street if street else None,
                'city': city if city else None,
                'state': state if state else None,
                'zip': postal_code if postal_code else None
            })
    return addresses


def parse_txt(file_path):
    addresses = []
    with open(file_path, 'r', encoding='utf-8') as txtfile:
        lines = txtfile.readlines()
        for i in range(0, len(lines), 5):
            name = lines[i].strip()
            street = lines[i + 1].strip()
            city_state = lines[i + 2].strip().split(',')
            city = city_state[0].strip() if city_state else None
            state = city_state[1].strip() if len(city_state) > 1 else None
            postal_code = lines[i + 3].strip()
            if postal_code.endswith('-'):
                postal_code = postal_code[:-1]
            addresses.append({
                'name': name if name else None,
                'organization': None,
                'street': street if street else None,
                'city': city if city else None,
                'state': state if state else None,
                'zip': postal_code if postal_code else None
            })
    return addresses


def main():
    root_directory = os.path.abspath(os.path.dirname(__file__))

    xml_file = os.path.join(root_directory, 'input1.xml')
    tsv_file = os.path.join(root_directory, 'input2.tsv')
    txt_file = os.path.join(root_directory, 'input3.txt')

    addresses = []
    addresses.extend(parse_xml(xml_file))
    addresses.extend(parse_tsv(tsv_file))
    addresses.extend(parse_txt(txt_file))

    # Remove addresses with None values for 'zip'
    addresses = [address for address in addresses if address['zip'] is not None]

    # Sort addresses by ZIP code
    sorted_addresses = sorted(addresses, key=lambda x: x['zip'])

    json.dump(sorted_addresses, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
