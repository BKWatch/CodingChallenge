import argparse
import json
import os
import sys
from xml_parser import XMLParser
from tsv_parser import TSVParser
from text_parser import TextParser

def custom_zip_key(address):
    zip_code = address.get('zip', '')
    if '-' in zip_code:
    # If hyphen exists, split the string and take the first part
        first_zip_part = zip_code.split('-')[0].strip()
    else:
    # If hyphen doesn't exist, take the whole string as the ZIP code
        first_zip_part = zip_code.strip()
    
    return first_zip_part

def main():
    parser = argparse.ArgumentParser(description='Parse US names and addresses from various file formats')
    parser.add_argument('files', metavar='file', type=str, nargs='+', help='input files to parse (supported formats: .xml, .tsv, .txt)')
    args = parser.parse_args()

    if not args.files:
        sys.stderr.write("Error: No input files provided.")
        sys.exit(1)
    

    

    addresses = []
    valid_formats = ['.xml', '.tsv', '.txt']
    for file_path in args.files:
        ext = os.path.splitext(file_path)[1].lower()
        if not os.path.exists(file_path):
            sys.stderr.write("Error: No input files provided or path does not exist.")
            sys.exit(1)
        try:
       
            if ext == '.xml':
                addresses.extend(XMLParser.parse(file_path))
            elif ext == '.tsv':
                addresses.extend(TSVParser.parse(file_path))
            elif ext == '.txt':
                addresses.extend(TextParser.parse(file_path))
            else:
                sys.stderr.write(f"Unsupported file format: {ext}\n")
                sys.exit(1)
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}", file=sys.stderr)
            sys.exit(1)

    if addresses:
        addresses.sort(key=custom_zip_key)

        try:
            json_addresses = json.dumps(addresses, indent=2)
            with open("output.json", "w") as json_file:
                json_file.write(json_addresses)
                print("Success: Addresses successfully written to output.json", file=sys.stdout)
                sys.exit(0)
            
           
        except Exception as e:
            sys.stderr.write(f"Error encoding addresses to JSON: {str(e)}\n")
            sys.exit(1)
    else:
        sys.stderr.write("No addresses found.\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
