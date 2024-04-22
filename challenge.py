import xml.etree.cElementTree as ET
import json
import csv
import sys
import argparse


def parse_xml(file_path):
    # Load and parse the XML file
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        return None, f"Error parsing XML file: {e}"
    except FileNotFoundError:
        return None, f"XML file not found: {file_path}"

    res = []

    # Access the ENTITY/ENT section
    for ent in root.findall('.//ENT'):
        temp  = {} # Dictionary to store the entity details

        # Get temp varibles to make it easy to read
        name = ent.find('NAME').text
        organization = ent.find('COMPANY').text
        street = ent.find('STREET').text
        city = ent.find('CITY').text
        state = ent.find('STATE').text
        postal_code = ent.find('POSTAL_CODE').text

        # Throw error if there is blank message
        if not name+organization+street+city+state+postal_code:
                        return None, f"Missing or empty required field '{tag}' in XML"
        if name != " ":
            temp['name'] = name
        
        elif organization != " ":
            temp['organization'] = organization

        temp['street'] = street
        temp['city'] = city
        temp['state'] = state
        # No county stored in xml


        # To let zip in the format 00000 or 00000-0000
        if len(postal_code) > 8:
            temp['zip'] = postal_code[:5] + '-' + postal_code[-4:]
        else:
            temp['zip'] = postal_code[:5]


        # Create a temp value to store the zip for sorting
        if "-" in temp['zip']:
            temp["fake_zip"] = postal_code[:5]+postal_code[-4:]
        else:
            temp["fake_zip"] = postal_code+"0000"

        res.append(temp) # Add the dictionary to the result array
    res.sort(key=lambda x: x['fake_zip'])
    
    for i in res:
        del i['fake_zip']

    return res, None



def parse_tsv(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            res = []
            for row in reader:
                temp = {}
                
                # To create the whole name
                first = row['first'].strip()
                middle = row['middle'].strip() 
                last = row['last'].strip()
                name = ""
                if first:
                    name += first + ' '
                if middle and middle != "N/M/N": # N/M/N = no middle name
                    name += middle +' '
                if last:
                    name += last +' '
                name = name[:-1]

                organization = row['organization'].strip() 


                # Store basic info for address
                street = row['address'].strip()
                city = row['city'].strip()
                state = row['state'].strip()
                county = row['county'].strip()

                if name:
                    temp['name'] = name
                
                elif organization:
                    temp['organization'] = organization

                temp['street'] = street
                temp['city'] = city
                if county:
                    temp['county'] = county
                temp['state'] = state


                # Get the zip 
                zip_code = row['zip'].strip()
                zip4 = row['zip4'].strip()
                if zip4:
                    temp['zip'] = zip_code+"-"+zip4
                    temp['fake_zip'] = zip_code+zip4
                else:
                    temp['zip'] = zip_code
                    temp['fake_zip'] = zip_code+'0000'

                res.append(temp)

            res.sort(key=lambda x: x['fake_zip'])
            
            # To delete useless column
            for i in res:
                del i['fake_zip']

            file.close()
            return res, None
    
    except FileNotFoundError:
        return None, f"TSV file not found: {file_path}"
    except csv.Error as e:
        return None, f"Error reading TSV file: {e}"

def parse_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # Read all lines and split into blocks separated by blank lines
            content = file.read().strip()
            blocks = content.split('\n\n')

            res = []
            for block in blocks:
                lines = block.strip().split('\n')
                temp = {}

                temp['name'] = lines[0].strip()
                # No company name in txt

                temp['street'] = lines[1].strip()

                if len(lines) == 4:
                    temp['county'] = lines[2].strip()[:-7]

                address = lines[-1].strip().split(',')
                temp['city'] = address[0]
                state_add = address[1].split()
                temp['state'] = ' '.join(state_add[0:-1]) # To combine the name like New Jersy


                postal_code = state_add[-1]


                # To let zip in the format 00000 or 00000-0000
                if len(postal_code) == 5:
                    temp['zip'] = postal_code
                elif 5 < len(postal_code) < 9:
                    temp['zip'] = postal_code[:5]
                else:
                    temp['zip'] = postal_code[:5] + '-' + postal_code[-4:]


                # Create a temp value to store the zip for sorting
                if "-" in temp['zip']:
                    temp["fake_zip"] = postal_code[:5]+postal_code[-4:]
                else:
                    temp["fake_zip"] = postal_code+"0000"

                res.append(temp) # Add the dictionary to the result array
            res.sort(key=lambda x: x['fake_zip'])

            # To delete useless column
            for i in res:
                del i['fake_zip']

            file.close()
            return res, None

    except FileNotFoundError:
        return None, f"TXT file not found: {file_path}"


def save_to_json(data, output_path):
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)
    except IOError as e:
        return f"Failed to write JSON output to {output_path}: {e}"
    return None

def main(args):

    # Uses argparse to manage command-line arguments and provide a --help option.
    if args.xml:
        data, error = parse_xml(args.xml)
        if error:
            sys.stderr.write(error + "\n")
            sys.exit(1)
        error = save_to_json(data, 'output1.json')
        if error:
            sys.stderr.write(error + "\n")
            sys.exit(1)

    if args.tsv:
        data, error = parse_tsv(args.tsv)
        if error:
            sys.stderr.write(error + "\n")
            sys.exit(1)
        error = save_to_json(data, 'output2.json')
        if error:
            sys.stderr.write(error + "\n")
            sys.exit(1)

    if args.txt:
        data, error = parse_txt(args.txt)
        if error:
            sys.stderr.write(error + "\n")
            sys.exit(1)
        error = save_to_json(data, 'output3.json')
        if error:
            sys.stderr.write(error + "\n")
            sys.exit(1)

    print("All files processed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process XML, TSV, and TXT files into JSON.")
    parser.add_argument('--xml', help="Path to the XML file")
    parser.add_argument('--tsv', help="Path to the TSV file")
    parser.add_argument('--txt', help="Path to the TXT file")
    args = parser.parse_args()
    print(args)

    main(args)

