import argparse
import sys
import json
import xml.etree.ElementTree as ET
import csv
import re

class BankruptcyWatch:
    """
    A class designed to encapsulate the parsing logic for various file formats is available.
    It provides support for TSV, XML, and plain text formats.
    """

    @staticmethod
    def extract_address_info(address_data):
        """
        Extracts address information from the given data.
        Args:
            address_data (list): A list containing address information.
        Returns:
            dict: A dictionary containing parsed address information.
        Raises:
            ValueError: If the length of address_data is invalid.
        """
        if len(address_data) not in [3, 4]:
            raise ValueError(f"The length of address data is invalid: '{len(address_data)}'")

        name = re.sub(r"(,?\s?Jr\.?|,?\s?Sr\.?|,?\s?I|,?\s?II|,?\s?III)$", "", address_data[0], flags=re.I).strip()

        city_state_zip = address_data[3] if len(address_data) == 4 else address_data[2]
        city, state_zip = city_state_zip.split(", ")
        state, zip_code = state_zip.rsplit(" ", 1)
        zip_code = zip_code.rstrip("-")

        if len(address_data) == 3:
            return {"name": name, "street": address_data[1], "city": city, "state": state, "zip": zip_code}
        else:
            return {"name": name, "street": address_data[1], "city": city, "county": address_data[2], "state": state,
                    "zip": zip_code}

    @staticmethod
    def parse_csv(file_path: str):
        """
        Parses a CSV file and returns a list of addresses.
        Args:
            file_path (str): Path to the CSV file.
        Returns:
            list: List of dictionaries representing addresses.
        """
        addresses = []

        try:
            with open(file_path) as textFile:
                reader = csv.DictReader(textFile, delimiter='\t')
                for row in reader:
                    inputs = {}
                    # Add names
                    if row["middle"] != "":
                        inputs["name"] = " ".join([row["first"], row["middle"], row["last"]])
                    elif row["middle"] == "N/M/N":
                        inputs["name"] = " ".join([row["first"], row["last"]])
                    elif row["organization"] == "N/A":
                        inputs["organization"] = row["last"]

                    # Legal Company Name
                    if row["organization"] != "N/A":
                        inputs["organization"] = row["organization"]

                    # STREET CITY STATE AND Country
                    inputs["street"] = row["address"]  # rename
                    inputs["city"] = row["city"]
                    inputs["state"] = row["state"]
                    if row["county"] != "":
                        inputs["county"] = row["county"]

                    # zip merging
                    inputs["zip"] = row["zip"]
                    if row["zip4"]:
                        inputs["zip"] += "-" + row["zip4"]

                    addresses.append(inputs)

        except FileNotFoundError as e:
            raise Exception(f"File '{file_path}' not found.") from e
        except Exception as e:
            raise Exception(f"Error reading file: {e}") from e

        return addresses

    @staticmethod
    def parse_xml(file_path: str):
        """
        Parses an XML file and returns a list of addresses.
        Args:
            file_path (str): Path to the XML file.
        Returns:
            list: List of dictionaries representing addresses.
        """
        addresses = []

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            addresses = []
            for entity in root.findall('.//ENT'):
                inputs = {}
                for data in entity:
                    tag = data.tag.upper()
                    if tag in ['NAME', 'COMPANY', 'STREET', 'CITY', 'STATE', 'POSTAL_CODE']:
                        if tag == 'COMPANY':
                            if data.text.strip():
                                inputs['organization'] = data.text.strip()
                        elif tag == "POSTAL_CODE":
                            if data.text.strip(" -"):
                                inputs["zip"] = data.text.strip(" -")
                        elif data.text.strip():
                            inputs[tag.lower()] = data.text.strip()
                addresses.append(inputs)

        except ET.ParseError as e:
            raise Exception(f"Error parsing XML file '{file_path}'") from e
        except FileNotFoundError as e:
            raise Exception(f"File '{file_path}' not found.") from e
        except Exception as e:
            raise Exception(f"Error reading file: {e}") from e

        return addresses

    @staticmethod
    def parse_text(file_path: str):
        """
        Parses a text file and returns a list of addresses.
        Args:
            file_path (str): Path to the text file.
        Returns:
            list: List of dictionaries representing addresses.
        """
        addresses = []

        try:
            with open(file_path, "r") as file:
                address_data = []
                for line in file:
                    line = line.strip()
                    if line:
                        address_data.append(line)
                    elif address_data:
                        address_info = BankruptcyWatch.extract_address_info(address_data)
                        addresses.append(address_info)
                        address_data = []
                if address_data:
                    address_info = BankruptcyWatch.extract_address_info(address_data)
                    addresses.append(address_info)

        except FileNotFoundError as e:
            raise Exception(f"File '{file_path}' not found.") from e
        except Exception as e:
            raise Exception(f"Error reading file: {e}") from e

        return addresses


def parse_arguments():
    """
    Parses command line arguments.
    Returns:
        Namespace: An object with file paths provided by the user.
    """
    parser = argparse.ArgumentParser(description="Get addresses from input files, combine them and output as JSON")
    # required args
    parser.add_argument("files", metavar='-f', type=str, nargs="+",
                        help="A list of input files in TSV, XML, or plain text format")
    return parser.parse_args()


def main():
    """
    Processes a list of files and extracts address information from them.
    The function accepts a list of file paths as command line arguments. It supports files in XML, TSV, and TXT formats.
    For each file, it reads the file, parses the addresses, and adds them to a list. If a file is not in a supported format,
    or if an error occurs during processing, the function prints an error message and exits with a status of 1.
    After all files have been processed, the function sorts the addresses by ZIP code and prints them to the console in JSON format.
    """
    args = parse_arguments()
    addresses = []

    for file_path in args.files:
        try:
            if file_path.lower().endswith(".xml"):
                addresses.extend(BankruptcyWatch.parse_xml(file_path))
            elif file_path.lower().endswith(".tsv"):
                addresses.extend(BankruptcyWatch.parse_csv(file_path))
            elif file_path.lower().endswith(".txt"):
                addresses.extend(BankruptcyWatch.parse_text(file_path))
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


if __name__ == "__main__":
    main()
