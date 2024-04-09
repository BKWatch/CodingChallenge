import xml.etree.ElementTree as ET
import csv
import sys
import json
import argparse

def format_zip(raw_zip):
    raw_zip = raw_zip.replace(' ', '').rstrip('-')
    if '-' in raw_zip or len(raw_zip) == 5:
        return raw_zip
    elif len(raw_zip) > 5:
        if '-' not in raw_zip:
            return raw_zip[:5] + '-' + raw_zip[5:]
        else:
            raw_zip
    else:
        sys.stderr.write(f"Incorrect zip formatting: {raw_zip}\n")
        sys.exit(1)

def parse_xml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        entities = []
        for ent in root.findall('.//ENTITY/ENT'):
            entity_dict = {}
            if ent.find('NAME').text and ent.find('NAME').text.strip():
                entity_dict['name'] = ent.find('NAME').text.strip()
            else:
                entity_dict['organization'] = ent.find('COMPANY').text.strip()
            entity_dict['street'] = ent.find('STREET').text.strip()
            entity_dict['city'] = ent.find('CITY').text.strip()
            entity_dict['state'] = ent.find('STATE').text.strip()
            if ent.find('COUNTRY').text and ent.find('COUNTRY').text.strip():
                entity_dict['county'] = ent.find('COUNTRY').text.strip()
            entity_dict['zip'] = format_zip(ent.find('POSTAL_CODE').text.strip())
            entities.append(entity_dict)
        return entities
    except Exception as e:
        sys.stderr.write(f"Error parsing XML file '{file_path}': {e}\n")
        return []

def parse_tsv(file_path):
    try:
        with open(file_path, 'r', newline='') as file:
            reader = csv.DictReader(file, delimiter='\t')
            data = []
            for entry in reader:
                each_entry = {}
                name = " ".join([entry.get("first", ""), entry.get("middle", ""), entry.get("last", "")]).strip()
                if name:
                    each_entry['name'] = name
                else:
                    each_entry['organization'] = entry.get("organization", "").strip()
                each_entry["street"] = entry.get("address", "").strip()
                if entry.get("county", "").strip():
                    each_entry["county"] = entry["county"].strip()
                each_entry["city"] = entry.get("city", "").strip()
                each_entry["state"] = entry.get("state", "").strip()
                each_entry["zip"] = format_zip(entry.get('zip', '').strip() + "-" + entry.get("zip4", "").strip())
                data.append(each_entry)
            return data
    except Exception as e:
        sys.stderr.write(f"Error parsing TSV file '{file_path}': {e}\n")
        return []

def parse_txt(file_path):
    try:
        with open(file_path, 'r') as file:
            data = file.read().split("\n\n")
            entries = []
            for entry_data in data:
                lines = entry_data.strip().split("\n")
                entry = {}
                if len(lines) >= 3:
                    entry['name'] = lines[0].strip()
                    entry['street'] = lines[1].strip()
                    city_state_zip = lines[-1].split(',')
                    entry['city'] = city_state_zip[0].strip()
                    state_zip = city_state_zip[1].strip().split()
                    entry['state'] = state_zip[0]
                    entry['zip'] = format_zip(state_zip[1])
                    if "COUNTY" in lines[2]:
                        entry['county'] = lines[2].split()[0]
                if entry:
                    entries.append(entry)
        return entries
    except Exception as e:
        sys.stderr.write(f"Error parsing TXT file '{file_path}': {e}\n")
        return []

def main():
    parser = argparse.ArgumentParser(description="Parse and combine addresses from different file formats.")
    parser.add_argument('files', nargs='+', help='file paths to parse')
    args = parser.parse_args()

    all_addresses = []
    for file_path in args.files:
        if file_path.endswith('.xml'):
            all_addresses.extend(parse_xml(file_path))
        elif file_path.endswith('.tsv'):
            all_addresses.extend(parse_tsv(file_path))
        elif file_path.endswith('.txt'):
            all_addresses.extend(parse_txt(file_path))
        else:
            sys.stderr.write(f"Error: Unsupported file format for {file_path}\n")

    if all_addresses:
        sorted_addresses = sorted(all_addresses, key=lambda x: x['zip'])
        print(json.dumps(sorted_addresses, indent=2))
    else:
        sys.stderr.write("No valid addresses found in input files.\n")
        sys.exit(1)

if __name__ == '__main__':
    sys.exit(main())