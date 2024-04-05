import argparse
import xml.etree.ElementTree as ET
import csv
import json
import sys

# Function to parse XML files
def parse_xml(file):
    try:
        # Parse the XML file and get the root element
        tree = ET.parse(file)
        root = tree.getroot()
    except ET.ParseError as e:
        # Handle parsing errors
        sys.stderr.write(f"Error parsing XML file {file}: {str(e)}\n")
        return []

    # Initialize a list to store the data
    xml_data = []
    # Iterate over each 'ENT' element in the XML
    for ent in root.findall('.//ENT'):
        # Initialize a dictionary to store the row data
        row = {}
        # Iterate over each child element in the 'ENT' element
        for child in ent:
            # Handle 'POSTAL_CODE' element separately
            if child.tag == 'POSTAL_CODE':
                # Remove spaces from the text and remove trailing '-' if present
                row['zip'] = child.text.replace(' ','')[:-1] if child.text.replace(' ','').endswith('-') else child.text.replace(' ','')
            # Ignore 'COUNTRY' element and empty elements
            elif child.tag != 'COUNTRY' and child.text.strip() != '':
                # Add the element to the row dictionary
                row[child.tag.lower()] = child.text.strip()
        # Add the row to the data list if it's not empty
        if row:
            xml_data.append(row)
    # Return the parsed data
    return xml_data

# Function to parse TSV files
def parse_tsv(file):
    # Initialize a list to store the data
    tsv_data = []
    try:
        # Open the TSV file
        with open(file, 'r') as f:
            # Create a CSV reader with tab delimiter
            reader = csv.reader(f, delimiter='\t')
            # Get the headers from the first row
            headers = next(reader)
            # Iterate over each row in the file
            for row in reader:
                # Create a dictionary from the row using the headers as keys
                row_dict = dict(zip(headers, row))
                # Initialize a dictionary to store the record data
                record = {}
                # Check if the name contains a business entity type
                if any(x in ' '.join([row_dict['first'],row_dict['middle'],row_dict['last']]).strip() for x in ['llc','inc','ltd']):
                    # If so, set the name to empty and the company to the full name
                    record['name'] = ''
                    record['company'] = ' '.join([row_dict['first'],row_dict['middle'],row_dict['last']]).strip()
                else:
                    # Otherwise, set the name to the full name and the company to the organization
                    record['name'] = ' '.join([row_dict['first'],row_dict['middle'],row_dict['last']]).strip()
                    record['company'] = row_dict['organization'].strip() if 'n/a' not in row_dict['organization'].lower() else ''
                # Add the rest of the fields to the record
                record['street'] = row_dict['address'].strip()
                record['city'] = row_dict['city'].strip()
                record['state'] = row_dict['state'].strip()
                # Handle the zip code and zip4 fields separately
                record['zip'] = '-'.join([row_dict['zip'].strip(),row_dict['zip4'].strip()]).strip() if row_dict['zip4'].strip() else row_dict['zip'].strip()
                # Remove empty fields from the record
                row_dict = {k: v for k, v in record.items() if v.strip() != ''}
                # Add the record to the data list if it's not empty
                if row_dict:
                    tsv_data.append(row_dict)
    except csv.Error as e:
        # Handle reading errors
        sys.stderr.write(f"Error reading TSV file {file}: {str(e)}\n")
    # Return the parsed data
    return tsv_data

# Function to parse TXT files
def parse_txt(file):
    # Initialize a list to store the data
    data = []
    try:
        # Open the TXT file
        with open(file, 'r') as file:
            # Split the file into records by empty line
            lines = file.read().split('\n\n')
        # Iterate over each record
        for line in lines:
            # Split the record into fields by newline
            elements = line.split('\n')
            # Ensure there are enough fields
            if len(elements) >= 3:
                # Create a dictionary from the fields
                record = {
                    'name': '' if any(x in elements[0].lower() for x in ['llc','inc','ltd']) else elements[0].strip(),
                    'company': elements[0].strip() if any(x in elements[0].lower() for x in ['llc','inc','ltd']) else '',
                    'street': elements[1].strip(),
                    'city': elements[-1].split(',')[0].strip(),
                    'county': elements[2].split()[0].strip() if len(elements) > 3 else '',
                    'state': elements[-1].split(',')[1].split()[0].strip(),
                    'zip': elements[-1].split()[-1].replace(" ", "")
                }
                # Remove empty fields from the record
                record = {k: v for k, v in record.items() if v.strip() != ''}
                # Remove trailing '-' from the zip code if present
                record['zip'] = record['zip'][:-1] if record['zip'].endswith('-') else record['zip']
                # Add the record to the data list
                data.append(record)
    except IOError as e:
        # Handle reading errors
        sys.stderr.write(f"Error reading TXT file {file}: {str(e)}\n")
    # Return the parsed data
    return data

def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Parse address files and output JSON.')
    # Add a 'files' argument that takes a list of files to parse
    parser.add_argument('--files', nargs='+', required=True, help='a list of files to parse')
    # Parse the command line arguments
    args = parser.parse_args()

    # Initialize a list to store the data
    data_list = []
    # Iterate over each file in the 'files' argument
    for f in args.files:
        # Check the file extension and call the appropriate parsing function
        if  f.endswith('.xml'):
            data_list += parse_xml(f)
        elif f.endswith('.tsv'):
            data_list += parse_tsv(f)
        elif  f.endswith('.txt'):
            data_list += parse_txt(f)
        else:
            # Write an error message for unrecognized file types
            sys.stderr.write(f"Skipping unrecognized file type: {f}\n")
    # Check if any data was parsed
    if data_list:
        # Sort the data by the first 5 digits of the zip code and convert it to JSON
        object = json.dumps(sorted(data_list, key=lambda x: x['zip'][:5]), indent=2)
        # Print the JSON data
        print(object)
        # Return 0 to indicate success
        return 0
    else:
        # Return 1 to indicate failure
        return 1

if __name__ == "__main__":
    sys.exit(main())