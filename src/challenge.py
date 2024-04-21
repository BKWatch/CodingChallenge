import sys
import csv
import json
import re
import xml.etree.ElementTree as ET


def parse_xml(file: str):
    result = []
    tree = ET.parse(file)
    root = tree.getroot()
    if root.find('ENTITY'):
        for ent in root.find('ENTITY').findall('ENT'):
            row = {}
            if ent.find('NAME') is not None:
                name = ent.find('NAME').text.strip()
                if name:
                    row['name'] = name
            if ent.find('COMPANY') is not None:
                company = ent.find('COMPANY').text.strip()
                if company:
                    row['organization'] = company
            street = []
            if ent.find('STREET') is not None:
                street0 = ent.find('STREET').text.strip()
                if street0:
                    street.append(street0)
            if ent.find('STREET1') is not None:
                street1 = ent.find('STREET1').text.strip()
                if street1:
                    street.append(street1)
            if ent.find('STREET2') is not None:
                street2 = ent.find('STREET2').text.strip()
                if street2:
                    street.append(street2)
            if street:
                row['street'] = ', '.join(street)
            if ent.find('CITY') is not None:
                city = ent.find('CITY').text.strip()
                if city:
                    row['city'] = city
            if ent.find('COUNTY') is not None:
                county = ent.find('COUNTY').text.strip()
                if county:
                    row['county'] = county
            if ent.find('STATE') is not None:
                state = ent.find('STATE').text.strip()
                if state:
                    row['state'] = state
            if ent.find('POSTAL_CODE') is not None:
                code = ent.find('POSTAL_CODE').text.strip()
                if code:
                    row['zip'] = code

            result.append(row)

    return result


def parse_txt(file: str):
    json_output = []
    with open(file, 'r', encoding='utf-8') as file:
        row = {}
        for line in file:
            line = line.strip()
            if line:
                if 'name' not in row:
                    row['name'] = line
                elif 'street' not in row:
                    row['street'] = line
                elif 'county' not in row and 'county' in line.lower():
                    county = line.split("//s+")[0]
                elif 'state' not in row:
                    parts = re.split(r'\s+', line)
                    row['city'] = parts[0][:-1]
                    if county: row['county'] = county
                    row['state'] = parts[1]
                    row['zip'] = parts[2]
            else:
                if row:
                    json_output.append(row)
                    row = {}
    return json_output


def parse_tsv(file: str):
    json_output = []
    with open(file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            json_output.append(row)

    return json_output


# parse data from the file
def parse(file: str):
    file_type = file.split(".")[-1]
    output_file = 'output/output.json'

    output_json = []
    if file_type == 'tsv':
        output_json += parse_tsv(file)
    elif file_type == 'txt':
        output_json += parse_txt(file)
    elif file_type == 'xml':
        output_json += parse_xml(file)
    with open(output_file, 'w') as json_file:
        json.dump(output_json, json_file, indent=4)


# read filenames
if __name__ == "__main__":
    file_names = sys.argv[1:]
    if not file_names:
        print("Missing required parameter filenames")
    else:
        for file_name in file_names:
            parse(file_name)
    print("process completed")
