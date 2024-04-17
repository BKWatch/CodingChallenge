import xml.etree.cElementTree as ET
import json
import csv


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
        # No county stored in xml


        # To let zip in the format 00000 or 00000-0000
        print(postal_code, len(postal_code))
        if len(postal_code) > 8:
            temp['zip'] = postal_code
        else:
            temp['zip'] = postal_code[:5]


        # Create a temp value to store the zip for sorting
        if "-" in temp['zip']:
            temp["fake_zip"] = postal_code[:5]+postal_code[-4:]
        else:
            temp["fake_zip"] = postal_code+"0000"

        res.append(temp) # Add the dictionary to the result array
    res.sort(key=lambda x: x['fake_zip'])
    
    for i in res:
        del i['fake_zip']

    with open('output1.json', 'w') as json_file:
        json.dump(res, json_file, indent=4)
    json_file.close()


def read_tsv():
    with open('input/input2.tsv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')

        res = []
        for row in reader:
            temp = {}
            
            # To create the whole name
            first = row['first'].strip()
            middle = row['middle'].strip() 
            last = row['last'].strip()
            name = ""
            if first:
                name += first + ' '
            if middle and middle != "N/M/N": # N/M/N = no middle name
                name += middle +' '
            if last:
                name += last +' '
            name = name[:-1]

            organization = row['organization'].strip() 


            # Store basic info for address
            street = row['address'].strip()
            city = row['city'].strip()
            state = row['state'].strip()
            county = row['county'].strip()

            if name:
                temp['name'] = name
            
            elif organization:
                temp['organization'] = organization

            temp['street'] = street
            temp['city'] = city
            if county:
                temp['county'] = county
            temp['state'] = state


            # Get the zip 
            zip_code = row['zip'].strip()
            zip4 = row['zip4'].strip()
            if zip4:
                temp['zip'] = zip_code+"-"+zip4
                temp['fake_zip'] = zip_code+zip4
            else:
                temp['zip'] = zip_code
                temp['fake_zip'] = zip_code+'0000'

            res.append(temp)

        res.sort(key=lambda x: x['fake_zip'])
        
        for i in res:
            del i['fake_zip']

        with open('output2.json', 'w') as json_file:
            json.dump(res, json_file, indent=4)   

        file.close()
        json_file.close()



if __name__ == '__main__':
    read_xml()

