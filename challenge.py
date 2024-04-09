import json
import sys
import xml.etree.ElementTree as ET
import csv
import argparse
from typing import List, Dict


class FileParser:
    """
    This class contains methods to parse .txt, .tsv, and .xml files
    """
    
    @staticmethod
    def parse_xml(file_path: str) -> List[Dict[str, str]]:
        """
        Parses .xml file and returns a list of address dictionaries.
        params:
            file_path: path to the xml file.
        returns:
            A list of dictionaries.
        """
        addresses = []
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            for entity in root.findall('.//ENTITY/ENT'):
                street = entity.find('STREET').text.strip()
                city = entity.find('CITY').text.strip()
                state = entity.find('STATE').text.strip()
                county = entity.find('COUNTY')
                zip = entity.find('POSTAL_CODE').text.strip()
                # if either name or organization is to be included 
                if entity.find('NAME').text.strip() == '': 
                    address = {
                        'organization': entity.find('COMPANY').text.strip(),
                        'street': street,
                        'city': city,
                        'state': state,
                        'county': county,
                        'zip': zip
                    }
                else:
                    address = {
                        'name': entity.find('NAME').text.strip(),
                        'street': street,
                        'city': city,
                        'state': state,
                        'county': county,
                        'zip': zip
                    }

                addresses.append(address)
            
            # sorting over zip
            sorted_xml = sorted(addresses, key=lambda x: x['zip'])
            return sorted_xml
        
        except (FileNotFoundError, ET.ParseError) as e:
            print(f"Error parsing file: {file_path}: {e}", file=sys.stderr)
            return 1


    @staticmethod
    def parse_tsv(file_path: str) -> List[Dict[str, str]]:
        """
        Parses .tsv file and returns a list of address dictionaries.
        params:
            file_path: path to the tsv file.
        returns:
            A list of dictionaries.
        """
        addresses = []
        try:
            with open(file_path, 'r') as f:
                csv_reader = csv.reader(f, delimiter="\t")
                # Skipping the header
                next(csv_reader, None)
                data = list(csv_reader)

                for row in data:
                    name_tokens  = (row[0].strip() + " " + row[1].strip() + " " + row[2].strip()).split(' ')
                    
                    street = row[4].strip()
                    city = row[5].strip()
                    state = row[6].strip()
                    county = row[7].strip()
                    zip = row[8].strip() + "-" + row[9].strip()

                    if ('LLC' in name_tokens) or ('Ltd.' in name_tokens):
                        organization = ' '.join(name_tokens).strip()
                        address = {
                            'organization': organization,
                            'street': street,
                            'city': city,
                            'state': state,
                            'county': county,
                            'zip': zip,
                        }
                                            
                    elif row[3] != 'N/A':
                        organization = row[3].strip()
                        address = {
                            'organization': organization,
                            'street': street,
                            'city': city,
                            'state': state,
                            'county': county,
                            'zip': zip,
                        }
                    
                    else:
                        name = ' '.join(name_tokens).strip()
                        address = {
                            'name': name,
                            'street': street,
                            'city': city,
                            'state': state,
                            'county': county,
                            'zip': zip,
                        }                       

                    addresses.append(address)
            
            # sorted tsv
            sorted_tsv = sorted(addresses, key=lambda x: x['zip'])
            return sorted_tsv
        
        except FileNotFoundError as e:
            print(f"Error opening file: {file_path}: {e}", file=sys.stderr)
            return 1


    @staticmethod
    def parse_plain_text(file_path: str) -> List[Dict[str, str]]:
        """
        Parses .txt file and returns a list of address dictionaries.
        params:
            file_path: path to the xml file.
        returns:
            A list of dictionaries.
        """
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                                
            # remove repeating '\n's
            cleaned_lines = []
            for item in lines:
                if len(cleaned_lines) == 0:
                    cleaned_lines.append(item)
                # elif item != '\n':
                #     cleaned_lines.append(item)
                elif item == '\n' and cleaned_lines[-1] == '\n':
                    continue
                else:
                    cleaned_lines.append(item)
                
            # making records
            record_list = []
            record = []
            for item in cleaned_lines:
                if item != '\n':
                    record.append(item)
                else:
                    # print(record)
                    if len(record) > 0:
                        record_list.append(record)
                    # instantiate new record object
                    record = []
            
            # extracting data from record_list
            addresses = []
            for record in record_list:
                name = record[0]
                street = record[1]

                if 'COUNTY' in record[2]:
                    # print('county ', len(record))
                    county = record[2].strip()
                    city = record[3].strip().split(',')[0].strip()
                    state = record[3].strip().split(',')[1].strip().split(' ')[0].strip()
                    zip = record[3].strip().split(',')[1].strip().split(' ')[1].strip()

                    address = {
                        'name': name,
                        'street': street,
                        'city': city,
                        'state': state,
                        'county': county,
                        'zip': zip,
                    }
                    addresses.append(address)
                
                else:
                    # print(len(record))
                    county = ''
                    city = record[2].strip().split(',')[0].strip()
                    state = record[2].strip().split(',')[1].strip().split(' ')[0].strip()
                    zip = record[2].strip().split(',')[1].strip().split(' ')[1].strip()

                    address = {
                        'name': name,
                        'street': street,
                        'city': city,
                        'state': state,
                        'county': county,
                        'zip': zip,
                    }
                    addresses.append(address)

            # sorted txt
            sorted_txt = sorted(addresses, key=lambda x: x['zip'])
            return addresses
    
        except FileNotFoundError as e:
            print(f"Error opening file: {file_path}: {e}", file=sys.stderr)
            return 1


def file_parsing(file_path: str) -> List[Dict[str, str]]:
    """
    Parses a file based on its extension and prints and returns a list of address dictionaries 
    sorted on zip code.
    params:
        file_path: path to the xml file.
    returns:
        A list of dictionaries.
    """
    extension = file_path.split(".")[-1].lower()
    
    if extension == "xml":
        return FileParser.parse_xml(file_path)
    elif extension == "tsv":
        return FileParser.parse_tsv(file_path)
    elif extension == "txt":
        return FileParser.parse_plain_text(file_path)
    else:
        print(f"Error: Unsupported file format: {file_path}", file=sys.stderr)
        return 1



def main() -> None:
    parser = argparse.ArgumentParser(description="Parses the passed files and prints a JSON.")
    parser.add_argument('files', nargs='+', help="List of file paths to be parsed")
    args = parser.parse_args()

    addresses = []
    for file_path in args.files:
        try:
            addresses.extend(file_parsing(file_path))
        except Exception as e:
            print(f"Error parsing {file_path}: {e}", file=sys.stderr)
            return 1

    print(json.dumps(addresses, indent=2))

if __name__ == "__main__":
    main()
