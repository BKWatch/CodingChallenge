import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict


def parse_xml(file_path):
    """
    Parse addresses from XML file.

    :param file_path: Path to the XML file.
    :return: List of OrderedDicts representing addresses.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    addresses = []
    for ent in root.findall('.//ENT'):  # Find all ENT elements under the root
        name = ent.find('NAME').text.strip() if ent.find('NAME') is not None else None
        org = ent.find('COMPANY').text.strip() if ent.find('COMPANY') is not None else None
        street = ent.find('STREET').text.strip() if ent.find('STREET') is not None else None
        city = ent.find('CITY').text.strip() if ent.find('CITY') is not None else None
        state = ent.find('STATE').text.strip() if ent.find('STATE') is not None else None
        zipcode = ent.find('POSTAL_CODE').text.strip() if ent.find('POSTAL_CODE') is not None else None
        zipcode = zipcode.strip().rstrip('-').strip()
        addresses.append(OrderedDict([
            ('name', name),
            ('organization', org),
            ('street', street),
            ('city', city),
            ('state', state),
            ('zip', zipcode)
        ]))
    return addresses

def parse_tsv(file_path):
    """
    Parse addresses from TSV file.

    :param file_path: Path to the TSV file.
    :return: List of OrderedDicts representing addresses.
    """
    addresses = []
    with open(file_path, 'r') as file:
        for line in file:
            fields = line.strip().split('\t')
            fields = line.split('\t')
            name = None
            org = None
            if fields[0]!='':
                if fields[1]!='N/M/N':
                    name = ' '.join([fields[0], fields[1], fields[2]]).strip()
                else:
                    name = ' '.join([fields[0], fields[2]]).strip()
            else:
                if fields[2]!='':
                    org = fields[2]
                else:
                    org = fields[3]
            street = fields[4]
            city = fields[5]
            state = fields[6]
            if fields[7]!='':
                county = fields[7]
            else:
                county = None
            zipcode = '-'.join([fields[8],fields[9]]).strip().rstrip('-')
            addresses.append(OrderedDict([
                ('name', name),
                ('organization', org),
                ('street', street),
                ('city', city),
                ('county', county),
                ('state', state),
                ('zip', zipcode)
            ]))
    return addresses


def parse_txt(file_path):
    """
    Parse addresses from TXT file.

    :param file_path: Path to the TXT file.
    :return: List of OrderedDicts representing addresses.
    """
    addresses = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
    groups = [group.split('\n') for group in ''.join(lines).split('\n\n')]
    result = [group for group in groups if any(line.strip() for line in group)]
    for record in result:
        try:
            name = record[0].strip()
            street = record[1].strip()
            if len(record) == 4:
                county = record[2].strip()
                city = record[3].split(',')[0].strip()
                zipcode = record[3].split(',')[1].split(' ')[-1].strip().rstrip('-')
                state = ' '.join(record[3].split(',')[1].split(' ')[:-1]).strip()
                org = None
            else:
                city = record[2].split(',')[0].strip()
                zipcode = record[2].split(',')[1].split(' ')[-1].strip().rstrip('-')
                state = ' '.join(record[2].split(',')[1].split(' ')[:-1]).strip()
                org = None
        except IndexError:
            print(f"Skipping malformed address at line {i + 1}", file=sys.stderr)
            continue
        addresses.append(OrderedDict([
            ('name', name),
            ('organization', org),
            ('street', street),
            ('city', city),
            ('county', county),
            ('state', state),
            ('zip', zipcode)
        ]))
    return addresses


def main():
    parser = argparse.ArgumentParser(description='Parse address files and output JSON.')
    parser.add_argument('files', nargs='+', help='Address files to parse')
    args = parser.parse_args()
    addresses = []
    for file_path in args.files:
        try:
            if file_path.endswith('.xml'):
                addresses.extend(parse_xml(file_path))
            elif file_path.endswith('.tsv'):
                addresses.extend(parse_tsv(file_path))
            elif file_path.endswith('.txt'):
                addresses.extend(parse_txt(file_path))
            else:
                print(f"Skipping unsupported file: {file_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}", file=sys.stderr)
            sys.exit(1)
    if addresses:
        sorted_addresses = sorted(addresses, key=lambda x: x['zip'])
        print(json.dumps(sorted_addresses, indent=2))
    else:
        print("No valid addresses found in input files.", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
