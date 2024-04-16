# Copyright Shane H Rhoads 2024, All Rights Reserved
# Created for BankruptcyWatch Coding Challenge https://github.com/BKWatch/CodingChallenge
# NOT TO BE USED, MODIFIED, OR REDISTRUBTED FOR COMMERICAL OR NON-COMMERICAL PURPOSES
# NOT TO BE USED AS TRAINING DATA FOR AI OR ML SYSTEMS

import sys, os, json, csv
import xml.etree.ElementTree as ET

def load_arguments():
    if len(sys.argv) < 2:
        raise ValueError("Please specify at least 1 file to read")

    if (sys.argv[1] == '--help'):
        print(f"Script for processing xml, tsv, and txt files into a JSON format.\nCreated for BankruptcyWatch Coding Challenge\nSyntax:\n\n python {sys.argv[0]} <path to input file(s)>")
        return ""

    return sys.argv[1:]

def process_file(filepath):
    _, filetype = os.path.splitext(filepath)

    # Suppport relative filepaths
    if (filepath[0] == '.'):
        filepath = os.path.dirname(__file__) + filepath[1:]

    # Determine filetype for processing
    if (filetype == ".txt"):
        return process_txt_file(filepath)
    elif (filetype == ".tsv"):
        return process_tsv_file(filepath)
    elif (filetype == ".xml"):
        return process_xml_file(filepath)
    else:
        raise ValueError(f"Unsupported filetype {filetype}")

def process_txt_file(filepath):
    file = open(filepath, "r")
    file_data = file.readlines()

    data_set = []
    working_set = []

    for line in file_data:
        # Delimited by empty lines
        if not line.strip():
            if len(working_set) > 0:
                data_set.append(working_set)
                working_set = []

        # Add line to set
        else:
            working_set.append(line.strip())

    json_dataset = []

    for data in data_set:
        json_data = {}

        # Process County data
        if (len(data) == 4):
            json_data["county"] = data[2]
            data.pop(2)

        # Process remaining Data
        if len(data) == 3:
            json_data["name"] = data[0]
            json_data["street"] = data[1]

            location_data = data[2].split(',')
            json_data["city"] = location_data[0]

            state_data = location_data[1].strip().split(' ')
            json_data["state"] = " ".join(state_data[:-1])
            json_data["zip"] = state_data[-1][:5]
        else:
            raise ValueError(f"Formatting error, expected 3 lines of data but found {len(data_set)} lines")

        # Add to loaded object list
        json_dataset.append(json_data)

    # Return list of json objects
    return json_dataset

def process_xml_file(filepath):
    data = ET.parse(filepath)

    json_dataset = []

    for entity in data.getroot()[1]:
        json_data = {}

        for element in entity:
            if (element.text.strip()):
                # Convert XML elements to expected Json rows
                if (element.tag.lower() == 'name'):
                    json_data['name'] = element.text

                if (element.tag.lower() == 'company'):
                    json_data['organization'] = element.text

                if (element.tag.lower() == 'street'):
                    json_data['street'] = element.text

                if (element.tag.lower() == 'city'):
                    json_data['city'] = element.text

                if (element.tag.lower() == 'state'):
                    json_data['state'] = element.text

                if (element.tag.lower() == 'postal_code'):
                    if (element.text.strip()[-1] == '-'):
                        json_data['zip'] = element.text[:5]

                    else:
                        json_data['zip'] = element.text[:5] + "-" + element.text[-4:]

        json_dataset.append(json_data)

    return json_dataset

def process_tsv_file(filepath):
     file = open(filepath, "r")
     file_data = file.readlines()

     json_dataset = []
     skip = False

     for line in file_data:
         json_data = {}
         row = line.split("\t")

         if (not skip):
             skip = True
             continue

         # Process full name and handle edge cases
         if (row[0] == ''):
             row.insert(0, '')
             row.pop(4)
         elif (row[1] != "N/M/N"):
             json_data["name"] = row[0] + " " + row[1] + " " + row[2]
         else:
             json_data["name"] = row[0] + " " + row[2]

         # Process organization name if present
         if (row[3] != "N/A"):
            json_data["organization"] = row[3]

         # Process location data
         json_data["street"] = row[4]
         json_data["city"] = row[5]
         json_data["state"] = row[6]

         if (row[7] != ''):
             json_data["county"] = row[7]

         if (row[9] != '\n'):
             json_data["zip"] = row[8] + "-" + row[9].strip()
         else:
            json_data["zip"] = row[8]

         json_dataset.append(json_data)

     return json_dataset


# Read filepaths from Arguments
input_files = load_arguments()

if (input_files):
    # Process and Sort Data
    merged_data = []
    for file in input_files:
        merged_data.extend(process_file(file))

    merged_data = sorted(merged_data, key=lambda x: x['zip'])

    print(json.dumps(merged_data, indent=2))
