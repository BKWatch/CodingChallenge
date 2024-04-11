# furkhan mehdi syed 
import json,os,sys,csv
import logging
import xml.etree.ElementTree as ET


def parse_xml_file(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    addresses = []

    for person in root.findall('person'):
        address = {}
        address['name'] = person.findtext('name')
        address['street'] = person.findtext('street')
        address['city'] = person.findtext('city')
        address['county'] = person.findtext('county')
        address['state'] = person.findtext('state')
        address['zip'] = person.findtext('zip')

        addresses.append(address)

    return addresses


def parse_tsv_file(file_path):
    addresses = []

    with open(file_path, 'r') as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter='\t')
        for row in reader:
            address = {}
            address['name'] = row['name']
            address['organization'] = row['organization']
            address['street'] = row['street']
            address['city'] = row['city']
            address['state'] = row['state']
            address['zip'] = row['zip']

            addresses.append(address)

    return addresses


def parse_txt_file(file_path):
    addresses = []

    with open(file_path, 'r') as txt_file:
        lines = txt_file.readlines()
        for line in lines:
            parts = line.split(',')
            if len(parts) == 6 or len(parts) == 7:
                address = {}
                address['name'] = parts[0]
                address['street'] = parts[1]
                address['city'] = parts[2]
                address['county'] = parts[3]
                address['state'] = parts[4]
                address['zip'] = parts[5].strip()

                addresses.append(address)

    return addresses


def parse_files(file_paths):
    addresses = []

    for file_path in file_paths:
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.xml':
            addresses.extend(parse_xml_file(file_path))
        elif file_extension == '.tsv':
            addresses.extend(parse_tsv_file(file_path))
        elif file_extension == '.txt':
            addresses.extend(parse_txt_file(file_path))
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

    return addresses


def validate_addresses(addresses):
    for address in addresses:
        if 'name' not in address and 'organization' not in address:
            raise ValueError("Invalid address: Missing name or organization")
        if 'street' not in address:
            raise ValueError("Invalid address: Missing street")
        if 'city' not in address:
            raise ValueError("Invalid address: Missing city")
        if 'state' not in address:
            raise ValueError("Invalid address: Missing state")
        if 'zip' not in address:
            raise ValueError("Invalid address: Missing zip")

    return True


def sort_addresses_by_zip(addresses):
    return sorted(addresses, key=lambda x: x['zip'])


def setup_logging():
    log_file = 'challenge.log'
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)


def main(file_paths):
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        addresses = parse_files(file_paths)
        validate_addresses(addresses)
        sorted_addresses = sort_addresses_by_zip(addresses)
        print(json.dumps(sorted_addresses, indent=2))
        logger.info('Address parsing and sorting completed successfully')
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    # Extract command-line arguments excluding the script name
    file_paths = sys.argv[1:]
    main(file_paths)