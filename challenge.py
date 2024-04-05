import xml.etree.ElementTree as ET
import argparse
import json
import os
import sys
import csv


# Function to parse XML file
def parse_xml(file_path):
    try:
        # Load the XML file
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Define an empty list to store the dictionaries for each entity
        entities = []

        # Iterate over each <ENT> element in the XML
        for ent in root.findall('.//ENTITY/ENT'):
            # Define an empty dictionary for the current entity
            entity_dict = {}
            # Extract data from the <ENT> element and generate the dictionary
            if ent.find('NAME').text and ent.find('NAME').text != " ":
                entity_dict['name'] = ent.find('NAME').text.strip()
            else:
                entity_dict['organization'] = ent.find('COMPANY').text.strip()
            entity_dict['street'] = ent.find('STREET').text.strip()
            entity_dict['city'] = ent.find('CITY').text.strip()
            entity_dict['state'] = ent.find('STATE').text.strip()
            if ent.find('COUNTRY').text and ent.find('COUNTRY').text != " ":
                entity_dict['county'] = ent.find('COUNTRY').text.strip()
            entity_dict['zip'] = ent.find('POSTAL_CODE').text.strip()

            # Append the dictionary to the list of entities
            entities.append(entity_dict)

        return entities
    except Exception as e:
        print(f"Error parsing xml file '{file_path}': {e}", file=sys.stderr)

# Function to parse TSV file
def parse_tsv(file_path):
    try:
        with open(file_path, 'r', newline='') as file:
            reader = csv.DictReader(file, delimiter='\t')
            data = []
            
            for entry in reader:
                # Define an empty dictionary for the current entity
                each_entry = {}
                # Combine first , middle and last name
                name = " ".join([entry.get("first", ""), entry.get("middle", ""), entry.get("last", "")])
                if name:
                    each_entry['name'] = name
                else:
                    each_entry['organization'] = organization
                # Combine zip and zip4 fields and format name
                each_entry["street"] = entry.get("address", "")
                if entry.get("county", ""):
                    each_entry["county"] = entry["county"]
                each_entry["city"] = entry.get("city", "")
                each_entry["state"] = entry.get("state", "")
                each_entry["zip"] = entry.get('zip', '') + "-" + entry.get("zip4", "")
                data.append(each_entry)
            return data        
    except Exception as e:
        print(f"Error parsing TSV file '{file_path}': {e}", file=sys.stderr)
        

# Function to parse TXT file
def parse_txt(file_path):
    try:
        entries = []
        with open(file_path, 'r') as file:
            data = file.read()
            # Seperate records by new lines
            entry_data = data.split("\n\n")
            
            # Process each record and store in dict form
            for data in entry_data:
                lines = data.split("\n")
                i = 0
                if len(lines) > 1:
                    while i < len(lines):
                        entry = {}
                        
                        # Parse name or organization
                        name = lines[i].strip()
                        entry["name"] = name
                        i += 1
                        # Parse street
                        street = lines[i].strip()
                        entry["street"] = street
                        i += 1                        
                        # Parse county if present
                        if "COUNTY" in lines[i]:
                            county = lines[i].strip()
                            entry["county"] = county
                            i += 1                            
                            
                        # Parse city, state, and ZIP
                        city_state_zip = lines[i].strip()
                        city_state_zip_parts = city_state_zip.split(',')
                        city = city_state_zip_parts[0].strip()
                        entry["city"] = city
                        state_zip_parts = city_state_zip_parts[1].strip().split()
                        state = state_zip_parts[-2].strip()
                        entry["state"] = state
                        zip_code = state_zip_parts[-1].strip()
                        entry["zip"] = zip_code
                        i += 1
                        entries.append(entry)
        return entries
    except Exception as e:
        print(f"Error parsing txt file '{file_path}': {e}", file=sys.stderr)



# Function to parse input files
def parse_input_files(file_paths):
    data = []
    for file_path in file_paths:
        extension = os.path.splitext(file_path)[1].lower()
        if extension == '.xml':
            data.extend(parse_xml(file_path))
        elif extension == '.tsv':
            data.extend(parse_tsv(file_path))
        elif extension == '.txt':
            data.extend(parse_txt(file_path))
        else:
            print(f"Error: Unsupported file format for '{file_path}'", file=sys.stderr)
            sys.exit(1)
    return data

# Function to print JSON formatted entries sorted by ZIP code
def print_sorted_entries(entries):
    sorted_entries = sorted(entries, key=lambda x: x["zip"])
    return sorted_entries

def main():
    # Initializing ArgumentParser object with a description
    parser = argparse.ArgumentParser(description="Parse US names and entries from various file formats and output as JSON sorted by ZIP code.")
    # Define a positional argument for file paths, allowing multiple paths
    parser.add_argument("file_paths", nargs='+', help="List of file paths to input files")
    # Parsing the command-line arguments
    args = parser.parse_args()

    file_paths = args.file_paths
    
    # Checking if all provided paths are valid files
    if not all(os.path.isfile(file_path) for file_path in file_paths):
        print("Error: All arguments must be valid file paths.", file=sys.stderr)
        # Exit the program with 1 status code to indicate failure
        sys.exit(1)

    try:
        entries = parse_input_files(file_paths)
        # Sort data according to zip code
        sorted_data = print_sorted_entries(entries)
        print(json.dumps(sorted_data, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
