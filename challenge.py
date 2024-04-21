import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
import csv
from collections import OrderedDict

# Clean the empty row
def clear_empty_data(data):
    keys_to_remove = [key for key, value in data.items() if value == ""]
    for key in keys_to_remove:
        del data[key]
    return data
    

# Parse the input files
def parse_xml(file_path):
    records = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

    except ET.ParseError as e:
        # Handle parsing errors
        print(f"Error parsing XML file {file_path}: {str(e)}\n")
        sys.exit(1)
    
    for ent in root.findall('.//ENT'):
        record = OrderedDict({"name": "" ,"organization": "","street": "", "city": "", "county": "", "state": "", "zip": "" })
        
        for element in ent:
            tag = element.tag

            if tag == "POSTAL_CODE":
                zipcode = element.text.replace(" ", "")

                if zipcode.endswith("-"):
                    record["zip"] = zipcode[:-1]

                else:
                    record["zip"] = zipcode

            elif tag == "COMPANY":
                if element.text.strip():
                    record["organization"] = element.text

            elif tag != "COUNTRY" and element.text.strip():
                record[tag.lower()] = element.text.strip()

        # remove tag with no value
        clear_empty_data(record)

        records.append(record)
    
    return records
def parse_tsv(file_path):
    records = []
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                
                record = OrderedDict({"name": "" ,"organization": "","street": "", "city": "", "county": "", "state": "", "zip": "" })
                
                # Organization is not N/A
                if row.get("organization").strip() != "N/A":
                    record["organization"] = row.get("organization").strip()

                # Organization is at "last"
                if row.get("last").strip() and not row.get("first").strip() and not row.get("middle").strip():
                    record["organization"] = row.get("last").strip()
                
                # No middle name
                if row.get("middle").strip() == "N/M/N":
                    record["name"] = row.get("first").strip() + " " + row.get("last").strip()
                
                elif row.get("last").strip() and row.get("first").strip() and row.get("middle").strip():
                    record["name"] = row.get("first").strip() + " " + row.get("middle").strip() + " " + row.get("last").strip(",")
                
                record["street"] = row.get("address").strip()
                record["city"] = row.get("city").strip()
                record["county"] = row.get("county").strip()
                record["state"] = row.get("state").strip()

                # Zip with zip4
                if row.get("zip4").strip():
                    record["zip"] = row.get("zip").strip() + "-" + row.get("zip4").strip()
                
                else:
                    record["zip"] = row.get("zip").strip()
                
                # remove tag with no value
                clear_empty_data(record)

                records.append(record)
            return records

    except Exception as e:
        print(f"Error parsing XML file {file_path}: {str(e)}\n")
        sys.exit(1)

def parse_txt(file_path):
    records = []
    try:
        with open(file_path, 'r') as f:
            entities = f.read().split("\n\n")

            for ent in entities:
                lines = ent.split("\n")
                
                record = {"name": "", "street": "", "city": "", "county": "", "state": "", "zip": ""}
                if len(lines) == 3:
                    record["name"] = lines[0].strip()
                    record["street"] = lines[1].strip()
                    record["city"] = lines[2].split(",")[0].strip()

                    # Special case for New Jersey
                    if len(lines[2].split(",")[1].strip().split()) == 3:
                        record["state"] = lines[2].split(",")[1].strip().split()[0] + " " + lines[2].split(",")[1].strip().split()[1]
                        record["zip"] = lines[2].split(",")[1].strip().split()[2].strip("-")
                    else:
                        record["state"] = lines[2].split(",")[1].strip().split()[0]
                        record["zip"] = lines[2].split(",")[1].strip().split()[1].strip("-")
                    
                    clear_empty_data(record)
                    records.append(record)

                elif len(lines) == 4:
                    record["name"] = lines[0].strip()
                    record["street"] = lines[1].strip()
                    record["county"] = lines[2].strip().split()[0]
                    record["city"] = lines[3].split(",")[0].strip()

                    # Special case for New Jersey
                    if len(lines[3].split(",")[1].strip().split()) == 3:
                        record["state"] = lines[3].split(",")[1].strip().split()[0] + " " + lines[2].split(",")[1].strip().split()[1]
                        record["zip"] = lines[3].split(",")[1].strip().split()[2].strip("-")
                    else:
                        record["state"] = lines[3].split(",")[1].strip().split()[0]
                        record["zip"] = lines[3].split(",")[1].strip().split()[1].strip("-")
                    
                    clear_empty_data(record)
                    records.append(record)
            return records
    except Exception as e:
        print(f"Error parsing XML file {file_path}: {str(e)}\n")
        sys.exit(1)

def parse_file(file_path):
    records = []
    _, ext = os.path.splitext(file_path)

    if ext == '.xml':
        records = parse_xml(file_path)
    elif ext == '.tsv':
        records = parse_tsv(file_path)
    elif ext == '.txt':
        records = parse_txt(file_path)
    else:
        print(f"Unsupported file extension: {ext}", file=sys.stderr)
        sys.exit(1)
    
    return records
        

def main():
    
    parser = argparse.ArgumentParser(description='Process files')
    parser.add_argument('files', metavar='F', type=str, nargs='+',
                        help='a list of files to be processed')
    args = parser.parse_args()

    records = []
    for file_path in args.files:
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist.", file=sys.stderr)
            sys.exit(1)
        records.extend(parse_file(file_path))
        
    # Sort with zip
    records.sort(key=lambda x: x['zip'])
    
    # Output in JSON format
    json_encoded_list = json.dumps(records, indent=4)
    print(json_encoded_list)
    sys.exit(0)

if __name__ == "__main__":
    main()