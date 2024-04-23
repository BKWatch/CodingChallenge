import csv
import sys
import xml.etree.ElementTree as ET
import json

def main():
    if "--help" in sys.argv:
        help()
    output_file_path = "output.json"
    if (len(sys.argv) > 1):
        for i in range(1,len(sys.argv)):
            filename = sys.argv[i]
            filename_components = filename.split(".", 1)
            if (len(filename_components) < 2):
                sys.stderr.write("Invalid file name detected: " + filename + ". Filename extension should be .xml, .tsv, or .txt")
                sys.exit(1)
            extension = filename_components[1]
            if extension == "xml":
                json_data = process_xml(sys.argv[i])
            elif extension == "tsv":
                json_data = process_tsv(sys.argv[i])
            elif extension == "txt":
                json_data = process_txt(sys.argv[i])
            else:
                sys.stderr.write("Invalid file extension detected: " + filename + ". Filename extension should be .xml, .tsv, or .txt, but was: " + extension)
                sys.exit(1)

            with open(output_file_path, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)

            sys.exit(0)
    else:
        sys.stderr.write("No file names specified. Please specify at least one file to be processed. Use option --help for more usage info.")
        sys.exit(1)

def help():
    print("Usage: python challenge.py [options] [arguments]")
    print("Options")
    print("\t--help\tShow this help message and exit\n\n")
    print("Arguments should be relative or absolute file paths to any combination of .xml, .tsv, and/or .txt files")
    sys.exit(0)

def process_xml(filepath):
    try:
        tree = ET.parse(filepath)
    except ET.ParseError:
        sys.stderr.write("Unable to parse XML file.")
        sys.exit(1)
        
    root = tree.getroot()

    if root.tag != 'EXPORT':
        sys.stderr.write("Error: Invalid XML format. Root tag must be 'EXPORT'.")
        sys.exit(1)

    data = []

    for ent in root.findall('ENTITY/ENT'):
        name = ent.find('NAME').text.strip()
        company = ent.find('COMPANY').text.strip()
        street_1 = ent.find('STREET').text.strip()
        street_2 = ent.find('STREET_2').text.strip()
        street_3 = ent.find('STREET_3').text.strip()
        city = ent.find('CITY').text.strip()
        state = ent.find('STATE').text.strip()
        zip_code = ent.find('POSTAL_CODE').text.strip().split(' - ')[0]

        street = ", ".join([street_1, street_2, street_3])

        if not (name and street and city and state and zip_code):
            sys.stderr.write("Error: Invalid XML format. Missing required fields.")
            sys.exit(1)

        person_data = {
            'name': name,
            'organization': company,
            'street': street,
            'city': city,
            'state': state,
            'zip': zip_code
        }
        data.append(person_data)

    return data

def process_tsv(filepath):
    data = []
    with open(filepath, 'r', newline='') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            # Extracting values from TSV columns
            first = row['first']
            middle = row['middle']
            last = row['last']
            name = f"{first} {''.join([f'{middle} ' if middle else ''])}{last}".strip()
            organization = row['organization']
            address = row['address']
            city = row['city']
            state = row['state']
            county = row['county']
            zip_code = row['zip']
            zip4 = row['zip4']

            full_zip = f"{zip_code}-{zip4}" if zip4 else zip_code


            if not (name and address and city and state and zip_code):
                sys.stderr.write("Error: Invalid TSV format. Missing required fields.")
                sys.exit(1)

            # Constructing data dictionary
            person_data = {
                'name': name,
                'organization': organization,
                'street': address,
                'city': city,
                'state': state,
                'county': county,
                'zip': full_zip
            }
            data.append(person_data)
    return data


def process_txt(filename):
    data = []
    with open(filename, 'r') as file:
        lines = file.readlines()
        entry = {}
        for line in lines:
            line = line.strip()
            if line:
                if 'name' not in entry:
                    entry['name'] = line
                elif 'street' not in entry:
                    entry['street'] = line
                elif 'county' not in entry:
                    parts = line.split(',')
                    if len(parts) == 3:
                        entry['city'], entry['state'], entry['zip'] = [part.strip() for part in parts]
                    else:
                        entry['county'] = line.strip()
                elif 'city' not in entry:
                    entry['city'] = line.split(',')[0].strip()
                elif 'state' not in entry:
                    entry['state'] = line.split(',')[1].strip()
                elif 'zip' not in entry:
                    entry['zip'] = line.split(',')[2].strip()
            else:
                if entry: # Don't include empty lines at the start as blank dictionaries.
                    if not (entry['name'] and entry['street'] and entry['city'] and entry['state'] and entry['zip_code']):
                        sys.stderr.write("Error: Invalid XML format. Missing required fields.")
                        sys.exit(1)
                    data.append(entry)
                entry = {}
    return data


if __name__ == "__main__":
    main()
