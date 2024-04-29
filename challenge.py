import sys
import json
import xml.etree.ElementTree as ET

def main():
    # Parse input files
    addresses = []
    for path in sys.argv[3:]:
        if path.endswith('.xml'):
            addresses.extend(parse_xml(path))
        elif path.endswith('.tsv'):
            addresses.extend(parse_tsv(path))
        elif path.endswith('.txt'):
            addresses.extend(parse_txt(path))
        else:
            print(f"Error: Unsupported file format for '{path}'", file=sys.stderr)
            sys.exit(1)

    # Sort addresses
    sort_addresses(addresses)

    # Print sorted addresses
    print_addresses(addresses)

def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    entities = []

    for ent in root.findall('./ENTITY/ENT'):
        name = ent.find('NAME').text.strip()
        company = ent.find('COMPANY').text.strip()
        street = ent.find('STREET').text.strip()
        city = ent.find('CITY').text.strip()
        state = ent.find('STATE').text.strip()
        postal_code = ent.find('POSTAL_CODE').text.strip()

        entity_data = {
            'name': name,
            'organization':company,
            'street': street,
            'city': city,
            'state': state,
            'zip': postal_code
        }

        entities.append(entity_data)

    return entities

def parse_tsv(file_path):
    result = []
    try:
        with open(file_path, 'r') as file:
            headers = next(file).strip().split('\t')
            for line in file:
                data = line.strip().split('\t')
                address = dict(zip(headers, data))
                
                # Check if any of the name fields (first, middle, last) are present, if not, skip the row
                if not any(address.get(field, '') for field in ['first', 'middle', 'last']):
                    continue
                
                # Check if LLC, Ltd., or Inc. is present in the last word of the last name and assign it to organization
                if 'last' in address and 'organization' not in address:
                    last_name_parts = address['last'].split()
                    if last_name_parts and any(suffix in last_name_parts[-1] for suffix in ['LLC', 'Ltd.', 'Inc.']):
                        address['organization'] = address['last']
                        address['last'] = ''
                
                # Construct the name using first, middle, and last name fields
                name_parts = [address.get(field, '') for field in ['first', 'middle', 'last'] if address.get(field, '')]
                address['name'] = ' '.join(name_parts)
                
                result.append(address)
        return result
    except FileNotFoundError:
        print(f"Error: File not found '{file_path}'", file=sys.stderr)
        sys.exit(1)

def parse_txt(file_path):
    result = []
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            address = {}
            current_key = None
            for line in lines:
                line = line.strip()
                if line:  # Non-empty line
                    if current_key is None:
                        address['name'] = line
                        current_key = 'street'
                    elif current_key == 'street':
                        address['street'] = line
                        current_key = 'city'
                    elif current_key == 'city':
                        parts = line.split(',')
                        if len(parts) > 1:
                            address['city'] = parts[0]
                            state_zip = parts[1].strip().split(' ')
                            address['state'] = state_zip[0]
                            address['zip'] = state_zip[1]
                        else:
                            address['city'] = line
                            current_key = 'state_zip'
                    elif current_key == 'state_zip':
                        state_zip = line.strip().split(' ')
                        address['state'] = state_zip[-2]
                        address['zip'] = state_zip[-1]
                        current_key = None
                else:  # Empty line indicates end of current address entry
                    result.append(address)
                    address = {}  # Reset address dictionary for next entry
                    current_key = None
            # Append the last address entry if any
            if address:
                result.append(address)
        return result
    except FileNotFoundError:
        print(f"Error: File not found '{file_path}'", file=sys.stderr)
        sys.exit(1)
        
def sort_addresses(addresses):
    # Define a custom sorting function
    def custom_sort(address):
        if 'zip' in address:
            return address['zip']
        else:
            return address.get('organization', '')  # Sort by organization name if zip is not available

    # Sort the addresses using the custom sorting function
    addresses.sort(key=custom_sort)
    
def print_addresses(addresses):
    formatted_addresses = []
    for address in addresses:
        formatted_address = {}
        if 'name' in address and address['name'] not in ('N/A', ' '):
            formatted_address['name'] = address['name']
        if 'organization' in address and address['organization'] not in ('N/A', ' '):
            formatted_address['organization'] = address['organization']
        if 'street' in address and address['street'] not in ('N/A', ' '):
            formatted_address['street'] = address['street']
        if 'city' in address and address['city'] not in ('N/A', ' '):
            formatted_address['city'] = address['city']
        if 'county' in address and address['county'] not in ('N/A', ' '):
            formatted_address['county'] = address['county']
        if 'state' in address and address['state'] not in ('N/A', ' '):
            formatted_address['state'] = address['state']
        if 'zip' in address and address['zip'] not in ('N/A', ' '):
            formatted_address['zip'] = address['zip']
        formatted_addresses.append(formatted_address)
    print(json.dumps(formatted_addresses, indent=2))

def print_help():
    help_text = """
    Usage: python challenge.py [OPTIONS] FILE1 [FILE2 ...]
    Options:
      --help            show this help message and exit
    """
    print(help_text)

if __name__ == '__main__':
    main()
