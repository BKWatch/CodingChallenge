import json
from xml.etree import ElementTree as ET
import csv
import os
#Not standard library 
import logging

def beutify_zipcode(zipcode):
    if zipcode[-1] == "-" or zipcode[-2] == "-":
        zipcode = zipcode[:5]
    return zipcode

def get_extension_type(filepath):
    return filepath.split('.')[-1]

def get_valid_extension(filepath):
    extension = filepath.split('.')[-1]
    return extension == "xml" or extension == "tsv" or extension == "txt"

def get_valid_filepaths():
    filepaths = []
    while True:
        filepath = input("Enter a file path or 'done' to finish or '--help' to help: ")
        if filepath.lower() == "done":
            break
        
        if filepath.lower() == "--help":
            print("e.g. = input/input1.xml.")
            print("\nOr add new files")
            continue

        if not os.path.exists(filepath):
            print("Invalid file path. Please try again.")
            continue

        if not get_valid_extension(filepath):
            print("Invalid extension. Please try again.")
            continue

        filepaths.append(filepath)
    return filepaths

def xml_to_list_dict(element):
    data = []
    for tag in element.iter('ENT'):
        ent = {}
        children = tag.findall('*')
        for child in children:
            if child.text != " ":
                if child.tag.upper() == "NAME":
                    ent["name"] = child.text
                elif child.tag.upper() == "COMPANY":
                    ent["organization"] = child.text
                elif child.tag.upper() == "STREET":
                    ent["street"] = child.text
                elif child.tag.upper() == "STREET_2":
                    ent["street"] += " " + child.text
                elif child.tag.upper() == "STREET_3":
                    ent["street"] += " " + child.text
                elif child.tag.upper() == "CITY":
                    ent["city"] = child.text
                elif child.tag.upper() == "STATE":
                    ent["state"] = child.text
                elif child.tag.upper() == "COUNTRY":
                    ent["country"] = child.text
                elif child.tag.upper() == "POSTAL_CODE":
                    ent["zip"] = beutify_zipcode(child.text)
        data.append(ent)
    return data


def xml_to_json(filePath):
    
    tree = ET.parse(filePath)
    root = tree.getroot()

    data = xml_to_list_dict(root)

    return json.dumps(data,  indent=4)


def tsv_to_json(filePath):
    data = []
    with open(filePath, 'r', newline='', encoding='utf-8') as tsvfile:
        tsv_reader = csv.DictReader(tsvfile, delimiter='\t')
        

        for row in tsv_reader:
            first = row['first']
            middle = row['middle']
            last = row['last']
            organization = row['organization']
            address = row['address']
            city = row['city']
            state = row['state']
            county = row['county'] 
            zip_code = row['zip']
            zip4 = row['zip4']

            ent = {}
            if first or middle or last:
                name = first + "  " + middle + " " + last
                ent['name'] = name.strip()
            if organization != "N/A":
                ent['organization'] = organization
            if address:
                ent['street'] = address
            if city:
                ent['city'] = city
            if state:
                ent['state'] = state
            if county:
                ent['county'] = county
            if zip_code:
                ent["zip"] = zip_code
            if  zip4:
                ent["zip"] += " - " + zip4
            
            data.append(ent)
            
        return json.dumps(data, indent=4)


def txt_to_json(filePath):
    data = []

    name = None
    street = None
    county = None
    city = None
    state = None
    zipcode = None
    
    with open(filePath, 'r', encoding='utf-8') as txtfile:
        for line in txtfile:
            line = line.strip()
            if line:
                if not name:
                    name = line
                elif not street:
                    street = line
                elif not county and "COUNTY" in line.upper():
                    county = line
                else:
                    city, state_zipcode = line.rsplit(',', 1)
                    state, zipcode = state_zipcode.strip().rsplit(' ', 1)
                    zipcode = beutify_zipcode(zipcode)
            elif name:
                if county is not None:
                    data.append({
                        "name" : name,
                        "street" : street,
                        "county": county, 
                        "city" : city,
                        "state" : state,
                        "zip" : zipcode
                    })
                else:
                    data.append({
                        "name" : name,
                        "street" : street,
                        "city" : city,
                        "state" : state,
                        "zip" : zipcode
                    })
                name = None
                street = None
                county = None
                city = None
                state = None
                zipcode = None

        
    return json.dumps(data, indent=4)

def main():
    json_response = []
    valid_paths = get_valid_filepaths()
    for path in valid_paths:
        if get_extension_type(path) == "xml":
            json_response.extend(json.loads(xml_to_json(path)))
        elif get_extension_type(path) == "tsv":
            json_response.extend(json.loads(tsv_to_json(path)))
        elif get_extension_type(path) == "txt":
            json_response.extend(json.loads(txt_to_json(path)))
    json_response_sorted_zip_codes = sorted(json_response, key=lambda x: x["zip"], reverse=True)
    print(json.dumps(json_response_sorted_zip_codes, indent=4))
        
if __name__ == "__main__":
    main()