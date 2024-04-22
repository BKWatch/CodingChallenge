"""
Author: Aryan Mehta <amehta64@asu.edu>
Date: 04/22/2024

Description:
    File Parser for BankruptcyWatch Challenge

    This script parses XML, TSV, and TXT file formats containing - 
    name, organization, street, city, state, county, and ZIP code information.

    The parsed data is combined into a sorted JSON-encoded list based on ZIP code, 
    handling common discrepancies in address formats.
    The script is designed for Python 3.11, adheres to PEP 8 standards, 
    and utilizes built-in libraries for maximum compatibility.

    Error handling is detailed within each parsing function, capturing and logging file-specific
    issues, ensuring that the user is informed of the nature of any processing interruptions.

Usage:
    python challenge.py <file_path1> <file_path2> ...
    To display help: python challenge.py --help
    Example: python challenge.py input1.xml input2.tsv input3.txt

Output Format:
    A JSON array of objects with fields: name, organization, street, city, county (optional), 
    state, and zip. The output is sorted in ascending order based on ZIP code.
"""

import argparse
import csv
import json
import sys
import xml.etree.ElementTree as ET
import re

def parse_xml(file_path):
    """
    Author: Aryan Mehta <amehta64@asu.edu>
    Date: 04/22/2024
    
    Parses an XML file to extract address data formatted as specified.

    The function expects the XML to follow a specific structure with the addresses wrapped
    inside <ENTITY><ENT> tags. Each <ENT> tag should contain child elements for name,
    organization, street address, city, state, and postal code.

    Args:
        file_path (str): The path to the XML file to be parsed.

    Returns:
        list of dict: A list of dictionaries, each dictionary representing an address
        containing the fields: name, organization, street, city, state, and zip.

    Example XML structure expected:
        <ENTITY>
            <ENT>
                <NAME>John Doe</NAME>
                <COMPANY>XYZ Corp</COMPANY>
                <STREET>Main St</STREET>
                <STREET_2>Suite 100</STREET_2>
                <STREET_3></STREET_3>
                <CITY>Metropolis</CITY>
                <STATE>NY</STATE>
                <POSTAL_CODE>12345-6789</POSTAL_CODE>
            </ENT>
            ...
        </ENTITY>

    Raises:
        Exception: If the XML file cannot be parsed, or if the file path is invalid,
                   an exception is raised with a message indicating the nature of the error.

    Note:
        If 'POSTAL_CODE' ends with a hyphen, it extracts only the first 5 digits.
        Street address is concatenated from potentially three fields: 
        STREET, STREET_2, and STREET_3.
    """
    directory = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for record in root.findall("./ENTITY/ENT"):
            address = {}
            name = record.find("NAME").text.strip()
            organization = record.find("COMPANY").text.strip()
            street = " ".join(
                [
                    record.find("STREET").text or "",
                    record.find("STREET_2").text or "",
                    record.find("STREET_3").text or "",
                ]
            ).strip()

            city = record.find("CITY").text.strip()
            state = record.find("STATE").text.strip()
            zip_code = record.find("POSTAL_CODE").text.strip()

            if name:
                address["name"] = name
            if organization:
                address["organization"] = organization
            if street:
                address["street"] = street
            if city:
                address["city"] = city
            if state:
                address["state"] = state
            if zip_code:
                if zip_code.endswith("-"):
                    address["zip"] = zip_code[:5]
                else:
                    address["zip"] = zip_code.replace(" ", "")

            directory.append(address)
    except Exception as e:
        sys.stderr.write(f"Error occurred while parsing XML file: {file_path}\n")
        sys.stderr.write(f"Error: {e}")
        sys.exit(1)

    return directory

