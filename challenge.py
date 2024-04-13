import json
import sys
import argparse
from xml.etree import ElementTree
import csv
import re

def parse_xml(file_path):
    tree = ElementTree.parse(file_path)
    root = tree.getroot()
    addresses = []
    for element in root.findall('.//address'):
        data = {
            'name': element.find('.//name').text if element.find('.//name') is not None else None,
            'organization': element.find('.//organization').text if element.find('.//organization') is not None else None,
            'street': element.find('.//street').text,
            'city': element.find('.//city').text,
            'county': element.find('.//county').text if element.find('.//county') is not None else None,
            'state': element.find('.//state').text,
            'zip': element.find('.//zip').text,
        }
        addresses.append(data)
    return addresses

def parse_tsv(file_path):
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter='\t')
        return [row for row in reader]


def parse_txt(file_path):
  addresses = []
  with open(file_path, 'r') as file:
    content = file.read().strip().split('\n\n')
    for entry in content:
      try:
        lines = entry.split('\n')
        city_state_zip = lines[-2].split(',')[-1].strip().split(' ')
        # Ensure we have at least one comma to separate city and state/zip
        if len(city_state_zip) < 2:
          raise ValueError("City, State, and ZIP code not in expected format.")

        # Extracting ZIP code which could be in different formats
        zip_code = ' '.join(city_state_zip[-2:])

        data = {
          'name': None,
          'organization': None,
          'street': lines[1],
          'city': city_state_zip[0],
          'county': None,
          'state': city_state_zip[-2],
          'zip': zip_code,
        }

        if 'COUNTY' in lines[0].upper():
          data['county'] = lines[0]
        elif ',' in lines[0] or len(lines[0].split()) > 1:
          data['name'] = lines[0]
        else:
          data['organization'] = lines[0]

        addresses.append(data)
      except IndexError as e:
        print(f"Error in entry: {entry}: {e}", file=sys.stderr)
        return None
      except ValueError as e:
        print(f"Error in entry: {entry}: {e}", file=sys.stderr)
        return None
  return addresses


def sort_and_output_json(data):
    sorted_data = sorted(data, key=lambda x: x['zip'])
    print(json.dumps(sorted_data, indent=2))

def main():
    parser = argparse.ArgumentParser(description='Process address files and output JSON sorted by ZIP code.')
    parser.add_argument('files', metavar='F', type=str, nargs='+', help='path to the input files')
    args = parser.parse_args()

    combined_addresses = []
    errors_occurred = False
    for file_path in args.files:
        if not file_path.endswith(('.xml', '.tsv', '.txt')):
          print(f"Error: Unsupported file format for file {file_path}", file=sys.stderr)
          errors_occurred = True
          break
        try:
            if file_path.endswith('.xml'):
                addresses=parse_xml(file_path)
            elif file_path.endswith('.tsv'):
                addresses=parse_tsv(file_path)
            elif file_path.endswith('.txt'):
                addresses = parse_txt(file_path)
            if addresses is None:  # An error occurred during parsing
              errors_occurred = True
              break
            combined_addresses.extend(addresses)
        except Exception as e:
            print(f"Error processing file {file_path}: {e}", file=sys.stderr)
            errors_occurred = True
            break

    if not errors_occurred and combined_addresses:
      sort_and_output_json(combined_addresses)
      sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
