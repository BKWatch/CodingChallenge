"""
This script parses XML, TSV, and TXT files to extract name and address information, sorts the entries by ZIP code, and outputs them in JSON format.

Usage:
    python challenge.py input1.xml input2.tsv input3.txt

Author: Levi Moore
Original coding challenge URL: https://github.com/BKWatch/CodingChallenge
"""
import argparse
import sys
from typing import List, Dict, Tuple, Union
from xml.etree import ElementTree as ET


def normalize_zip(zip_code: str) -> str:
    """
    Normalize a ZIP code to the format '00000' or '00000-0000'.
    """
    return zip_code.replace(" ", "").rstrip("-")


def parse_address(address: str) -> Tuple[str, str, str]:
    """
    Returns the city, state, and ZIP code extracted from a US address string.
    If the format is invalid, returns a tuple of empty strings.
    """
    city_state_zip_match = re.match(r"(.+),([A-Za-z -]+)\s*([\d-]*)", address)
    if city_state_zip_match:
        return (
            city_state_zip_match.group(1),
            city_state_zip_match.group(2).strip(),
            normalize_zip(city_state_zip_match.group(3)),
        )
    return ("", "", "")


def parse_xml(file_path: str) -> List[Dict[str, Union[str, None]]]:
    """
    Parse an XML file and return a list of dictionaries representing the entries.
    """
    entries: List[Dict[str, Union[str, None]]] = []
    try:
        tree = ET.parse(file_path)
        for ent in tree.findall(".//ENT"):
            entry = {
                "name": "",
                "street": "",
                "city": "",
                "county": "",
                "state": "",
                "zip": "",
                "organization": "",
            }
            for element in ent:
                if element.text and element.text.strip():
                    text = element.text.strip()
                    tag = element.tag.lower()
                    if tag in ["name", "street", "city", "county", "state"]:
                        entry[tag] = text
                    elif tag == "company":
                        entry["organization"] = text
                    elif tag == "postal_code":
                        entry["zip"] = normalize_zip(text)
            entries.append(entry)
    except Exception as e:
        sys.stderr.write(f"Error occurred while parsing XML file '{file_path}': {e}\n")
        sys.exit(1)
    return entries


def parse_tsv(file_path: str) -> List[Dict[str, str]]:
    """
    Parse a TSV file and return a list of dictionaries representing the entries.
    """
    entries: List[Dict[str, str]] = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            headers = [header.lower() for header in lines[0].strip().split("\t")]
            for line in lines[1:]:
                values = line.strip().split("\t")
                entry = {headers[i]: values[i] for i in range(len(values))}
                if not entry.get("first") and not entry.get("middle"):
                    if entry.get("organization", "N/A") != "N/A":
                        entry["name"] = entry["organization"]
                    elif entry.get("last"):
                        entry["name"] = entry["last"]
                else:
                    first_name = entry.get("first", "")
                    middle_name = entry.get("middle", "N/M/N")
                    last_name = entry.get("last", "")
                    if middle_name == "N/M/N":
                        entry["name"] = " ".join([first_name, last_name])
                    else:
                        entry["name"] = " ".join([first_name, middle_name, last_name])
                entry["street"] = entry.get("address", "")
                city, state, zip_code = parse_address(entry.get("city", ""))
                entry["city"] = city
                entry["state"] = state
                entry["zip"] = (
                    zip_code + ("-" + entry["zip4"]) if entry.get("zip4") else ""
                )
                entries.append(entry)
    except Exception as e:
        sys.stderr.write(f"Error occurred while parsing TSV file '{file_path}': {e}\n")
        sys.exit(1)
    return entries


def parse_txt(file_path: str) -> List[Dict[str, str]]:
    """
    Parse a TXT file and return a list of dictionaries representing the entries.
    """
    entries: List[Dict[str, str]] = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            current_entry: Dict[str, str] = {}
            for line in lines:
                line = line.strip()
                if line:
                    if "name" not in current_entry:
                        current_entry["name"] = line
                    elif "street" not in current_entry:
                        current_entry["street"] = line
                    elif "county" not in current_entry and "COUNTY" in line:
                        current_entry["county"] = line.split()[0]
                    elif "city" not in current_entry:
                        city, state, zip_code = parse_address(line)
                        current_entry["city"] = city
                        current_entry["state"] = state
                        current_entry["zip"] = zip_code
                else:
                    if current_entry:
                        entries.append(current_entry)
                        current_entry = {}
    except Exception as e:
        sys.stderr.write(f"Error occurred while parsing TXT file '{file_path}': {e}\n")
        sys.exit(1)
    return entries


def main(args: argparse.Namespace) -> None:
    all_entries: List[Dict[str, Union[str, None]]] = []
    for file_path in args.files:
        ext = file_path.split(".")[-1].lower()
        if ext == "xml":
            all_entries.extend(parse_xml(file_path))
        elif ext == "tsv":
            all_entries.extend(parse_tsv(file_path))
        elif ext == "txt":
            all_entries.extend(parse_txt(file_path))
        else:
            sys.stderr.write(f"Unsupported file format: {ext}\n")
            sys.exit(1)

    sorted_entries = sorted(all_entries, key=lambda x: x.get("zip", ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This script parses XML, TSV, and TXT files to extract name and address information, sorts the entries by ZIP code, and outputs them in JSON format."
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="One or more file paths to be parsed. Supports XML, TSV, and TXT formats.",
    )
    args = parser.parse_args()
    main(args)
