#!/bin/python

from typing import Dict, List

import argparse

import csv
import io
import json
import re
import sys
import os
import xml.etree.ElementTree as ET


def parse_xml(contents: str) -> List[Dict[str, str]]:
    root = ET.fromstring(contents)
    # Create an empty list to store the data
    data = []

    # Iterate over each ENT element
    for ent in root.findall('ENTITY/ENT'):
        # Create a dictionary to store the entity data
        entity_data = {}
        for child in ent:
            entity_data[child.tag] = child.text.strip()

        # Append the dictionary to the data list
        data.append(entity_data)

    return data


def parse_tsv(contents: str) -> List[Dict[str, str]]:
    reader = csv.reader(io.StringIO(contents), delimiter='\t')
    # Skip the header row (if it exists)
    next(reader, None)
    data = []
    for row in reader:
        # Check if the row is empty (represents an organization entry)
        if not row[0]:
            organization = row[3].strip()

        # Create a dictionary to store the person data
        person_data = {
            'name': " ".join(row[:3]),
            'organization': organization,
            'address': row[4].strip(),
            'city': row[5].strip(),
            'state': row[6].strip(),
            'county': row[7].strip(),
            'zip': "-".join([row[8], row[9]])
        }

        # Append the dictionary to the data list
        data.append(person_data)

    return data


def parse_txt_entry(entry_data):
    name = entry_data[0].strip()
    address = entry_data[1].strip()
    # Handle county names with multiple lines
    if len(entry_data) > 3 and entry_data[2].upper().endswith("COUNTY"):
        city_state_zip = " ".join(entry_data[3:]).strip()
    else:
        city_state_zip = " ".join(entry_data[2:]).strip()

    # Split city, state, and zip code (assuming US format)
    city, state_zip_code = city_state_zip.rsplit(",", 1)

    state = re.findall(r"([^\d]+)\d", state_zip_code)[0].strip()
    zip_code = re.findall(r"\d.+", state_zip_code)[0].strip()
    # Remove extra hyphen in zip code (if present)

    return {
        "name": name,
        "address": address,
        "city": city.rstrip(", " + state),
        "state": state,
        "zip": zip_code,
    }


def parse_txt(contents: str) -> List[Dict[str, str]]:

    entries = []
    current_entry = []
    for line in contents.splitlines():
        line = line.strip()
        if not line:
            if current_entry:
                entries.append(parse_txt_entry(current_entry))
                current_entry = []
        else:
            current_entry.append(line)

    # Add the last entry (if any)
    if current_entry:
        entries.append(parse_txt_entry(current_entry))
    return entries


def normalize_data(entry: Dict[str, str]) -> Dict[str, str]:

    entry = {k.lower(): v for k, v in entry.items()}

    # Output columns and their possible alternative aliases;
    column_alias_map = {
        "name": ["first"],
        "organization": ["company"],
        "street": ["address"],
        "city": [],
        "county": [],
        "state": [],
        "zip": ["postal_code"],
    }

    final_entry = {}
    for target_column, alt_source_columns in column_alias_map.items():
        if target_column in entry:
            final_entry[target_column] = entry[target_column]
        else:
            for source_column in alt_source_columns:
                try:
                    final_entry[target_column] = entry[source_column]
                except KeyError:
                    pass

    final_entry["zip"] = final_entry["zip"].strip(" -").replace(" ", "")

    # Remove empty entries;
    final_entry = {
        k: v
        for k, v in final_entry.items()
        if v.strip() not in ["", "N/A"]
    }

    return final_entry


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="This script helps to parse lists "
        "containing information about multiple people "
        "in different formats. Extremely useful in stalking workflows."
    )

    parser.add_argument(
        'input',
        help="One or multiple input filepaths, "
        "given as separate arguments. "
        "The input files can be in .txt, .tsv, or .xml format. "
        "For input examples, refer to the './input' directory.",
        nargs='*'
    )

    return parser.parse_args()


def main():

    arguments = parse_arguments()

    all_data = []
    for input_file in arguments.input:

        match os.path.splitext(input_file)[-1]:
            case ".tsv":
                parser = parse_tsv
            case ".txt":
                parser = parse_txt
            case ".xml":
                parser = parse_xml
            case _:
                print(f"Unsupported file format for {input_file}.")
                sys.exit(1)

        with open(input_file, encoding="utf-8") as f:
            contents = f.read()
            all_data += parser(contents)

    # Try to fix the data;
    all_data = [normalize_data(entry) for entry in all_data]

    # Display the findal data;
    all_data = sorted(all_data, key=lambda k: k["zip"])
    print(json.dumps(all_data, indent=4))


if __name__ == '__main__':
    main()
