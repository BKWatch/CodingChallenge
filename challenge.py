"""
BankruptcyWatch Coding Challenge
Date: 04/17/2024
Author: Swetha Arunraj
Description: This script parses address data from XML, TSV, and TXT files, 
             combines them into a single list, sorts the list by ZIP code, 
             and outputs the result as a JSON-formatted string to the standard output.
Contact: swe.arunraj@gmail.com
"""

import argparse
import sys
import json
import csv
from xml.etree import ElementTree as ET

def parse_args():
    """
    Parse command line arguments.
    Returns a namespace object with file paths provided by the user.
    """
    parser = argparse.ArgumentParser(
        description='Parse and combine addresses from various file formats into'
                    ' a sorted JSON output based on zip.')
    parser.add_argument(
        'files', nargs='+', 
        help='List of file paths to parse. Files should be in XML, TSV, or TXT format.')
    return parser.parse_args()

def clean_zip(zip_code):
    """
    Cleans and formats the ZIP code to standard formats (XXXXX or XXXXX-XXXX).
    
    Args:
    zip_code (str): The raw ZIP code string.
    
    Returns:
    str: The cleaned ZIP code.
    """
    zip_code = zip_code.strip()
    parts = zip_code.split('-')
    if len(parts) == 1:
        return parts[0]  # Return 5-digit ZIP code
    elif len(parts) == 2 and len(parts[1]) == 4:
        return f"{parts[0]}-{parts[1]}"  # Return full ZIP+4 code
    return parts[0]
    
def clean_county(county_name):
    """
    Cleans county names by removing the word 'county' if present.
    
    Args:
    county_name (str): The raw county name.
    
    Returns:
    str: The cleaned county name.
    """
    if 'county' in county_name.lower():
        return ' '.join(word for word in county_name.split() if word.lower() != 'county')
    return county_name

def parse_xml(file_path):
    """
    Parses an XML file for addresses.
    
    Args:
    file_path (str): Path to the XML file.
    
    Returns:
    list: A list of address dictionaries parsed from the XML file.
    """
    addresses = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for entity in root.findall('.//ENT'):
            address = {}
            # Handle organization or personal name based on presence of data
            if entity.find('NAME').text.strip():
                address['name'] = entity.findtext('NAME', '').strip()
            elif entity.find('COMPANY').text.strip():
                address['organization'] = entity.findtext('COMPANY', '').strip()
            # Address field extraction
            address['street'] = entity.findtext('STREET', '').strip()
            address['city'] = entity.findtext('CITY', '').strip()
            county = entity.findtext('COUNTY', '').strip()
            if county:
                address['county'] = clean_county(county)
            address['state'] = entity.findtext('STATE', '').strip()
            address['zip'] = clean_zip(entity.findtext('POSTAL_CODE', '').strip())
            addresses.append(address)
    except ET.ParseError as e:
        sys.stderr.write(f"Error parsing XML file: {e}\n")
        sys.exit(1)
    return addresses

def parse_tsv(file_path):
    """
    Parses a TSV file for addresses.
    
    Args:
    file_path (str): Path to the TSV file.
    
    Returns:
    list: A list of address dictionaries parsed from the TSV file.
    """
    addresses = []
    try:
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                address = {}
                # Handle organization or personal name based on presence of data
                if row['organization'].strip() != 'N/A':
                    address['organization'] = row['organization'].strip()
                else:
                    name_parts = [row['first'].strip(),
                                  row['middle'].strip() if row['middle'].strip() != 'N/M/N' else '',
                                  row['last'].strip()]
                    address['name'] = ' '.join(part for part in name_parts if part)
                # Address field extraction
                address['street'] = row['address'].strip()
                address['city'] = row['city'].strip()
                if row.get('county'):
                    address['county'] = clean_county(row['county'].strip())
                address['state'] = row['state'].strip()
                address['zip'] = clean_zip(row['zip'].strip())
                addresses.append(address)
    except Exception as e:
        sys.stderr.write(f"Error parsing TSV file: {e}\n")
        sys.exit(1)
    return addresses


def parse_txt(file_path):
    """
    Parses a TXT file for addresses.
    
    Args:
    file_path (str): Path to the TXT file.
    
    Returns:
    list: A list of address dictionaries parsed from the TXT file.
    """
    addresses = []
    address_block = []

    def process_block(block):
        """
        Helper function to process blocks of text into address dictionaries.
        """
        if not block:
            return
        try:
            address = {}
            address_lines = [line.strip() for line in block.split('\n') if line.strip()]
            # Check if first line is a name or organization
            if len(address_lines[0].split()) > 1:
                address['name'] = address_lines[0]
            else:
                address['organization'] = address_lines[0]
            address['street'] = address_lines[1]
            city_state_zip_line = address_lines[-1]
            potential_county_line = address_lines[-2] if len(address_lines) > 3 else ""
            last_line_parts = address_lines[-1].split(',')
            address['city'] = last_line_parts[0].strip()            
            if "county" in potential_county_line.lower():
                address['county'] = clean_county(potential_county_line)
            state_zip_combined = last_line_parts[1].strip().split(' ')
            address['state'] = ' '.join(state_zip_combined[:-1])
            address['zip'] = clean_zip(state_zip_combined[-1])
            addresses.append(address)
        except IndexError as e:
            sys.stderr.write(f"Error processing text block due to missing data: {e}\nBlock: {block}\n")

    try:
        with open(file_path, 'r') as file:
            for line in file:
                if line.strip() == '':
                    process_block('\n'.join(address_block))
                    address_block = []
                else:
                    address_block.append(line.strip())
            process_block('\n'.join(address_block))
    except FileNotFoundError:
        sys.stderr.write(f"File not found: {file_path}\n")
        sys.exit(1)
    except IOError as e:
        sys.stderr.write(f"I/O Error: {str(e)}\n")
        sys.exit(1)
    return addresses


def main():
    """
    Main function to process files and print addresses sorted by ZIP code.
    """
    args = parse_args()
    all_addresses = []
    for file_path in args.files:
        # Ensure file has a supported format before parsing
        if not any(file_path.endswith(ext) for ext in ['.xml', '.tsv', '.txt']):
            sys.stderr.write(f"Unsupported file format for: {file_path}\n")
            sys.exit(1)
        if file_path.endswith('.xml'):
            all_addresses.extend(parse_xml(file_path))
        elif file_path.endswith('.tsv'):
            all_addresses.extend(parse_tsv(file_path))
        elif file_path.endswith('.txt'):
            all_addresses.extend(parse_txt(file_path))
    # Sort addresses by ZIP code and output them in JSON format
    sorted_addresses = sorted(all_addresses, key=lambda x: x['zip'])
    print(json.dumps(sorted_addresses, indent=4))

if __name__ == "__main__":
    main()