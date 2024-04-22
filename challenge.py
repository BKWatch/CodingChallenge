import os
import sys
import xml.etree.ElementTree as ET
import json
import csv



def extract_xml_info(file_path):

    extracted_data = []
    tree = ET.parse(file_path)
    root = tree.getroot()
    for entity in root.findall('./ENTITY/ENT'):

        data_dict = {}
        name = entity.find('NAME')
        if name is not None:

            data_dict['name'] = name.text.strip()
        else:
            data_dict['name'] = None
        
        company = entity.find('COMPANY')
        if company is not None:

            data_dict['organization'] = company.text.strip()
        else:
            data_dict['organization'] = None
        
        data_dict['street'] = entity.find('STREET').text.strip()
        data_dict['city'] = entity.find('CITY').text.strip()
        data_dict['state'] = entity.find('STATE').text.strip()
        
        country = entity.find('COUNTRY')
        if country is not None:

            data_dict['country'] = country.text.strip()
        else:
            data_dict['country'] = None
        
        postal_code = entity.find('POSTAL_CODE').text.strip().split('-')[0]
        data_dict['zip'] = postal_code
        
        extracted_data.append(data_dict)
    return extracted_data

def extract_tsv_info(file_path):
    data = []

    with open(file_path, 'r', encoding='utf-8') as file:

        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:

            data.append(row)
    return data

def extract_text_info(file_path):
    extracted_info = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        current_data = {}
        for line in lines:

            line = line.strip()

            if line:
                if not current_data:

                    current_data['name'] = line
                elif len(line.split(',')) > 1:

                    city_state_zip = line.split(',')
                    current_data['city'] = city_state_zip[0].strip()
                    if len(city_state_zip) > 1:

                        current_data['state'] = city_state_zip[1].strip().split()[0]
                        if len(city_state_zip[1].strip().split()) > 1:

                            current_data['zip'] = city_state_zip[1].strip().split()[1]

                elif len(line.split()) == 1:

                    current_data['state'] = line
                else:

                    current_data['street'] = line
                    extracted_info.append(current_data)
                    current_data = {}
    return extracted_info

def main(*args,**kwargs):
    for arg in args:

        path_list = arg
        for path in path_list:

            filename, file_extension = os.path.splitext(path)
            if file_extension == ".xml":

                data = extract_xml_info(path)
                print(json.dumps(data, indent=4))

            elif file_extension == ".tsv":

                data = extract_tsv_info(path)
                print(json.dumps(data, indent=4))

            elif file_extension == ".txt":

                data = extract_text_info(path)
                print(json.dumps(data, indent=4))
                
            else:
                print("Error: Unsupported file format")

if __name__=="__main__":
   args = sys.argv[1:]
   main(args)