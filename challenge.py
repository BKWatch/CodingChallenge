"""
Address Parser for BankruptcyWatch Challenge

This script parses US names and addresses from files in XML, TSV, and TXT formats,
combining the data into a sorted JSON-encoded list based on ZIP code. 

The script adheres to Python 3.11 standards, is PEP 8 compliant, and uses only
standard Python libraries. Error handling is robust, with clear messages for
user guidance and input validation.

Usage:
    python challenge.py <file_path1> <file_path2> ...

Output Format:
    JSON array of objects with fields: name, organization, street, city, county (optional),
    state, and zip, adhering to the specified property order.

Example:
    python challenge.py input1.xml input2.tsv input3.txt

Author: Vishva Desai
Date: 04/09/2024
"""

import argparse
import csv
import json
import sys
import xml.etree.ElementTree as ET
import re


def parse_txt(file_path):
    """Parse a text file containing address information.

    Args:
        file_path (str): The path to the text file to be parsed.

    Returns:
        list of dict: A list of dictionaries, each representing an address.
    """
    directory = []
    with open(file_path, "r") as file:
        content = file.read()
        content = content.lstrip().splitlines()

    i = 0
    increment = 4
    while i < len(content):
        address = {}
        county = ""
        if i + 4 > len(content):
            break
        if not content[i]:
            i += 1
            continue

        address["name"] = content[i].strip()
        address["street"] = content[i + 1].strip()
        if "," in content[i + 2]:
            city_state_split = content[i + 2].rsplit(", ", 1)
            i += 4
        else:
            county = content[i + 2].strip()
            city_state_split = content[i + 3].rsplit(", ", 1)
            i += 5

        address["city"] = city_state_split[0].strip()
        if county:
            address["county"] = county

        pattern = r"([A-Za-z\s]+),?\s*(\d{5}(?:-\d{4})?)"
        match = re.search(pattern, city_state_split[1])
        address["state"] = match.group(1).strip()
        zip = match.group(2).strip()
        address["zip"] = zip[:5] if len(zip) == 6 else zip

        directory.append(address)
        county = ""
    return directory


def parse_tsv(file_path):
    """Parse a TSV file containing address information.

    Args:
        file_path (str): The path to the TSV file to be parsed.

    Returns:
        list of dict: A list of dictionaries, each representing an address.
    """
    directory = []
    company_filters = ["llc", "inc.", "ltd."]
    with open(file_path, "r") as file:
        reader = csv.DictReader(file, delimiter="\t")
        for row in reader:
            address = {}
            first_name = row["first"] if row["first"] else ""
            middle_name = (
                "" if (row["middle"] == "N/M/N" or not row["middle"]) else row["middle"]
            )
            last_name = row["last"] if row["last"] else ""

            if any(filter_item in last_name.lower() for filter_item in company_filters):
                address["organization"] = last_name
                last_name = ""

            name = f"{first_name} {middle_name} {last_name}".strip()
            if name:
                address["name"] = name
            if row["organization"] != "N/A" or not row["organization"]:
                address["organization"] = row["organization"]
            if row["address"]:
                address["street"] = row["address"]
            if row["city"]:
                address["city"] = row["city"]
            if row["county"]:
                address["county"] = row["county"]
            if row["state"]:
                address["state"] = row["state"]

            address["zip"] = row["zip"]
            if row["zip4"]:
                address["zip"] += f"-{row['zip4']}"
            directory.append(address)
    return directory


def parse_xml(file_path):
    """Parse an XML file containing address information.

    Args:
        file_path (str): The path to the XML file to be parsed.

    Returns:
        list of dict: A list of dictionaries, each representing an address.
    """
    directory = []
    tree = ET.parse(file_path)
    root = tree.getroot()
    for entity in root.findall("./ENTITY/ENT"):
        address = {}
        name = entity.find("NAME").text.strip()
        organization = entity.find("COMPANY").text.strip()
        street = " ".join(
            [
                entity.find("STREET").text or "",
                entity.find("STREET_2").text or "",
                entity.find("STREET_3").text or "",
            ]
        ).strip()
        city = entity.find("CITY").text.strip()
        state = entity.find("STATE").text.strip()
        zip = entity.find("POSTAL_CODE").text.strip()

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
        if zip:
            address["zip"] = zip[:5] if zip.endswith("-") else zip.replace(" ", "")

        directory.append(address)

    return directory


def main():
    """Main function to parse address files and output JSON."""

    parser = argparse.ArgumentParser(description="Parse input files and output JSON.")
    parser.add_argument(
        "files",
        nargs="+",
        help=" Pass path to address files <file_path1> <file_path2> <file_path3> ...",
    )
    args = parser.parse_args()

    directory = []
    for file_path in args.files:
        try:
            if file_path.endswith(".tsv"):
                directory.extend(parse_tsv(file_path))
            elif file_path.endswith(".xml"):
                directory.extend(parse_xml(file_path))
            elif file_path.endswith(".txt"):
                directory.extend(parse_txt(file_path))
            else:
                print(
                    f"Error: File format unsupported for '{file_path}'", file=sys.stderr
                )
                return 0
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.", file=sys.stderr)
            return 0
        except Exception as e:
            print(f"Error: Failed to parse file '{file_path}': {e}", file=sys.stderr)
            return 0

    sorted_directory = sorted(directory, key=lambda a: a.get("zip"))
    json_output = [record for record in sorted_directory]

    print(json.dumps(json_output, indent=2))
    return 1


if __name__ == "__main__":
    sys.exit(main())
