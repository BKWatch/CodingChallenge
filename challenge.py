import sys, csv, argparse, json
from pathlib import Path
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET

XML_COL_MAP = [
    ("NAME", "name"),
    ("COMPANY", "organization"),
    ("STREET", "street"),
    ("CITY", "city"),
    ("STATE", "state"),
    ("POSTAL_CODE", "zip")
]

class LineNumberingParser(ET.XMLParser):
    def _start(self, *args, **kwargs):
        element = super(self.__class__, self)._start(*args, **kwargs)
        element._start_line_number = self.parser.CurrentLineNumber
        element._start_column_number = self.parser.CurrentColumnNumber
        element._start_byte_index = self.parser.CurrentByteIndex
        return element

    def _end(self, *args, **kwargs):
        element = super(self.__class__, self)._end(*args, **kwargs)
        element._end_line_number = self.parser.CurrentLineNumber
        element._end_column_number = self.parser.CurrentColumnNumber
        element._end_byte_index = self.parser.CurrentByteIndex
        return element


def parse_xml(file_path: str) -> list[dict]:
    entries = [] # stores results
    def get_xml_elmt_loc(ent)->str:
        return f"Line:{ent._start_line_number} Col:{ent._start_column_number}"

    root = ET.parse(file_path, parser=LineNumberingParser()).getroot()
    for ent in root.findall('.//ENTITY/ENT'):
        
        entry = {}
        for from_col, to_col in XML_COL_MAP:
            entry[to_col] = (ent.find(from_col).text or '').strip()

        if entry['name'] and entry['organization']:
            # A personal name or organization name will always be present, but not both.
            raise Exception(f"Entry with both a NAME and COMPANY found in '{file_path}'.  {get_xml_elmt_loc(ent)}")
        elif entry['name']:
            entry.pop('organization')
        elif entry['organization']:
            entry.pop('name')
        else:
            # A personal name or organization name will always be present, but not both.
            raise Exception(f"Entry without a NAME or COMPANY found in '{file_path}'.  {get_xml_elmt_loc(ent)}")
    
        street_2 = (ent.find('STREET_2').text or '').strip()
        street_3 = (ent.find('STREET_3').text or '').strip()
        entry['street'] = ', '.join([street for street in [entry['street'], street_2, street_3] if street.strip()])
            
        entry['zip'] = entry['zip'].replace(' ','').rstrip('-')
        
        # Stricter controls to throw error on missing data
        for col in ('street', 'city', 'state', 'zip'):
            if not entry[col]:
                raise Exception(f"Entry with missing value, {col}, found in '{file_path}'  {get_xml_elmt_loc(ent)}")
        
        entries.append(entry)
    if not entries:
        raise Exception(f"Did not find any entries in '{file_path}'")
    return entries

TSV_COLS = [
    'first', 
    'middle', 
    'last', 
    'organization', 
    'address', 
    'city', 
    'state', 
    'county', 
    'zip', 
    'zip4'
]

def parse_tsv(file_path: str) -> list[dict]:
    entries = []
    with open(file_path, 'r', newline="") as tsv_file:
        reader = csv.reader(tsv_file, delimiter='\t')
        header = next(reader)
        line_no = 1
        if header != TSV_COLS:
            raise Exception(f"TSV columns do not match schema.  File:'{file_path}'")
        for row in reader:
            line_no+=1
            if len(row) < 10:
                raise Exception(f"Data row is missing columns.  File:'{file_path}'.  Line:{line_no}")
            
            entry = {}
            first, middle, last, organization, street, city, state, county, zipcode, zip4 = row[:10]
            
            name = ' '.join([name_part.strip() for name_part in (first, middle, last) if name_part.strip()])
            organization = organization.strip()
            organization = organization if organization.upper() != "N/A" else ''
            
            if name and organization:
                raise Exception(f"Entry with both a name and organization found in '{file_path}'.  Line:{line_no}")
            if name:
                entry['name'] = name
            elif organization:
                entry['organization'] = organization
            else:
                raise Exception(f"Entry without a name or organization found in '{file_path}'.  Line:{line_no}")
    
            entry['street'] = street.strip()
            entry['city'] = city.strip()
            entry['county'] = county.strip()
            entry['state'] = state.strip()
            entry['zip'] = zipcode.strip()
            if not entry['zip']:
                raise Exception(f"Entry with missing value, zipcode, found in '{file_path}'.  Line:{line_no}")
            zip4 = zip4.strip()
            if zip4:
                entry['zip'] = f"{entry['zip']}-{zip4}"
            
            if not entry['county']:
                entry.pop('county')
                
            # Stricter controls to throw error on missing data
            for col in ('street', 'city', 'state', 'zip'):
                if not entry[col]:
                    raise Exception(f"Entry with missing value, {col}, found in '{file_path}'.  Line:{line_no}")
    
            entries.append(entry)
        if not entries:
            raise Exception(f"Did not find any entries in '{file_path}'")
    return entries


