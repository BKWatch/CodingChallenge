import sys
import json
import xml.etree.ElementTree as ET
import csv


def parse_xml(file_path):
    addresses = []
    tree = ET.parse(file_path)
    root = tree.getroot()
    for entity in root.findall('ENTITY/ENT'):
        address_info = {}
        name = entity.find('NAME').text.strip()
        company = entity.find('COMPANY').text.strip()
        street = entity.find('STREET').text.strip()
        city = entity.find('CITY').text.strip()
        state = entity.find('STATE').text.strip()
        postal_code = entity.find('POSTAL_CODE').text.strip()
        if name:
            address_info['name'] = name
        if company:
            address_info['organization'] = company
        address_info['street'] = street
        address_info['city'] = city
        address_info['state'] = state
        if postal_code:
            if "-" in postal_code:
                zip_parts = postal_code.split("-")
                if len(zip_parts[1]) > 3:
                    address_info['zip'] = postal_code.strip()
                else:
                    address_info['zip'] = zip_parts[0].strip()
            else:
                address_info['zip'] = postal_code
        addresses.append(address_info)
    return addresses


def parse_tsv(file_path):
    addresses = []
    with open(file_path, 'r', newline='') as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter='\t')
        for row in reader:
            address = {}
            name = row['first'] + (' ' + row['middle'] if row['middle'] != 'N/M/N' else '') + ' ' + row['last']
            if name.strip() != "":
                address['name'] = name.strip()
            organization = row['organization']
            if organization.strip() != "N/A":
                address['organization'] = organization.strip()
            address['street'] = row['address'].strip()
            address['city'] = row['city'].strip()
            address['state'] = row['state'].strip()
            county = row['county']
            if county.strip():
                address['county'] = county.strip()
            zip_code = row['zip'][:5]
            if zip_code.strip() != "":
                if row['zip4'].strip():
                    address['zip'] = zip_code.strip() + '-' + row['zip4'].strip()
                else:
                    address['zip'] = zip_code.strip()
            addresses.append(address)
    return addresses


def parse_txt(file_path):
    addresses = []
    with open(file_path, 'r') as txtfile:
        lines = txtfile.readlines()
        i = 0
        segments = []
        current_segment = []
        for line in lines:
            if line.strip() == '':
                if current_segment:
                    segments.append(current_segment)
                    current_segment = []
            else:
                current_segment.append(line.strip())
        if current_segment:
            segments.append(current_segment)
        for segment in segments:
            address = {}
            if len(segment) == 4:
                address['name'] = segment[0].strip()
                address['street'] = segment[1].strip()
                address['County'] = segment[2].strip()
                address['city'] = segment[3].strip().split(",")[0]
                address['State'] = segment[3].strip().split(",")[1].split(" ")[1]
                address['zip'] = segment[3].strip().split(",")[1].split(" ")[2]
                addresses.append(address)
            else:
                address['name'] = segment[0].strip()
                address['street'] = segment[1].strip()
                address['city'] = segment[2].strip().split(",")[0]
                address['State'] = segment[2].strip().split(",")[1].split(" ")[1]
                address['zip'] = segment[2].strip().split(",")[1].split(" ")[2]
                addresses.append(address)
    return addresses


def parse_file(file_path):
    if file_path.endswith('.xml'):
        return parse_xml(file_path)
    elif file_path.endswith('.tsv'):
        return parse_tsv(file_path)
    elif file_path.endswith('.txt'):
        return parse_txt(file_path)
    else:
        print(f"Unsupported file format: {file_path}", file=sys.stderr)
        return []


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--help":
        print("Usage: python challenge.py file1 file2 ...", file=sys.stderr)
        sys.exit(1)

    combined_addresses = []
    for file_path in sys.argv[1:]:
        try:
            addresses = parse_file(file_path)
            combined_addresses.extend(addresses)
        except Exception as e:
            print(f"Error parsing file '{file_path}': {e}", file=sys.stderr)
            sys.exit(1)

    if combined_addresses:
        combined_addresses.sort(key=lambda x: x.get('zip', ''))
        print(json.dumps(combined_addresses, indent=2))
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

