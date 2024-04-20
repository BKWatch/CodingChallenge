import sys
import xml.etree.ElementTree as ET
import json

def get_name(first,middle,last):
    if middle == "":
        full_name = first + " " + last
    else:
        full_name = first + " " + middle + " " + last
        return full_name.strip()

def get_zip(zip):
    if len(zip) == 1:
        return zip[0]
    return zip[0]+"-"+zip[1]

def format_text_data(details):
    data = {}
    for index, l in enumerate(details):
        def extract_address():
            address = l.split(',')
            *state, zip = address[1].strip().split(' ')
            if zip[-1] == '-':
                zip = zip.strip().replace("-","")
            data['city'] = address[0]
            data['state'] = " ".join(state)
            data['zip'] = zip
        if index == 0:
            data['name'] = l
        elif index == 1:
            data['street'] = l
        elif index == 2:
            if ',' not in l:
                data['county'] = l
            else:
               data['county'] = ""
               extract_address()
        elif index == 3:
            extract_address()
            
    return data

def parse_tsv(file):
    data = {}
    with open(file, 'r') as file:
        lines = file.readlines()

        # Iterate over each line
        for index,line in enumerate(lines):
            # Split the line into fields using tab ('\t') as the delimiter
            fields = line.split('\t')
            if index == 0:
                continue
            l = len(fields)
            fields[l-1] =  fields[l-1].strip("\n")
            while l<10:
                fields.append("")
                l = l + 1

            first, middle, last = fields[0:3]
            organization = fields[3]
            address = fields[4].strip()
            zip1,zip2 = fields[8:10]
            name = get_name(first,middle,last)
            full_name = name if name else ""
           
            zip = fields[8:10]
            new_zip = []
            for z in zip:
                if z.strip() == "":
                    continue
                new_zip.append(z.strip())
            zip = get_zip(new_zip)

            postal_code = zip if zip else "" 
            if full_name == "":
                data["organization"] = organization.strip()
            else:
                data["name"] = name.strip()
            data = {
                    ** data,
                    "street": address,
                    "city": fields[5],
                    "county": fields[7],
                    "state": fields[6],
                    "zip": postal_code
                }
            final_json.append(data)
            data = {}

def parse_xml(file):
    data = {}
    tree = ET.parse(file)
    root = tree.getroot()

    # Iterate over each 'entity' element
    for entity in root.findall('ENTITY'):
        for ent in entity.findall('ENT'):

    
            name = ent.find('NAME').text
            company = ent.find('COMPANY').text.strip()
            street = ent.find('STREET').text.strip()
            city = ent.find('CITY').text.strip()
            country = ent.find('COUNTRY').text.strip()
            state = ent.find('STATE').text.strip()
            zip = ent.find('POSTAL_CODE').text.strip()

            zip = zip.split('-')
            new_zip = []
            for z in zip:
                if z.strip() == "":
                    continue
                new_zip.append(z.strip())
            if name ==  None:
                data["organization"] = company
            else:
                data["name"] = name.strip()
            data = {
                **data,
                "street": street,
                "city": city,
                "county": country,
                "state": state,
                "zip":  get_zip(new_zip)
            }

            final_json.append(data)
            data = {}

def parse_txt(file):
    with open(file, 'r') as file:
    # Iterate over each line in the file
        person_details = []
        for line in file:
            # Strip any leading or trailing whitespace from the line
            line = line.strip()
            
            # If the line is not empty, add it to the person details list
            if line:
                person_details.append(line)
            # If the line is empty and there are details in the person_details list,
            # it means we have finished reading details for one person
            elif person_details:
                # Print the person details
                r = format_text_data(person_details[0:])
                person_details = []
                final_json.append(r)
                

        # Print the last person's details if any
        if person_details:
            person_data = format_text_data(person_details[0:])
            person_details = []
            final_json.append(person_data)

final_json = []
if len(sys.argv)<2:
    print("No files attached to read")
    sys.exit(1)
file_list = sys.argv[1:]
for i, filename in enumerate(file_list):
    filename = filename.strip()
    _, extension = filename.split('.')
    try:
        if extension == 'xml':
            parse_xml(filename)
        elif extension == 'tsv':
                parse_tsv(filename)
        elif extension == 'txt':
                parse_txt(filename)  
        else:
            print("This file extension {} at index {} is not supported".format(extension, i))     
    except Exception as e:
        print("An error occurred: ",e)
     
    if  final_json:  
        # sort the JSON
        final_json.sort(key = lambda x: x["zip"])

        # format the final JSON

        beautified_json = json.dumps(final_json, indent=4)

        # Print the beautified JSON
        
        print(beautified_json)

