import xml.etree.cElementTree as ET
import json


def read_xml():
    # Load and parse the XML file
    tree = ET.parse('input/input1.xml')
    root = tree.getroot()

    res = []

    # Access the ENTITY/ENT section
    for ent in root.findall('.//ENT'):
        temp  = {} # Dictionary to store the entity details

        name = ent.find('NAME').text
        organization = ent.find('COMPANY').text
        street = ent.find('STREET').text
        city = ent.find('CITY').text
        state = ent.find('STATE').text
        country = ent.find('COUNTRY').text
        postal_code = ent.find('POSTAL_CODE').text

        if name != " ":
            temp['name'] = name
        
        elif organization != " ":
            temp['organization'] = organization

        temp['street'] = street
        temp['city'] = city
        temp['state'] = state
        if country != " ":
            temp['country'] = country

        # To let zip in the format 00000 or 00000-0000
        print(postal_code, len(postal_code))
        if len(postal_code) > 8:
            temp['zip'] = postal_code
        else:
            temp['zip'] = postal_code[:5]


        # Create a temp value to store the zip for sorting
        if "-" in temp['zip']:
            temp["real_zip"] = postal_code[:5]+postal_code[-4:]
        else:
            temp["real_zip"] = postal_code+"0000"

        res.append(temp) # Add the dictionary to the result array
    res.sort(key=lambda x: x['real_zip'])
    
    for i in res:
        del i['real_zip']

    with open('output1.json', 'w') as json_file:
        json.dump(res, json_file, indent=4)




if __name__ == '__main__':
    read_xml()

