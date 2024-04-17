import argparse
import sys
import json
import xml.etree.ElementTree as ET
import csv
import re

def parse_address(address_info):
    """
    Parses address information into a dictionary.

    Args:
        address_info (list): A list of strings representing an address. The list should have either 3 or 4 elements:
            - name (str): The name of the person.
            - street (str): The street address.
            - county (str, optional): The county. Only included if the list has 4 elements.
            - city_state_zip (str): The city, state, and zip code, in the format "City, State Zip".

    Returns:
        dict: A dictionary representing the address, with the following keys:
            - "name": The name of the person.
            - "street": The street address.
            - "county": The county, or None if not provided.
            - "city": The city.
            - "state": The state.
            - "zip": The zip code.

    Raises:
        ValueError: If the length of address_info is not 3 or 4.
    """
    if len(address_info) not in [3, 4]:
        raise ValueError(f"Invalid length: '{len(address_info)}'")

    # Get name
    name = re.sub(r"(,?\s?Jr\.?|,?\s?Sr\.?|,?\s?I|,?\s?II|,?\s?III)$", "", address_info[0], flags=re.I).strip()

    # Get city, state, and zip
    city_state_zip = address_info[3] if len(address_info) == 4 else address_info[2]
    city, state_zip = city_state_zip.split(", ")
    state, zip_code = state_zip.rsplit(" ", 1)
    zip_code = zip_code.rstrip("-")

    if len(address_info) == 3:
        return {"name": name, "street": address_info[1], "city": city, "state": state, "zip": zip_code}
    else:
        return {"name": name, "street": address_info[1], "city": city, "county": address_info[2], "state": state, "zip": zip_code}


def parse_txt(file_path):
    """
    Reads a text file and returns a list of addresses.

    Args:
        file_path (str): Path to the text file.

    Returns:
        list: List of dictionaries representing addresses.
    """
    addresses = []  # Initialize an empty list for addresses

    try:
        with open(file_path, "r") as file:
            address_info = []
            for line in file:
                line = line.strip()  # Remove leading/trailing white spaces
                if line:  # If line is not empty
                    address_info.append(line)
                elif len(address_info) > 0:  # If line is empty, it means we have reached the end of an address
                    address_dict = parse_address(address_info)
                    addresses.append(address_dict)
                    address_info = []  # Reset the list for the next address
            if address_info:  # Add the last address if the file doesn't end with an empty line
                address_dict = parse_address(address_info)
                addresses.append(address_dict)
    except FileNotFoundError:
        raise Exception(f"File '{file_path}' not found.")
    except Exception as e:
        raise Exception(f"Error reading file: {e}")

    return addresses


def parse_tsv(file_path):
    """
    Parses a TSV file and returns a list of addresses.

    Args:
        file_path (str): Path to the TSV file.

    Returns:
        list: List of dictionaries representing addresses.
    """
    addresses = []  # Initialize an empty list for addresses

    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file, delimiter='\t')
            reader.fieldnames = [name.strip() for name in reader.fieldnames]  # Strip white spaces from field names
            for row in reader:
                # Remove trailing hyphens from the zip code and combine zip and zip4
                zip_code = row['zip'].rstrip('-')
                if row['zip4'].strip() != "":
                    zip_code += "-" + row['zip4']
                # Replace empty names with None and exclude 'N/M/N' middle names
                first_name = row['first'].strip() if row['first'] and row['first'].strip() != "" else ""
                middle_name = row['middle'].strip() if row['middle'] and row['middle'].strip() not in ["", "N/M/N"] else ""
                last_name = row['last'].strip() if row['last'] and row['last'].strip() != "" else ""
                name_parts = [part for part in [first_name, middle_name, last_name] if part]
                name = " ".join(name_parts)
                # Replace 'N/A' organizations with None
                organization = row['organization'].strip() if row['organization'] and row['organization'].strip() != "N/A" else None
                # Create a dictionary for the address
                address_dict = {}

                if name:
                    address_dict["name"] = name
                if organization:
                    address_dict["organization"] = organization
                address_dict["street"] = row['address']
                address_dict["city"] = row['city']
                address_dict["state"] = row['state']
                if row['county'].strip() != "":
                    address_dict["county"] = row['county']
                address_dict["zip"] = zip_code

                addresses.append(address_dict)

    except FileNotFoundError:
        raise Exception(f"File '{file_path}' not found.")
    except Exception as e:
        raise Exception(f"Error reading file: {e}")

    return addresses


