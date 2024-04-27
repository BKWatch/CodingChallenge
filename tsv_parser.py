import csv
import sys

class TSVParser:

    @staticmethod
    def parse(file_path):
        addresses = []
        try:
            with open(file_path, 'r') as file:
                reader = csv.DictReader(file, delimiter='\t')
                for row in reader:
                    cleaned_zip, cleaned_zip4 = TSVParser.clean_value(row.get('zip', '')), TSVParser.clean_value(row.get('zip4', ''))
                    merged_zip = cleaned_zip + " - " + cleaned_zip4 if cleaned_zip4 else cleaned_zip
                    first_name = TSVParser.clean_value(row.get('first', ''))
                    middle_name = TSVParser.clean_value(row.get('middle', ''))
                    last_name = TSVParser.clean_value(row.get('last', ''))
                    name = " ".join([first_name, middle_name, last_name]).strip()
                    organization = TSVParser.clean_value(row.get('organization', ''))
                    name_contains_keyword = any(keyword in part.lower() for part in [last_name] for keyword in ['llc', 'ltd.', 'inc.'])

                    if name_contains_keyword:
                        if organization:
                            organization += ", " + last_name
                        else:
                            organization = last_name
                        name = ""
                    address = {
                        'name': name,
                        'organization': organization,
                        'street': TSVParser.clean_value(row.get('address', '')),
                        'city': TSVParser.clean_value(row.get('city', '')),
                        'state': TSVParser.clean_value(row.get('state', '')),
                        'zip': merged_zip
                    }
                    addresses.append(address)
        except Exception as e:
            sys.stderr.write(f"Error parsing TSV file {file_path}: {str(e)}\n")
            sys.exit(1)
        return addresses
   
    def clean_value(value):
        cleaned = value.strip() if value else ""
        return "" if cleaned in ("N/A", "N/M/N") else cleaned