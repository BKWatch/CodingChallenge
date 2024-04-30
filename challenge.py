import json
import argparse
import sys
from functools import cmp_to_key

from address_parser.xml_parser import parse_xml
from address_parser.tsv_parser import parse_tsv
from address_parser.txt_parser import parse_txt


# Comparator function for sorting addresses by ZIP code
def compare_zip(address1, address2):
    zip1 = int(address1.get('zip', '0').split('-')[0])
    zip2 = int(address2.get('zip', '0').split('-')[0])
    return zip1 - zip2

# Command line argument setup
parser = argparse.ArgumentParser(description='Parse address files and output JSON')
parser.add_argument('files', metavar='F', type=str, nargs='+', help='File paths to parse')
args = parser.parse_args()


addresses = []
for file_path in args.files:
    if file_path.endswith('.xml'):
        addresses.extend(parse_xml(file_path))
    elif file_path.endswith('.tsv'):
        addresses.extend(parse_tsv(file_path))
    elif file_path.endswith('.txt'):
        addresses.extend(parse_txt(file_path))
    else:
        sys.stderr.write(f'Error: Unrecognized file format for {file_path}\n')
        sys.exit(1)

# Sort addresses by ZIP code
addresses.sort(key=cmp_to_key(compare_zip))

# Output the addresses as pretty-printed JSON
print(json.dumps(addresses, indent=2))