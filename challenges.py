import os
import sys
import json
import pandas
import argparse
import xml.etree.ElementTree as ET

def parse_json_from_xml(file):
    tree = ET.parse(file)
    root = tree.getroot()

    output = []

    for entity in root.iter('ENT'):
        entity_dict = {}
        for data in entity.iter():
            if data.tag == 'NAME' and data.text.strip() != '':
                entity_dict['name'] = data.text
            elif data.tag == 'COMPANY' and data.text.strip() != '':
                entity_dict['company'] = data.text
            if data.tag == 'STREET' and data.text.strip() != '':
                entity_dict['street'] = data.text
            if data.tag == 'STREET2' and data.text.strip() != '':
                entity_dict['street'] += ' ' + data.text
            if data.tag == 'STREET3' and data.text.strip() != '':
                entity_dict['street'] += ' ' + data.text
            if data.tag == 'CITY' and data.text.strip() != '':
                entity_dict['city'] = data.text
            if data.tag == 'CONUTY' and data.text.strip() != '':
                entity_dict['county'] = data.text
            if data.tag == 'STATE' and data.text.strip() != '':
                entity_dict['state'] = data.text
            if data.tag == 'POSTAL_CODE' and data.text.strip() != '':
                zip, zip_4 = data.text.split('-')
                entity_dict['zip'] = zip.strip() + '-' + zip_4.strip() if zip_4.strip() != '' else zip.strip()

        output.append(entity_dict)
    
    return output

def parse_json_from_tsv(file):
    data = pandas.read_csv(file, sep='\t')
    output = []
    for index, row in data.iterrows():
        entity_dict = {}

        if type(row['first']) != float:
            entity_dict['name'] = row['first']
        if type(row['middle']) != float and row['middle'] != 'N/M/N':
            entity_dict['name'] = entity_dict.get('name', '') + ' ' + row['middle']
            entity_dict['name'] = entity_dict['name'].strip()
        if type(row['last']) != float:
            entity_dict['name'] =  entity_dict.get('name', '') + ' ' + row['last']
            entity_dict['name'] = entity_dict['name'].strip()
        elif type(row['organization']) != float:
            entity_dict['company'] = row['organization']

        if type(row['address']) != float:
            entity_dict['street'] = row['address']
        if type(row['city']) != float:
            entity_dict['city'] = row['city']
        if type(row['county']) != float:
            entity_dict['count'] = row['county']
        if type(row['state']) != float:
            entity_dict['state'] = row['state']
        if type(row['zip']) != float:
            entity_dict['zip'] = row['zip']
            if type(row['zip4']) != float:
                entity_dict['zip'] += '-' + row['zip4']

        output.append(entity_dict)
    
    return output
        

def parse_json_from_txt(file):
    output = []

    with open(file, 'r') as f:
        entities, data = [], []
        for line in f:
            if line == '\n':
                if len(data) > 0:
                    entities.append(data)
                    data = []
            else:
                data.append(line.strip())

        entity_dict = {}

        for entity in entities:
            entity_dict['name'] = entity[0]
            entity_dict['street'] = entity[1]
            city, state_zip = entity[-1].split(',')
            
            zip4 = ''
            if len(state_zip.strip().split('-')) > 1:
                state_zip, zip4 = state_zip.strip().split('-')
            state, pre_zip = state_zip[:-5], state_zip[-5:]

            entity_dict['city'] = city.strip()
            if 'county' in entity[2].lower():
                entity_dict['county'] = entity[2]
            entity_dict['state'] = state.strip()
            entity_dict['zip'] = pre_zip + '-' + zip4 if zip4 != '' else pre_zip

            output.append(entity_dict)
            entity_dict = {}

    return output

def parse_json_from_file(file):

    if not os.path.isfile(file):
        print('Path to file does not exist: ', file)
        return 1
    
    ext = os.path.splitext(file)[-1].lower()
    output = None

    if ext == '.xml':
        output = parse_json_from_xml(file)
    elif ext == '.tsv':
        output = parse_json_from_tsv(file)
    elif ext == '.txt':
        output = parse_json_from_txt(file)
    
    output = sorted(output, key = lambda x:x['zip'])
    print(json.dumps(output, indent=4))

    return 0



parser = argparse.ArgumentParser("challenges")
parser.add_argument("file", help="A file with the extensions [.xml, .tsv, .txt] will be parse and prints a pretty-formatted JSON. Returns 0 on completion and 1 upon error.", type=str)
args = parser.parse_args()

output = parse_json_from_file(args.file)