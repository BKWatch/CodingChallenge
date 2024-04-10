"""
This script parses XML, TSV, and TXT files to extract name and address information, sorts the entries by ZIP code, and outputs them in JSON format.

Usage:
    python challenge.py input1.xml input2.tsv input3.txt

Author: Gabriel Rabanal
Original coding challenge URL: https://github.com/BKWatch/CodingChallenge
"""

import argparse
import json
import re
import sys
from xml.etree import ElementTree as ET


def parse_file(filepath):
    """
    Parse a file based on its extension (XML, TSV or TXT). Returns a list of entries parsed from the file.
    """
    ext = filepath.split('.')[-1].lower()
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            if ext == 'xml':
                return parse_xml(file)
            elif ext == 'tsv':
                return parse_tsv(file.readlines())
            elif ext == 'txt':
                return parse_txt(file.readlines())
            else:
                raise RuntimeError(f"Unsupported file format: {ext}")
    except Exception as e: 
        # Write error message to stderr and exit with status 1
        sys.stderr.write(f"Error occurred while parsing file '{filepath}': {e}\n")
        sys.exit(1)


def parse_xml(file):
    """
    Parse an XML file and return a list of dictionaries representing the entries.
    """
    entries = []
    try:
        tree = ET.parse(file)
        # Iterate over each 'ENT' element in XML tree
        for ent in tree.findall('.//ENT'):
            entry = {}
            # Iterate over each child element of 'ENT' element
            for element in ent:
                # Extract content of element
                if element.text and element.text.strip() != '':
                    text = element.text.strip()
                    # Map element tags to lowercase and handle accordingly
                    if element.tag.lower() in ['name', 'street', 'city', 'county', 'state']:
                        entry[element.tag.lower()] = text
                    elif element.tag == 'COMPANY':
                        entry['organization'] = text
                    elif element.tag == 'POSTAL_CODE':
                        entry['zip'] = normalize_zip(text) # Normalize ZIP code and add to entry
            entries.append(entry) # Add parsed entry to list of entries
    except Exception as e:
        # Write error message to stderr and exit with status 1
        sys.stderr.write(f"Error occurred while parsing XML file: {e}\n")
        sys.exit(1)
    return entries


def parse_tsv(lines):
    """
    Parse a TSV file and return a list of dictionaries representing the entries.
    """
    entries = []
    try:
        # Parse headers from first line and convert to lowercase
        headers = [header.lower() for header in lines[0].split('\t')]
        
        # Iterate over each line (excluding line of headers) and create entries
        for line in lines[1:]:
            values = line.split('\t')  # Split line into values
            ent = {headers[i]: values[i].strip() for i in range(len(values))}  # Create a dictionary for the entry

            entry = {} # Initialize empty dictionary to hold current entry 
            
            # Determine if it's an organization, or a person
            if not ent.get('first') and not ent.get('middle'):
                if ent.get('organization', 'N/A') != 'N/A':
                    entry['organization'] = ent['organization']
                elif ent.get('last'):
                    entry['organization'] = ent['last']
            else:
                # Set person's name based on first, middle, and last names
                first_name  = ent.get('first', '')
                middle_name = ent.get('middle', 'N/M/N')
                last_name   = ent.get('last', '')
                if middle_name == 'N/M/N':
                    entry['name'] = ' '.join([first_name, last_name]) # Ignore middle name
                else:
                    entry['name'] = ' '.join([first_name, middle_name, last_name])  # Combine first, middle, and last
            # Map remaining attributes to entry, with special handling for 'address' tag
            for tag in ['address', 'city', 'county', 'state']:
                if ent.get(tag):
                    if tag == 'address':
                        entry['street'] = ent[tag]
                    else:
                        entry[tag] = ent[tag]
            # Combine ZIP and ZIP+4 if available
            entry['zip'] = ent['zip'] + ('-' + ent['zip4'] if ent.get('zip4') else '')
            entries.append(entry)  # Add entry to the list of entries
    except Exception as e:
        # Write error message to stderr and exit with status 1
        sys.stderr.write(f"Error occurred while parsing TSV file: {e}\n")
        sys.exit(1)
    return entries


def parse_txt(lines):
    """
    Parse a TXT file and return a list of dictionaries representing the entries.
    """
    entries = []
    try:
        current_entry = {}  # Initialize an empty dictionary to hold the current entry being processed
        for line in lines:
            line = line.strip()  # Remove leading and trailing whitespaces
            if line:  
                if not current_entry.get("name"): # If name field is not yet in entry
                    current_entry["name"] = line  
                elif 'street' not in current_entry:  # If 'street' field is not yet in entry
                    current_entry["street"] = line  
                elif 'county' not in current_entry and 'COUNTY' in line:  # If 'county' is not yet in entry & 'COUNTY' is in line
                    parts = line.split(' ')  
                    current_entry["county"] = parts[0].strip()  # Assign first word to 'county' field
                elif 'city' not in current_entry:  # If 'city' field is not yet present in entry
                    # Parse address line to extract city, state, and ZIP code
                    city, state, zip_code  = parse_address(line)
                    current_entry["city"]  = city  
                    current_entry["state"] = state  
                    current_entry["zip"]   = zip_code  
            else:  # If line is empty
                if current_entry:  # If there's a current entry being processed
                    # Swap order of 'city' and 'county' if present
                    if 'city' in current_entry and 'county' in current_entry:
                        entry = {
                            'name'  : current_entry.get('name', ''),
                            'street': current_entry.get('street', ''),
                            'city'  : current_entry.get('city', ''),
                            'county': current_entry.get('county', ''),
                            'state' : current_entry.get('state', ''),
                            'zip'   : current_entry.get('zip', '')
                        }
                        current_entry = entry
                    entries.append(current_entry)  
                    current_entry = {}  # Reset current entry dictionary
    except Exception as e:
        # Write error message to stderr and exit with status 1
        sys.stderr.write(f"Error occurred while parsing TXT file: {e}\n")
        sys.exit(1) 
    return entries  


def normalize_zip(zip_code):
    """
    Normalize a ZIP code in the format '00000' or '00000-0000'.
    """
    # Remove all spaces and trailing hyphen(s)
    zip_code_cleaned = zip_code.replace(' ', '').rstrip('-')
    return zip_code_cleaned


def parse_address(address):
    """
    Returns the city, state, and ZIP code from a US address string.
        "Belleville, New Jersey 07109-" -> ["Belleville", "New Jersey", "07109"]
    Returns an list of empty strings if the format is invalid.
    """
    # Initialize variables to store city, state, and ZIP code
    city = state = zip_code = ''

    # Extract city, state, and ZIP code from the address string
    city_state_zip_match = re.match(r'(.+),([A-Za-z -]+)\s*([\d-]*)', address)
    if city_state_zip_match:
        city     = city_state_zip_match.group(1)
        state    = city_state_zip_match.group(2).strip()
        zip_code = normalize_zip(city_state_zip_match.group(3))

    return [city, state, zip_code]


def main(args):
    all_entries = []
    for filepath in args.files:
        all_entries.extend(parse_file(filepath))
    sorted_entries = sorted(all_entries, key=lambda x: x.get('zip', ''))
    print(json.dumps(sorted_entries, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This script parses XML, TSV, and TXT files to extract name and address information, sorts the entries by ZIP code, and outputs them in JSON format.")
    parser.add_argument('files', nargs='+', help="One or more file paths to be parsed. Supports XML, TSV, and TXT formats.")
    args = parser.parse_args()
    main(args)