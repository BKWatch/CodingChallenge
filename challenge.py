import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET

# properities need to be put in the json
PROPERTIES = [
    "name",
    "organization",
    "street",
    "city",
    "county",
    "state",
    "zip"
]

# List with all the output Json
json_list = []

"""
func to parse xml file
"""

def parse_xml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # properity names for xml file
        property_name = ['name', 'company', 
                         'street', 'city', 'county', 'state', 'postal_code']
        
        # parse all entities
        for entity in root.findall('.//ENT'):
            name_or_organization = False
            entity_json = {}
            # find all elements containing 'street'
            streets = [element.text.strip() for element in entity
                                            if 'street' in element.tag.lower() 
                                            and element.text 
                                            and element.text.strip()]
            
            for i in range(len(property_name)):
                if property_name[i] == 'street':
                    # find all street tags
                    entity_json['street'] = ' '.join(streets)
                else:
                    element = entity.find(property_name[i].upper())
                    # json opject has a field if present
                    if element is not None and element.text and element.text.strip():
                        entity_json[PROPERTIES[i]] = element.text.strip()
            
            if entity_json:
                if not entity_json.get('name') and not entity_json.get('organization'):
                    # find entity without neither name nor organization
                    raise ValueError("Invalid format, " 
                                     "entity without neither name nor organization")
                
                if len(entity_json.keys()) < 5:
                    # JSON objects, each having 5 or 6 properties
                    raise ValueError("Invalid format, json with properties less than 5")
                
                json_list.append(entity_json)

    except FileNotFoundError:
        print(f"xml file not found: {file_path}")
        exit(1)
    except ET.ParseError as e:
        print(f"Error parsing XML file {file_path}: {e}, invalid xml format")
        exit(1)
    except Exception as e:
        print(f"Unexpected error when parsing XML file {file_path}: {e}, invalid xml format")
        exit(1)


"""
func to parse tsv file
"""

def parse_tsv(file_path):
    try:
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                # merge all name relate fields
                name_parts = [row['first'], row['middle'], row['last']]
                name = ' '.join(part 
                                for part in name_parts 
                                if part and part != 'N/M/N')

                # merge zip fields
                zip_code = f"{row['zip']}{'-' + row['zip4'] if row['zip4'] else ''}"

                # build json
                entity_json = {}
                for field in PROPERTIES:
                    # json opject has a field if present
                    if field in row and row[field].strip() and row[field] != 'N/A':
                        entity_json[field] = row[field].strip()
                    elif field == 'name' and name:
                        entity_json['name'] = name
                    elif field == 'zip' and zip_code:
                        entity_json['zip'] = zip_code
                    elif field == 'street' and row['address'].strip():
                        entity_json['street'] = row['address'].strip()

                if entity_json:
                    if not entity_json.get('name') and not entity_json.get('organization'):
                        # find entity without neither name nor organization
                        raise ValueError("Invalid format, " 
                                     "entity without neither name nor organization")

                    if len(entity_json.keys()) < 5:
                        # JSON objects, each having 5 or 6 properties
                        raise ValueError("Invalid format, json with properties less than 5")
                
                json_list.append(entity_json)
    except FileNotFoundError:
        print(f"TSV file not found: {file_path}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error when parsing TSV file {file_path}: {e}, invalid tsv format")
        exit(1)


"""
Func to parse txt file
"""
def parse_txt(file_path):
    try:
        with open(file_path, 'r') as file:
            text = file.read()

        # entities are divided by blank line
        entity_blocks = re.split(r'\n\s*\n', text.strip())

        for block in entity_blocks:
            lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
            if not lines:
                continue

            entity_json = {}
            county = None
            zip_line = ""
            entity_json['name'] = lines[0]
            entity_json['street'] = lines[1]

            # find out is line 3 county
            if 'COUNTY' in lines[2].upper():
                # line 3 is conuty
                countys = lines[2].split()
                county = countys[0]
                zip_line = lines[3]
            else:
                zip_line = lines[2]

            # parse rest part
            parts = zip_line.split(', ')
            entity_json['city'] = parts[0]
            if county is not None:
                # line 3 is county
                entity_json['county'] = county
            parts = parts[1].split()
            entity_json['state'] = ' '.join(parts[:-1])
            entity_json['zip'] = parts[-1]

            json_list.append(entity_json)
            
    except FileNotFoundError:
        print(f"txt file not found: {file_path}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error when parsing text file {file_path}: invalid txt format")
        exit(1)

def main():
    parser = argparse.ArgumentParser(description="BKWatch Challenge")
    parser.add_argument('--files', nargs='+', help='List of file paths, example: challenge.py --files input1.xml input2.tsv input3.txt')
    args = parser.parse_args()

    for file_path in args.files:
        if file_path.endswith('.xml'):
            parse_xml(file_path)
        elif file_path.endswith('.tsv'):
            parse_tsv(file_path)
        elif file_path.endswith('.txt'):
            parse_txt(file_path)
        else:
            raise ValueError("Unsupported file format")
    
    sorted_json = sorted(json_list, key=lambda x: x['zip'])
    print(json.dumps(sorted_json, indent=4))


if __name__ == "__main__":
    main()
    print("Parse success")
    exit(0)