def parse_tsv(file_path):
    """
    Author: Aryan Mehta <amehta64@asu.edu>
    Date: 04/22/2024
    
    Parses a TSV (Tab-Separated Values) file to extract address data.

    This function reads a TSV file where each row represents an address detail information.
    The function supports fields such as 'first', 'middle', 'last', 'organization', 'address',
    'city', 'county', 'state', and 'zip'. It also handles zip extensions.

    Args:
        file_path (str): The path to the TSV file to be parsed.

    Returns:
        list of dict: A list of dictionaries, each dictionary representing an address with the
        fields: name, organization, street, city, county (optional), state, and zip.

    Raises:
        Exception: If there is an error opening or reading the TSV file, or if the file format
                   does not match expectations, an exception is raised with a descriptive error 
                   message.

    Example TSV file format:
        first   middle  last    organization   address city    county  state   zip zip4
        John    Q.      Public  N/A            123 St  Gotham  Wayne   NY      12345 6789

    Note:
        - 'N/M/N' in the middle name column or 'N/A' in the organization field are treated as None.
        - Organization names are identified by keywords like 'llc', 'inc.', etc., in the last name 
        field.
    """
    directory = []
    company_keywords = ["llc", "inc.", "pvt.", "ltd."]
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            tsv_reader = csv.DictReader(file, delimiter="\t")
            for row in tsv_reader:
                address = {}
                if row["first"]:
                    first_name = row["first"].strip()
                else:
                    first_name = ""

                if (row["middle"] == "N/M/N" or not row["middle"]):
                    middle_name = ""
                else:
                    middle_name = row["middle"].strip()

                if row["last"]:
                    last_name = row["last"].strip()
                else:
                    last_name = ""

                if last_name:
                    if any(key in last_name.lower() for key in company_keywords):
                        address["organization"] = last_name
                        last_name = ""

                name = f"{first_name} {middle_name} {last_name}".strip()

                if name:
                    address["name"] = name

                if row["organization"] != "N/A" or not row["organization"]:
                    address["organization"] = row["organization"].strip()

                if row["address"]:
                    address["street"] = row["address"].strip()

                if row["city"]:
                    address["city"] = row["city"].strip()

                if row["county"]:
                    address["county"] = row["county"].strip()

                if row["state"]:
                    address["state"] = row["state"].strip()

                address["zip"] = row["zip"].strip()
                if row["zip4"]:
                    address["zip"] += f"-{row['zip4']}"

                directory.append(address)

    except Exception as e:
        sys.stderr.write(f"Error occurred while parsing TSV file: {file_path}\n")
        sys.stderr.write(f"Error: {e}")
        sys.exit(1)

    return directory

def parse_txt(file_path):
    """
    Author: Aryan Mehta <amehta64@asu.edu>
    Date: 04/22/2024

    Parses a plain text file to extract address data listed in a specific format.

    This function reads a plain text file where each address block includes a name or organization,
    followed by the street address, and then either directly the city and state with zip or an
    additional county line before the city, state, and zip. It uses a regular expression to parse
    the city, state, and zip code from a combined line. This function also identifies organizations
    based on specified keywords ('llc', 'inc.', 'pvt.', 'ltd.') in the name line.

    Args:
        file_path (str): The path to the text file to be parsed.

    Returns:
        list of dict: A list of dictionaries, each dictionary representing an address with
        the fields: name (optional), organization (optional), street, city, county (optional),
        state, and zip.

    Raises:
        Exception: If the text file cannot be opened, read, or properly parsed, an exception is 
                   raised with a detailed error message indicating the nature of the error.

    Example input format:
        John Doe
        5678 Oak St
        Smalltown County
        City, CA, 90210

    Note:
        - Addresses are parsed based on line breaks; each block is considered one complete address.
        - If a line directly after the street does not contain a comma, it is considered a county.
        - The regex pattern is used to split the city and state from the zip code.
    """
    directory = []
    company_keywords = ["llc", "inc.", "pvt.", "ltd."]
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip().split('\n')
        i = 0
        while i < len(content):
            address = {}
            county = ""

            if not content[i]:
                i += 1
                continue

            name_or_org = content[i].strip()
            if any(key in name_or_org.lower() for key in company_keywords):
                address["organization"] = name_or_org
            else:
                address["name"] = name_or_org

            address["street"] = content[i + 1].strip()

            if "," in content[i + 2]:
                city_state_split = content[i + 2].split(", ")
                i += 4
            else:
                county = content[i + 2].strip()
                city_state_split = content[i + 3].split(", ")
                i += 5

            address["city"] = city_state_split[0].strip()

            if county:
                address["county"] = county

            # Extract state and zip code
            # Explanation of regex pattern:
            # ([A-Za-z\s]+) - captures the state name
            # ,?\s* - optional comma and any number of spaces
            # (\d{5}(?:-\d{4})?) - captures the zip code
            pattern = r"([A-Za-z\s]+),?\s*(\d{5}(?:-\d{4})?)"
            match = re.search(pattern, city_state_split[1])
            if match:
                address["state"] = match.group(1).strip()
                zip_code = match.group(2).strip()
                if len(zip_code) == 6:
                    address["zip"] = zip_code[:5]
                else:
                    address["zip"] = zip_code

            directory.append(address)

    except Exception as e:
        sys.stderr.write(f"Error occurred while parsing TXT file: {file_path}\n")
        sys.stderr.write(f"Error: {e}")
        sys.exit(1)

    return directory

