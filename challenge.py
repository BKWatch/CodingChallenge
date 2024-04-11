'''
- First Name: Shreeram
- Last Name: Gudemaranahalli Subramanya (PS: Becuase I have 2 words in my last name, I used logic of demiliting upto 2 words in organization/ last name filtering in the tsv processor)
- How to use the code base on command line:
- Takes multiple arguments
    1) python3 challenge.py input/input1.xml
    2) python3 challenge.py input/input1.xml input/input2.tsv
    3) python3 challenge.py input/input1.xml input/input2.tsv input/input3.txt
    4) python3 challenge.py input/input1.xml input/input2.tsv input/input3.txt input/input2.tsv
    5) Watch out for error handling unsupported files:
        python3 challenge.py input/input1.xml input/input2.pdf
         o/p => parsing of first file
          ERROR - Unsupported file extension: pdf | input/input2.pdf
          parsing of third file
          
        - echo $? to check exit status
        ERROR - Unsupported file extension: pdf | input/input2.pdf
        exit status 0
        else 1
        
'''

import json
import sys
import argparse
import csv
import xml.etree.ElementTree as ET
import logging

# Configuring logger
logging.basicConfig(level=logging.DEBUG, filename='challenge.log', encoding='utf-8', format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
# Error logging
error_handler = logging.StreamHandler()   
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(levelname)s - %(message)s')
error_handler.setFormatter(error_formatter)
logging.getLogger('').addHandler(error_handler)

# XML processing and helper function
def process_xml_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = file.read()
    except Exception as e:
        log_exception(e, file_path)
        sys.exit(1)

    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        logging.error(f"XML parsing error: {file_path} - {e}")
        sys.exit(1)

    entities  = []
    for entity in root.findall('.//ENTITY/ENT'):
        entities .append(process_xml_entity(entity))
        #iNDIVIDUALS zip code sort followed by Organization zip code
        entities = sorted(entities, key=lambda x: (x['zip'] == "", x['zip']))
        
    return entities

## Helper func XML processing
def process_xml_entity(entity):
    processed_entity = {}
    name = entity.findtext('NAME', default='').strip()
    company = entity.findtext('COMPANY', default='').strip()
    # if exist: name -> individual else Company -> organization
    if name:
        processed_entity['name'] = name
        county = entity.findtext('COUNTY', default='').strip()
        if county:
            processed_entity['county'] = county
    elif company:
        processed_entity['organization'] = company
    processed_entity['street'] = entity.findtext('STREET', default='').strip()
    processed_entity['city'] = entity.findtext('CITY', default='').strip()
    # County not mentioned in XML
    if name:
        processed_entity['county'] = ""
    processed_entity['state'] = entity.findtext('STATE', default='').strip()
    processed_entity['zip'] = process_zip(entity.findtext('POSTAL_CODE', default=''))  
    return processed_entity


# TSV-files processing and helper function
def process_tsv_file(file_path):
    entities = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            tsv_reader = csv.DictReader(file, delimiter='\t')
            for row in tsv_reader:
                entities.append(process_tsv_row(row))
    except FileNotFoundError:
        logging.error(f"TSV file not found: {file_path}")
        sys.exit(1)
    except PermissionError:
        logging.error(f"Permission denied: {file_path}")
        sys.exit(1)
    except csv.Error as e:
        logging.error(f"CSV parsing error in file {file_path}: {e}")
        sys.exit(1)
    except Exception as e:
        log_exception(e, file_path)
        sys.exit(1)
        
    entities_sorted = sorted(entities, key=lambda x: (x['zip'] == "", x['zip']))
    return entities_sorted

## Helper tsv processor
def process_tsv_row(row):
    processed_entity = {}
    name = ""
    if row.get('organization', 'N/A') != 'N/A':
        processed_entity['organization'] = row.get('organization', '').strip()
    else:
        first_name = row.get('first', '').strip()
        #Filtering no middle name
        middle_name = row.get('middle', '').strip().replace("N/M/N", "").strip()
        last_name = row.get('last', '').strip()
        
        # Check if the last name has more than two words, indicating an organization
        if len(last_name.split()) > 2:
            processed_entity['organization'] = last_name
        else:
            # If not an organization,
            name_parts = [first_name, middle_name, last_name]
            name = ' '.join(part for part in name_parts if part).strip()
            processed_entity['name'] = name
        
    processed_entity['street'] = row.get('address', '').strip()
    processed_entity['city'] = row.get('city', '').strip()
    if name:
        processed_entity['county'] = row.get('county', "").strip()
    processed_entity['state'] = row.get('state', '').strip()
    processed_entity['zip'] = process_zip(row.get('zip', '') + ('-' + row.get('zip4') if row.get('zip4') else '')).strip()

    return processed_entity

# Text processing and helper function
def process_txt_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            txt_entities = file.read().strip().split('\n\n')
            entities = [process_txt_entity(entity) for entity in txt_entities]
            entities = sorted(entities, key=lambda x: x['zip'])
            return entities
    except FileNotFoundError:
        logging.error(f"TXT file not found: {file_path}")
        logging.debug(FileNotFoundError, exc_info=True)
        sys.exit(1)
    except PermissionError:
        logging.error(f"Permission denied: {file_path}")
        logging.debug(PermissionError, exc_info=True)
        sys.exit(1)
    except Exception as e:
        log_exception(e, file_path)
        sys.exit(1)
        
## Helper text processor
def process_txt_entity(entity):
    lines = entity.strip().split('\n')
    county = None
    # Finding appropriate county | MARICOPA COUNTY, if word COUNTY exists
    for line in lines:
            if 'COUNTY' in line.upper():
                words = line.split()
                county_index = next((i for i, word in enumerate(words) if word.upper() == 'COUNTY'), None)
                if county_index and county_index > 0:
                    county = words[county_index - 1]
                break
    city_state_zip = lines[-1]
    entities = {
        'name': lines[0].strip(),
        'street': lines[1].strip(),
        'county': "" if county is None else county,
        'city': ' '.join(city_state_zip.split()[:-2]).replace(',', ''),
        'state': city_state_zip.split()[-2].replace(',', ''),
        'zip': process_zip(city_state_zip.split()[-1])
    }
    return entities

# Zip error handling
def process_zip(postal_code):
    postal_code = postal_code.strip()
    #if first 5 digist doesnt exist | eg: " - 1234"
    parts = postal_code.split("-")       
    if len(parts[0].strip()) == 0: 
        return ""
      
    if len(parts) == 1 or len(parts[1].strip()) == 0:
        return parts[0].strip()
    
    return f'{parts[0].strip()}-{parts[1].strip()}'

# Exception Logger
def log_exception(file_path,exception):
    logging.error(f"Error processing file {file_path}: {exception}")
    logging.debug(exception, exc_info=True)

#Main Function
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process multiple address files.')
    parser.add_argument('file_paths', type=str, nargs='+', help='Path(s) to the input file(s).')
    args = parser.parse_args()
    success = True
    for file_path in args.file_paths:
        file_extension = file_path.split('.')[-1].lower()
        processing_functions = {
            'xml': process_xml_file,
            'tsv': process_tsv_file,
            'txt': process_txt_file
        }

        if file_extension not in processing_functions:
            logging.error(f"Unsupported file extension: {file_extension} | {file_path} ")
            logging.warning(f"Unsupported file extension: {file_extension} | This File:{file_path}  shall be skipped")
            success = False
            continue
        try:
            results = processing_functions[file_extension](file_path)
            print(json.dumps(results, indent=4))
            
        except Exception as e:
            success = False
            logging.error(f"Error processing file {file_path}: {e}")
            log_exception(file_path,e)
            continue
        
    #Check Exit status
    if success:
        sys.exit(1)
    else:
        sys.exit(0)