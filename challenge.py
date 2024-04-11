import os
import sys
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET
import csv
import argparse
import re
import json

def main():
    input = argparse.ArgumentParser(description="Address Data Parser")
    input.add_argument('input', nargs="+")
    input.add_argument('-q', '--quiet', action='store_true', help="Enable to prevent printing addresses to the screen")
    input.add_argument('-o', '--output', help="Select a file to write to")

    args= input.parse_args()
    
    data = []

    # Input Verification
    for file_path in args.input:
        if not os.path.isfile(file_path):
            print("File: '{}' not found".format(file_path))
            sys.exit(1)

    for file_path in args.input:
        extension = os.path.splitext(file_path)[1]
        addressParser = fileParserFactory(extension)
        if addressParser == None:
            print("UNSUPPORTED FILE TYPE: ", file_path)
            sys.exit(1)
        with open(file_path, 'r') as f:
            parsed_data = addressParser.parseFile(f)
            if parsed_data != None:
                data += parsed_data
            f.close()

    # Printing and Saving
    data.sort(key=getZip)

    json_data = json.dumps(data, indent=2)
    if not args.quiet: print(json_data)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(json_data)

    exit()

def getZip(addr):
    return addr['zip']


def fileParserFactory(ext):
    match ext.lower():
        case ".xml":
            return FileParserXML()
        case ".tsv":
            return FileParserCSV('\t')
        case ".txt":
            return FileParserTXT()
        case default:
            print("File Extension Not Supported")
            return None

class FileParser(ABC):
    def validateZip(self, zip):
        zip = re.sub('\s+', '', zip)
        zip = re.search("\d{5}-\d{4}|\d{5}", zip)
        return zip[0]

    @abstractmethod
    def parseFile(self, file):
        pass

class FileParserXML(FileParser):
    def parseFile(self, file):
        tree = ET.parse(file)
        entities = None
        data = []
        for entity in tree.getroot().find('ENTITY').iter("ENT"):
            name_or_organization = "name"
            title = entity.find("NAME").text.strip()
            if title == "":
                name_or_organization = "organization"
                title = entity.find("COMPANY").text.strip()

            street = (
                    entity.find("STREET").text 
                    + entity.find("STREET_2").text 
                    + entity.find("STREET_3").text
                ).strip()

            zip = self.validateZip(entity.find("POSTAL_CODE").text)
            
            data.append({
                name_or_organization: title,
                "street": street,
                "city": entity.find("CITY").text,
                "state": entity.find("STATE").text,
                "zip": zip,
            })
        return data

class FileParserCSV(FileParser):
    def __init__(self, delimiter=","):
        self.delimiter = delimiter

    def parseFile(self, file):
        data = []
        values = csv.reader(file, delimiter=self.delimiter)
        next(values)
        for row in values:
            name_or_org = "name"
            if row[0] == "":
                name_or_org = "organization"
                if row[3] == "N/A": title = row[2]
                else: title = row[3]
            elif row[1] == "N/M/N":
                title = row[0] +' '+row[2]
            else:
                title = row[0]+' '+row[1]+' '+row[2]

            street = row[4]
            city = row[5]
            state = row[6]
            county = row[7]
            zip = self.validateZip(row[8])

            data.append({
                name_or_org: title.strip(),
                "street": street.strip(),
                "city": city.strip(),
                "state": state.strip(),
                "county": county.strip(),
                "zip": zip,
            })
        return data

class FileParserTXT(FileParser):
    def parseFile(self, file):
        data = []
        values = []
        for line in file:
            if line == "\n":
                if len(values) == 0: continue
                name = values[0].strip()
                street = values[1].strip()
                city = None
                county = None
                state = None
                zip = "0"
                if len(values) == 3:
                    last_line = values[2]
                elif len(values) == 4:
                    county = values[2].strip()
                    last_line = values[3]
                
                reg = re.findall(r'([^,]+),(?:\s*)(\D+) (\d{5}-\d{4}|\d{5})', last_line)[0]
                city = reg[0].strip()
                state = reg[1].strip()
                zip = reg[2].strip()
                data.append({
                    "name":name,
                    "street": street,
                    "city": city,
                    "county": county,
                    "state": state,
                    "zip": zip
                })
                last_line = None
                values = []
            else:
                values.append(line)
        return data

if __name__ == '__main__':
    main()