def parse_txt_group(group:list[str], file_path:str)->dict:
    if len(group) < 3:
        raise Exception(f"Entry with missing rows found in '{file_path}'.  Entry {group}")
    elif len(group) > 4:
        raise Exception(f"Entry with too many rows found in '{file_path}'.  Entry {group}")

    entry = {}
    entry['name'] = group[0]
    entry['street'] = group[1]
    
    county, city_line = '', ''
    if len(group) == 4:
        if len(group[2]) < 9 or group[2][-7:].upper() != " COUNTY":
            raise Exception(f"County line not in expected format (ex. GENERAL COUNTY) in file '{file_path}'.\nEntry {group}")
        county = group[2][:-7]#.title()  #Leaving case alone for now
        city_line = group[3].strip()
    else:
        city_line = group[2].strip()
        
    city_spl = city_line.split(',')
    if len(city_spl) != 2:
        raise Exception(f"City line not in expected format (ex. City, AA 12345) in file '{file_path}'.\nEntry {group}")
        
    entry['city'] = city_spl[0].strip()
    if not entry['city']:
        raise Exception(f"City line not in expected format (ex. City, AA 12345) in file '{file_path}'.\nEntry {group}")

    if county:
        entry['county'] = county
        
    state_spl = city_spl[1].strip().split()
    if len(state_spl) < 2:
        raise Exception(f"City line not in expected format (ex. City, AA 12345) in file '{file_path}'.\nEntry {group}")
    entry['state'] = ' '.join(state_spl[:-1])
    entry['zip'] = state_spl[-1].rstrip('-')
    
    return entry
    

def parse_txt(file_path: str) -> list[dict]:
    with open(file_path, 'r', encoding='utf-8') as file:
        entries = []
        group = []

        # no need to read the whole file into memory at once
        for line in file:
            line = line.strip()
            
            if line:
                group.append(line)
                continue
    
            if group:
                entry = parse_txt_group(group, file_path)
                entries.append(entry)
                group = []
        
        # catch last group if no blank line at EOF
        if group:
            entry = parse_txt_group(group, file_path)
            entries.append(entry)
            
        return entries


def check_files_exist(file_list: list[str]) -> bool:
    for file_path in file_list:
        if not Path(file_path).is_file():
            raise Exception(f"Input file not found.  File:{file_path}")
    return True

def check_files_extension(file_list: list[str]) -> bool:
    for file_path in file_list:
        if len(file_path) < 4 or file_path[-4:] not in set([".xml", ".tsv", ".txt"]): 
            raise Exception(f"File not in recognized format (xml, tsv, txt).  File: {file_path}")
    return True

def generate_json(entries: list[dict])->str:
    entries_sorted = sorted(entries, key=lambda x: x.get('zip', ''))
    entries_json = json.dumps(entries_sorted, indent=2)
    return entries_json

def main(file_list: list[str]):
    try:
        check_files_extension(file_list)
        check_files_exist(file_list)
        results = []
        for file_path in file_list:
            ext = file_path[-3:].lower()
            if ext == "xml":
                results += parse_xml(file_path)
            elif ext == "tsv":
                results += parse_tsv(file_path)
            elif ext == "txt":
                results += parse_txt(file_path)

        json_results = generate_json(results)
        print(json_results)
            
    except Exception as e:
        print(getattr(e, 'message', str(e)), file=sys.stderr)
        sys.exit(1)


def get_args()->[argparse.Namespace]:
    parser = argparse.ArgumentParser(description='Parses addresses from multiple file formats (xml/tsv/txt)')
    parser.add_argument('-files', '--file-list', nargs='+', default=[], help='Space seperated list of files to parse')
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    main(args.file_list)

