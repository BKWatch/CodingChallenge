import xml.etree.ElementTree as ElementTree
import argparse
from os.path import splitext, isfile
import sys
import json
import csv


def check_file_list(file_list):
    for file_name in file_list:
        if not isfile(file_name):
            print("No such file '{}'. Please make sure the files listed exist.".format(file_name), file=sys.stderr)
            exit(1)
        name, extension = splitext(file_name)
        if extension.lower() != '.xml' and extension.lower() != '.tsv' and extension.lower() != '.txt':
            print("Input files have invalid extension (accepted: 'xml', 'tsv', 'txt')", file=sys.stderr)
            exit(1)


def clean_zip_code(dirty_zip):
    dirty_zip = dirty_zip.replace(' ', '')
    zip_list = dirty_zip.split('-')
    if len(zip_list) == 2:
        if zip_list[1] == '':
            return zip_list[0]
        else:
            return '{}-{}'.format(zip_list[0], zip_list[1])
    elif len(zip_list) == 1:
        return zip_list[0]
    else:
        print("Error: Zip code format for '{}' is completely incorrect".format(dirty_zip), file=sys.stderr)
        exit(1)


def parse_xml(file_name):
    entities = []
    tree = ElementTree.parse(file_name)
    root = tree.getroot()
    for entity in root.findall('./ENTITY/ENT'):
        entity_dict = {}
        for info in entity:
            if info.text.strip() == '':
                continue
            tag = info.tag
            if tag == 'NAME':
                entity_dict['name'] = info.text
            elif tag == 'COMPANY':
                entity_dict['organization'] = info.text
            elif tag == 'STREET':
                entity_dict['street'] = info.text
            elif tag == 'STREET_2':
                entity_dict['street'] = '{}, {}'.format(entity_dict['street'], info.text)
            elif tag == 'STREET_3':
                entity_dict['street'] = '{}, {}'.format(entity_dict['street'], info.text)
            elif tag == 'CITY':
                entity_dict['city'] = info.text
            elif tag == 'STATE':
                entity_dict['state'] = info.text
            elif tag == 'POSTAL_CODE':
                entity_dict['zip'] = clean_zip_code(info.text)
            elif tag == 'COUNTY':
                entity_dict['county'] = info.text
            # NOTE: XML files don't seem to include a COUNTY based on the example file
        entities.append(entity_dict)
    return entities


def parse_tsv(file_name):
    with open(file_name, 'r') as fd:
        rd = csv.reader(fd, delimiter="\t")
        next(rd)    # skip header
        entities = []
        for i, row in enumerate(rd):
            entity_dict = {}
            try:
                first, middle, last, organization, address, city, state, county, postal, zip4 = row
                # If organization is N/A and first and middle name are blank, then last name is the organization
                if first.strip() == '':
                    if last.strip() == '' and organization.strip().upper() != 'N/A':
                        entity_dict['organization'] = organization
                    elif organization.strip().upper() == 'N/A':
                        entity_dict['organization'] = last
                    else:
                        print("Missing Organization/Name information in row {} in file {}.".format(i, file_name),
                              file=sys.stderr)
                        exit(1)
                else:
                    if middle.strip().lower() == 'n/m/n':
                        entity_dict['name'] = "{} {}".format(first.strip(), last.strip())
                    else:
                        entity_dict['name'] = "{} {} {}".format(first.strip(), middle.strip(), last.strip())

                entity_dict['street'] = address
                entity_dict['city'] = city
                entity_dict['state'] = state
                if county.strip() != '':
                    entity_dict['county'] = county
                if zip4.strip() != '':
                    entity_dict['zip'] = '{}-{}'.format(postal, zip4)
                else:
                    entity_dict['zip'] = postal
            except ValueError:
                print("Row {} in file {} does not have the correct number of values.".format(i, file_name),
                      file=sys.stderr)
                exit(1)
            entities.append(entity_dict)
        return entities


def parse_txt(file_name):
    # Each entity is separated by a newline
    # Companies end with "Inc.", "LLC", or "Ltd."
    # Format:
    #   Name/Organization
    #   Address
    #   County (If "County" is in the line)
    #   City, State Zip
    entities = []
    with open(file_name, 'r') as fd:
        file_string = fd.read()
        clean_entity_list = [entity.strip() for entity in file_string.split('\n\n') if entity.strip()]

    for entity in clean_entity_list:
        entity_dict = {}
        info_list = entity.split('\n')
        try:
            name_or_org = info_list.pop(0).strip()
            if name_or_org.lower().endswith(('llc', 'ltd.', 'inc.')):
                entity_dict['organization'] = name_or_org
            else:
                entity_dict['name'] = name_or_org
            address = info_list.pop(0).strip()
            entity_dict['street'] = address
            county_or_last_line = info_list.pop(0).strip()
            if county_or_last_line.lower().endswith('county'):
                entity_dict['county'] = county_or_last_line
                county_or_last_line = info_list.pop(0).strip()
        except IndexError:
            print("IndexError: Missing info from file '{}'".format(file_name), file=sys.stderr)
            exit(1)
        city, remainder = county_or_last_line.split(', ', 1)
        entity_dict['city'] = city.strip()
        state, postal = remainder.rsplit(' ', 1)
        entity_dict['state'] = state.strip()
        entity_dict['zip'] = clean_zip_code(postal)
        entities.append(entity_dict)

    return entities


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file_list', nargs='+', help='one or more filenames with extension .txt, .xml, or'
                                                     '.tsv each separated by a whitespace')
    args = parser.parse_args()

    check_file_list(args.file_list)

    combined_list = []

    for file_name in args.file_list:
        name, extension = splitext(file_name)
        if extension.lower() == '.xml':
            combined_list += parse_xml(file_name)
        elif extension.lower() == '.tsv':
            combined_list += parse_tsv(file_name)
        elif extension.lower() == '.txt':
            combined_list += parse_txt(file_name)
        else:
            exit(1)

    combined_list = sorted(combined_list, key=lambda item: item['zip'])

    print(json.dumps(combined_list, indent=2))


if __name__ == "__main__":
    main()
    exit(0)