def main():
    """
    Author: Aryan Mehta <amehta64@asu.edu>
    Date: 04/22/2024

    Main execution function for the BankruptcyWatch file parsing challenge.

    This function uses argparse to process command line arguments where users specify file paths to
    XML, TSV, or TXT files containing address data. It parses these files based on their extension,
    aggregates all the address data into a list, sorts this list by ZIP code in ascending order,
    and then prints the sorted data in JSON format.

    The function supports error handling for unsupported file formats, missing files, and general
    errors during file parsing. It ensures that errors are reported clearly to the user.

    Returns:
        int: Exit code indicating the status of the program execution.
             Returns 0 on successful execution, 1 on any error or exception.

    Raises:
        FileNotFoundError: If any specified file is not found.
        Exception: General exceptions related to file parsing errors are caught and logged.

    Usage:
        To run the program, use the command:
        >> python challenge.py <file_path1> <file_path2> ...

        Example:
        >> python challenge.py input1.xml input2.tsv input3.txt

    Note:
        The function is designed to be called from the command line. It uses argparse to parse
        command line arguments, where each argument is expected to be a file path to an XML, TSV,
        or TXT file. The function identifies the type of each file by its extension and delegates
        the parsing to the corresponding parser function (parse_xml, parse_tsv, or parse_txt).
    """
    parser = argparse.ArgumentParser(description="BankruptcyWatch python file processor \
                                     that accepts a list of pathnames \
                                     of files in xml, tsv, or txt format and \
                                     outputs a JSON array of objects with address \
                                     information sorted by ZIP code in ascending \
                                     order.")
    parser.add_argument(
        "files",
        nargs="+",
        type=str,
        help="Pass files or file paths as arguments.\
            Example: >>python challenge.py input1.xml input2.tsv input3.txt",
    )
    args = parser.parse_args()

    output = []
    for file_path in args.files:
        try:
            if file_path.endswith(".xml"):
                output.extend(parse_xml(file_path))
            elif file_path.endswith(".tsv"):
                output.extend(parse_tsv(file_path))
            elif file_path.endswith(".txt"):
                output.extend(parse_txt(file_path))
            else:
                sys.stderr.write(f"Error: Unsupported file format: \"{file_path}\"\n")
                sys.stderr.write("Please use a valid file of type: .xml, .tsv, or .txt only\n")
                return 1
        except FileNotFoundError:
            sys.stderr.write(f"Error: File '{file_path}' not found.\n")
            return 1
        except Exception as e:
            sys.stderr.write(f"Error: Failed to parse file '{file_path}': {e}\n")
            return 1

    json_output = list(sorted(output, key=lambda x: x.get("zip")))

    print(json.dumps(json_output, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
