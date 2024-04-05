import csv
import sys
import json
import os

def parse_tsv(file_path):
    """
    Parse TSV file and extract address information.

    Args:
        file_path (str): Path to the TSV file.

    Returns:
        list: List of dictionaries containing address information.
    """

    try:
        addresses = []

        with open(file_path, 'r', encoding='utf-8', newline='') as tsvfile:
            reader = csv.DictReader(tsvfile, delimiter='\t')
            
            for row in reader:
                # Extracting first name, middle name, last name, organization, county, and determining their presence
                first_name = row['first'].strip() if row['first'] else ""
                middle_name = row['middle'].strip() if row['middle'] else ""
                if middle_name == "N/M/N":
                    middle_name = ""
                last_name = row['last'].strip() if row['last'] else ""
                organization = row['organization'].strip() if row['organization'] else ""
                county = row['county'].strip() if row['county'] else ""
                county_name_present = bool(county)
                name_present = any([first_name, middle_name, last_name])
                organization_present = bool(organization)

                # Determining address name based on presence of personal name or organization name
                if name_present:
                    address_name = f"{first_name} {middle_name} {last_name}".strip()
                    variable_name = "name"
                elif organization_present:
                    address_name = organization
                    variable_name = "company"
                else:
                    print(f"No personal name or organization found in {file_path}. Skipping this entry.", file=sys.stderr)
                    continue

                # Creating address dictionary
                        
                # Adding county if present
                if county_name_present:
                    address = {
                        variable_name: address_name,
                        "street": row['address'].strip(),
                        "city": row['city'].strip(),
                        "county": county,
                        "state": row['state'].strip(),
                        "zip": f"{row['zip']}-{row['zip4']}" if row['zip4'] else row['zip']
                    }
                else:
                    address = {
                        variable_name: address_name,
                        "street": row['address'].strip(),
                        "city": row['city'].strip(),
                        "state": row['state'].strip(),
                        "zip": f"{row['zip']}-{row['zip4']}" if row['zip4'] else row['zip']
                    }

                addresses.append(address)

        # Sorting addresses based on zip code
        sorted_data = sorted(addresses, key=lambda item: item['zip'].rstrip('-'))
        
        # Convert addresses to JSON string
        json_data = json.dumps(sorted_data, indent=2)
        return json_data
    
    except Exception as e:
        print(f"Error parsing TSV file: {file_path}. {e}", file=sys.stderr)
        sys.exit(1)