def parse_xml(file_path):
    """
    Parses an XML file and returns a list of addresses.

    Args:
        file_path (str): Path to the XML file.

    Returns:
        list: List of dictionaries representing addresses.
    """
    addresses = []  # Initialize an empty list for addresses

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        for ent in root.iter('ENT'):
            # Get name/company
            name = ent.find('NAME').text if ent.find('NAME') is not None and ent.find('NAME').text.strip() != "" else None
            if name is not None:
                name = re.sub(r"(,?\s?Jr\.?|,?\s?Sr\.?|,?\s?I|,?\s?II|,?\s?III)$", "", name, flags=re.I).strip()
            # If the company name includes "d/b/a", set company to everything after "d/b/a"
            company = ent.find('COMPANY').text if ent.find('COMPANY') is not None and ent.find('COMPANY').text.strip() != "" else None
            if company is not None and "d/b/a" in company.lower():
                company = company.lower().split("d/b/a")[1].strip()

            # Get street
            street = ent.find('STREET').text if ent.find('STREET') is not None else ""
            street2 = ent.find('STREET_2').text if ent.find('STREET_2') is not None and ent.find('STREET_2').text.strip() != "" else ""
            street3 = ent.find('STREET_3').text if ent.find('STREET_3') is not None and ent.find('STREET_3').text.strip() != "" else ""
            street_values = [street, street2, street3]
            street_values = [value for value in street_values if value.strip() != ""]
            street = ", ".join(street_values)

            # Get city, state, and zip
            city = ent.find('CITY').text if ent.find('CITY') is not None else None
            state = ent.find('STATE').text if ent.find('STATE') is not None else None
            zip_code = ent.find('POSTAL_CODE').text.replace(" ", "").rstrip("-") if ent.find('POSTAL_CODE') is not None else None

            # Append to addresses
            if name is None:
                address_dict = {"organization": company, "street": street, "city": city, "state": state, "zip": zip_code}
            else:
                address_dict = {"name": name, "street": street, "city": city, "state": state, "zip": zip_code}
            addresses.append(address_dict)

    except ET.ParseError:
        raise Exception(f"Error parsing XML file '{file_path}'")
    except FileNotFoundError:
        raise Exception(f"File '{file_path}' not found.")
    except Exception as e:
        raise Exception(f"Error reading file: {e}")

    return addresses

    
def parse_args():
    parser = argparse.ArgumentParser(description="Combine addresses from input files and output as JSON")
    parser.add_argument("files", nargs="+", help="List of input file paths")
    return parser.parse_args()


def main():
    """
    Processes a list of files and extracts address information from them.

    The function accepts a list of file paths as command line arguments. It supports files in XML, TSV, and TXT formats.
    For each file, it reads the file, parses the addresses, and adds them to a list. If a file is not in a supported format,
    or if an error occurs during processing, the function prints an error message and exits with a status of 1.

    After all files have been processed, the function sorts the addresses by ZIP code and prints them to the console in JSON format.

    Usage:
        python challenge.py input/file1.xml input/file2.tsv input/file3.txt

    Raises:
        SystemExit: If a file is not in a supported format, or if an error occurs during processing.
    """
    parser = argparse.ArgumentParser(description='Process some files.')
    parser.add_argument('files', metavar='F', type=str, nargs='+',
                        help='A list of files to process in .xml, .tsv, or .txt format')
    args = parser.parse_args()

    addresses = []

    for file_path in args.files:
        try:
            if file_path.lower().endswith(".xml"):
                addresses.extend(parse_xml(file_path))
            elif file_path.lower().endswith(".tsv"):
                addresses.extend(parse_tsv(file_path))
            elif file_path.lower().endswith(".txt"):
                addresses.extend(parse_txt(file_path))
            else:
                print(f"Error: Unsupported file format: {file_path}", file=sys.stderr)
                sys.exit(1)

        except Exception as e:
            print(f"Error processing file '{file_path}': {e}", file=sys.stderr)
            sys.exit(1)

    # Sort by ZIP code
    sorted_addresses = sorted(addresses, key=lambda addr: addr.get("zip", ""))

    # Output as JSON
    print(json.dumps(sorted_addresses, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()