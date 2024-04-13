# Importing relevant libraries
import os
import sys
import json
import xml.etree.ElementTree as ET
from collections import OrderedDict

def xml_to_json(xmldata):
    # Creating root for XML data
    root = ET.fromstring(xmldata)
    entities = []

    # Dealing with each entity, creating a dictionary and converting it to JSON
    for ent in root.findall('.//ENTITY/ENT'):
        entity = {}
        for elem in ent:
            if elem.text.strip():
                if elem.tag == 'NAME':
                    entity['name'] = elem.text.strip()
                elif elem.tag == 'COMPANY':
                    entity['organization'] = elem.text.strip()
                elif elem.tag == 'STREET':
                    entity['street'] = elem.text.strip()
                elif elem.tag == 'CITY':
                    entity['city'] = elem.text.strip()
                elif elem.tag == 'STATE':
                    entity['state'] = elem.text.strip()
                elif elem.tag == 'POSTAL_CODE':
                    entity['zip'] = elem.text.strip()
                    if (entity['zip'][-1]=='-'):
                        entity['zip'] = entity['zip'][:-1]
                    if (entity['zip'][-1]==' '):
                        entity['zip'] = entity['zip'][:-1]
        entities.append(entity)
    
    return entities

# Helper function for dictionary reorganization in tsv data
def reorder_dictionary(dictionary, key):
    #Reorder the dictionary with the specified key moved to the front.
    ordered_dict = OrderedDict([(key, dictionary[key])])
    for k, v in dictionary.items():
        if k != key:
            ordered_dict[k] = v
    return ordered_dict

def tsv_to_json(data):
    details = []
    headers = ["first", "middle", "last", "organization","address", "city", "state", "county", "zip", "zip4"]

    for line in data:
        if line[:5] == "first":
            continue
        fields = line.split('\t')
        #print(fields)
        current_entry = {}

        # Iterate through each field and add it to the current entry
        for index, field in enumerate(fields):
            current_entry[headers[index]] = field.strip()

        # Remove empty or N/A fields
        current_entry = {k: v for k, v in current_entry.items() if v and v != 'N/A'}

        # Cleaning and reogranizing entries
        if 'middle' in current_entry and current_entry['middle'] == 'N/M/N':
            del current_entry['middle']
        if 'first' not in current_entry and 'last' in current_entry:
            current_entry['organization'] = current_entry['last']
            current_entry = reorder_dictionary(current_entry, "organization")
            del current_entry['last']
        if 'zip4' in current_entry:
            current_entry['zip'] += ('-'+current_entry['zip4'])
            del current_entry['zip4']

        # Append the current entry to the list of details
        details.append(current_entry)

    return details

def txt_to_json(data):
    details = []
    current = {}
    count = 1

    for entry in data:
        entry = entry.strip()

        if len(entry)!=0:
            if (count==1):
                current['name'] = entry
            if (count==2):
                current['street'] = entry
            if (count==3):
                if (entry[-6:] == 'COUNTY'):
                    county = entry.split()
                    current['county'] = county[0]
                else:
                    count+=1
            if(count==4):
                city, state = entry.split(', ')
                current['city'] = city
                state, pin = state.split(" ", 1)
                current['state'] = state
                if pin[-1]=='-':
                    pin = pin[:-1]
                current['zip'] = pin
            count+=1
        else:
            if current:
                details.append(current)
                current = {}
            count = 1
    if current:
        details.append(current)
    
    return details

def main():
    # Check for --help option
    if len(sys.argv) == 2 and sys.argv[1] == '--help':
        print("Usage: python3 challenge.py [file_name.file_extension]")
        sys.exit(0)

    # Check for errors in the argument list
    if len(sys.argv) < 2:
        print("Error: No files provided.")
        sys.exit(1)

    addresses = []

    # Iterate over each file provided
    for file_path in sys.argv[1:]:
        #print("Processing " + file_path)
        file_name, file_extension = os.path.splitext(file_path)
        file_path = os.path.join('input', file_path)

        # Check if the file exists
        if not os.path.isfile(file_path):
            print(f"Error: File '{file_path}' not found.")
            sys.exit(1)

        # Read the content of the file based on its extension and convert to JSON
        with open(file_path, "r") as f:
            data = f.readlines()
        
        if file_extension == '.xml':
            addresses.extend(xml_to_json(''.join(data)))
        elif file_extension == '.tsv':
            addresses.extend(tsv_to_json(data))
        elif file_extension == '.txt':
            addresses.extend(txt_to_json(data))
        else:
            print(f"Error: Unsupported file format '{file_extension}'.")
            sys.exit(1)

    # Sort addresses by ZIP code in ascending order
    addresses.sort(key=lambda x: x['zip'][:5])

    # Output the addresses as pretty-printed JSON array to stdout
    print(json.dumps(addresses, indent=4))

if __name__ == "__main__":
    main()
