import json
import sys
import xml.etree.ElementTree as ET
import csv

def parse_xml(file_path):
    """Parses xml files and returns list of addresses"""
    with open(file_path, 'r', encoding='Latin-1') as file:
        tree = ET.parse(file)
        root = tree.getroot()

        address_list = []
        for ent in root.findall('.//ENT'):
            address = {}

            name = ent.find('NAME').text if ent.find('NAME') is not None else None
            company = ent.find('COMPANY').text if ent.find('COMPANY') is not None else None
            street = ent.find('STREET').text if ent.find('STREET') is not None else None
            city = ent.find('CITY').text if ent.find('CITY') is not None else None
            state = ent.find('STATE').text if ent.find('STATE') is not None else None
            zip = ent.find('POSTAL_CODE').text if ent.find('POSTAL_CODE') is not None else None

            if name.strip():
                address['name'] = ' '.join(name.split())
            if company.strip():
                address['organization'] = company.strip()
            if street.strip():
                address['street'] = street.strip()
            if city.strip():
                address['city'] = city.strip()
            if state.strip():
                address['state'] = state.strip()
            if zip.strip():
                if zip.strip()[-1] == "-":
                    address['zip'] = zip.strip()[:-1].strip()
                elif " - " in zip.strip():
                    address['zip'] = zip.strip().replace(" - ", "-")
                else:
                    address['zip'] = zip.strip()
            
            address_list.append(address)
    return address_list

def parse_tsv(file_path):
    """Parses tsv files and returns list of addresses"""
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter='\t')
        address_list = []
        for row in reader:
            address = {}
            if row['first'] or row['middle'] or row['last']:
                if row['middle'] == "N/M/N":
                    name_parts = [row['first'], row['last']]    
                else:
                    name_parts = [row['first'], row['middle'], row['last']]
                address['name'] = ' '.join(filter(None, name_parts))
            if row['organization'].strip() and row['organization'] != "N/A":
                address['organization'] = row['organization']
            if row['address'].strip():
                address['street'] = row['address']
            if row['city'].strip():
                address['city'] = row['city']
            if row['county'].strip():
                address['county'] = row['county']
            if row['state'].strip():
                address['state'] = row['state']
            if row['zip'].strip():
                address['zip'] = f"{row['zip']}-{row['zip4']}" if row['zip4'] else row['zip']
            address_list.append(address)
    return address_list

def parse_txt(file_path):
    """Parses tsv files and returns list of addresses"""
    with open(file_path, 'r') as file:
        entries = file.read().split('\n\n')
        address_list = []
        for entry in entries:
            if entry.strip():
                lines = entry.strip().split('\n')
                address = {}

                address['name'] = lines[0].strip()
                address['street'] = lines[1].strip()
                if 'COUNTY' in lines[2]:
                    address['city'] = lines[3].split(',')[0].strip()
                    address['county'] = lines[2].replace('COUNTY', '').strip()
                    
                    state_parts = lines[3].split(',')[1].strip()
                    address['state'] = state_parts.split(' ')[0].strip()
                    address['zip'] = state_parts.split(' ')[1].strip()
                else:
                    address['city'] = lines[2].split(',')[0].strip()

                    state_parts = lines[2].split(',')[1].strip()
                    state = state_parts.split(' ')[0:-1]
                    address['state'] = " ".join(state).strip()
                    zip = address['zip'] = state_parts.split(' ')[-1].strip()
                    if zip.strip()[-1] == "-":
                        address['zip'] = zip.strip()[:-1]
                    elif " - " in zip.strip():
                        address['zip'] = zip.strip().replace(" - ", "-")
                    else:
                        address['zip'] = zip.strip()
            
                address_list.append(address)
    return address_list

def parse_file(file_path):
    """Checks for errors in argument list"""
    if file_path.endswith(".xml"):
        return parse_xml(file_path)
    elif file_path.endswith(".tsv"):
        return parse_tsv(file_path)
    elif file_path.endswith(".txt"):
        return parse_txt(file_path)
    else:
        raise ValueError(f'File format is unsupported: {file_path}')

def parse_all_files(file_paths):
    """Loops over all files in input, prints an error during parsing"""
    all_addresses = []
    for file_path in file_paths:
        try:
            all_addresses.extend(parse_file(file_path))
        except Exception as e:
            sys.stderr.write(f"Error parsing file {file_path}: {str(e)}\n")
            sys.exit(1)

    return all_addresses

def main():
    """Main function"""
    file_paths = sys.argv[1:]
    addresses = parse_all_files(file_paths)
    addresses.sort(key=lambda x: x['zip'])
    print(json.dumps(addresses, indent=2))
    sys.exit(0)

if __name__ == "__main__":
    main()