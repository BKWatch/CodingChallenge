#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""\
This script accepts a list of pathnames of files (*.xml, *.tsv, *.txt), parses them,
and writes a JSON-encoded list of the combined addresses to standard output, sorted by
ZIP code.

usage: challenge.py [-h] file [file ...]

A few assumptions about the data and instructions were made by this script. These have
been noted with comments marked '# ASSUMPTION:'.
"""

# ASSUMPTION: The instructions in README.txt list 'organization' as one of the output
# JSON keys. In the sample output, however, 'company' is used instead. This code assumes
# 'organization' to be the correct key.


__author__ = "Jake Larkin"
__email__ = "jkub66@gmail.com"
__status__ = "Prototype"
__version__ = "0.1"


import argparse
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET


RE_NAME = re.compile(r"^$|^.*$")
RE_ORGANIZATION = re.compile(r"^$|^.*$")
RE_STREET = re.compile(r"^.*(\n.+){0,2}$")
RE_CITY = re.compile(r"^.*$")
RE_COUNTY = re.compile(r"^$|^.*$")
RE_STATE = re.compile(r"^[A-Za-z. ]*$")
RE_ZIP = re.compile(r"^\d{5}(-\d{4})?$")

RE_CITY_STATE_ZIP = re.compile(r"^.*, [A-Za-z. ]* \d{5}(-\d{4})?-?$")

STATE_CODES = {
    "ALABAMA": "AL",
    "ALASKA": "AK",
    "AMERICAN SAMOA": "AS",
    "ARIZONA": "AZ",
    "ARKANSAS": "AR",
    "CALIFORNIA": "CA",
    "COLORADO": "CO",
    "CONNECTICUT": "CT",
    "DELAWARE": "DE",
    "DISTRICT OF COLUMBIA": "DC",
    "FLORIDA": "FL",
    "GEORGIA": "GA",
    "GUAM": "GU",
    "HAWAII": "HI",
    "IDAHO": "ID",
    "ILLINOIS": "IL",
    "INDIANA": "IN",
    "IOWA": "IA",
    "KANSAS": "KS",
    "KENTUCKY": "KY",
    "LOUISIANA": "LA",
    "MAINE": "ME",
    "MARYLAND": "MD",
    "MASSACHUSETTS": "MA",
    "MICHIGAN": "MI",
    "MINNESOTA": "MN",
    "MISSISSIPPI": "MS",
    "MISSOURI": "MO",
    "MONTANA": "MT",
    "NEBRASKA": "NE",
    "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH",
    "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM",
    "NEW YORK": "NY",
    "NORTH CAROLINA": "NC",
    "NORTH DAKOTA": "ND",
    "NORTHERN MARIANA ISLANDS": "MP",
    "OHIO": "OH",
    "OKLAHOMA": "OK",
    "OREGON": "OR",
    "PENNSYLVANIA": "PA",
    "PUERTO RICO": "PR",
    "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD",
    "TENNESSEE": "TN",
    "TEXAS": "TX",
    "UNITED STATES MINOR OUTLYING ISLANDS": "UM",
    "U.S. VIRGIN ISLANDS": "VI",
    "UTAH": "UT",
    "VERMONT": "VT",
    "VIRGINIA": "VA",
    "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV",
    "WISCONSIN": "WI",
    "WYOMING": "WY",
}


def normalize_name(name):
    """Normalize and validate name values."""
    name = name.strip()

    if not RE_ORGANIZATION.match(name):
        sys.exit(f"Error: '{name}' is not a valid name.")
    return name


def normalize_organization(organization):
    """Normalize and validate organization values."""
    organization = organization.strip()

    if organization == "N/A":
        organization = ""

    if not RE_ORGANIZATION.match(organization):
        sys.exit(f"Error: '{organization}' is not a valid organization.")
    return organization


def normalize_street(street):
    """Normalize and validate street values."""
    street = street.strip()
    if not RE_STREET.match(street):
        sys.exit(f"Error: '{street}' is not a valid street.")
    return street


def normalize_city(city):
    """Normalize and validate city values."""
    city = city.strip()
    if not RE_CITY.match(city):
        sys.exit(f"Error: '{city}' is not a valid city.")
    return city


def normalize_county(county):
    """Normalize and validate county values."""
    county = county.strip()

    if not RE_COUNTY.match(county):
        sys.exit(f"Error: '{county}' is not a valid county.")
    return county


def normalize_state(state):
    """Normalize and validate state values."""
    state = state.strip().upper()

    if state in STATE_CODES:
        return STATE_CODES[state]
    elif state in STATE_CODES.values():
        return state
    else:
        sys.exit(f"Error: '{state}' is not a valid state.")


def normalize_zip(zip):
    """Normalize and validate ZIP code values."""
    zip = zip.strip().rstrip("- ")
    zip = zip.replace(" - ", "-")

    if not RE_ZIP.match(zip):
        sys.exit(f"Error: '{zip}' is not a valid ZIP code.")
    return zip


def parse_CSZ(city_state_zip):
    """Parse data from City-State-ZIP format into separate vars (city, state, zip)."""
    city_state_zip = city_state_zip.strip()

    if not RE_CITY_STATE_ZIP.match(city_state_zip):
        sys.exit(f"Error: '{city_state_zip}' is not a valid city-state-zip.")

    city, state_zip = city_state_zip.split(", ")
    state = " ".join(state_zip.split(" ")[:-1])
    zip = state_zip.split(" ")[-1]

    city = normalize_city(city)
    state = normalize_state(state)
    zip = normalize_zip(zip)

    return (city, state, zip)


def parse_txt_section(section):
    """Parse a single section (single entry) from the txt file format. A section is
    designated by surrounding newlines."""
    if len(section) == 0:
        return {}

    # ASSUPTION: The main difficulty here is determining the presence/absence of both
    # organization and county. This code will be assuming that the county string will
    # always end with ' county' or ' COUNTY' (for example 'DUVAL COUNTY'). Without this
    # assumption, (or similar assumptions) there does not appear to be any way to
    # distinguish the two.
    organization_present = False
    county_present = False

    if len(section) == 3:
        organization_present = False
        county_present = False
    elif len(section) == 4 and section[2].upper().endswith(" COUNTY"):
        organization_present = False
        county_present = True
    elif len(section) == 4:
        organization_present = True
        county_present = False
    elif len(section) == 4 and section[3].upper().endswith(" COUNTY"):
        organization_present = True
        county_present = True
    else:
        sys.exit(f"Error: Invalid .txt format section:\n{section}")

    entry = {}
    entry["name"] = normalize_name(section[0])

    if organization_present:
        entry["organization"] = normalize_organization(section[1])
        entry["street"] = normalize_street(section[2])

        if county_present:
            entry["county"] = normalize_county(section[3])
            entry["city"], entry["state"], entry["zip"] = parse_CSZ(section[4])
        else:
            entry["county"] = section[2]
            entry["city"], entry["state"], entry["zip"] = parse_CSZ(section[3])
    else:
        entry["street"] = normalize_street(section[1])

        if county_present:
            entry["county"] = normalize_county(section[2])
            entry["city"], entry["state"], entry["zip"] = parse_CSZ(section[3])
        else:
            entry["city"], entry["state"], entry["zip"] = parse_CSZ(section[2])

    return entry


def load_txt(file):
    """Parse a file in .txt format into a list of Python dict entries."""
    entries = []
    section = []

    for line in file.readlines():
        line = line.rstrip("\r\n")

        if line == "":
            parsed_section = parse_txt_section(section)
            section = []
            if len(parsed_section) >= 1:
                entries.append(parsed_section)
        else:
            section.append(line)

    return entries


def load_tsv(file):
    """Parse a file in .tsv format into a list of Python dict entries."""
    entries = []

    tsv_file = csv.reader(file, delimiter="\t")

    first_line = True

    for line in tsv_file:
        if len(line) != 10:
            sys.exit(
                f"Error: '{len(line)}' is an invalid number of cols (should be 10)"
            )

        if first_line:
            first_line = False
            continue

        entry = {}

        first, middle, last = line[0], line[1], line[2]
        if middle == "N/M/N":
            middle = ""
        name = ""
        if first != "":
            name += first + " "
        if middle != "":
            name += middle + " "
        if last != "":
            name += last + " "
        name = name.strip()

        entry["name"] = normalize_name(name)
        entry["organization"] = normalize_organization(line[3])
        entry["street"] = normalize_street(line[4])
        entry["city"] = normalize_city(line[5])
        entry["county"] = normalize_county(line[7])
        entry["state"] = normalize_state(line[6])
        entry["zip"] = normalize_zip(line[8] + "-" + line[9])

        # ASSUMPTION: It appears that the organization name is often entered into the
        # last name field. This code will assume the .tsv data is broken here, and will
        # attempt to fix it by reading the last name as the organization if first name,
        # middle name, and organization are all blank.
        if first == "" and middle == "" and entry["organization"] == "":
            entry["name"] = ""
            entry["organization"] = last

        entries.append(entry)

    return entries


def load_xml(file):
    """Parse a file in .xml format into a list of Python dict entries."""
    tree = ET.parse(file)
    root = tree.getroot()
    entity = root.find("ENTITY")

    if entity is None:
        sys.exit(f"Error: '{file.name}' does not contain an ENTITY tag.")

    entries = []

    for ent in entity.findall("ENT"):
        entry = {}

        name = ent.find("NAME")
        organization = ent.find("COMPANY")

        street1 = ent.find("STREET")
        street2 = ent.find("STREET_2")
        street3 = ent.find("STREET_3")

        city = ent.find("CITY")
        state = ent.find("STATE")
        zip = ent.find("POSTAL_CODE")

        if None in [name, organization, street1, street2, street3, city, state, zip]:
            sys.exit(f"Error: '{file.name}' does not contain the proper value tags.")

        street = "\n".join(
            [street1.text.strip(), street2.text.strip(), street3.text.strip()]
        )

        entry["organization"] = normalize_organization(organization.text)
        entry["street"] = normalize_street(street)
        entry["city"] = normalize_city(city.text)
        entry["state"] = normalize_state(state.text)
        entry["county"] = ""
        entry["zip"] = normalize_zip(zip.text)

        entries.append(entry)

    return entries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This script accepts a list of pathnames of files (*.xml, *.tsv, \
                    *.txt), parses them, and write JSON-encoded list of the combined \
                    addresses to standard output, sorted by ZIP code."
    )
    parser.add_argument(
        "file",
        type=argparse.FileType("r"),
        nargs="+",
        help="a file to load (*.xml, *.tsv, *.txt)",
    )
    args = parser.parse_args()

    entries = []

    for file in args.file:
        if file.name.endswith(".xml"):
            entries += load_xml(file)
        elif file.name.endswith(".tsv"):
            entries += load_tsv(file)
        elif file.name.endswith(".txt"):
            entries += load_txt(file)
        else:
            sys.exit(f"Error: '{file.name}' is not a supported file type.")

    # Remove blank name, organization, and county entries
    for entry in entries:
        if entry.get("name", "-") == "":
            del entry["name"]
        if entry.get("organization", "-") == "":
            del entry["organization"]
        if entry.get("county", "-") == "":
            del entry["county"]

    # Sort entries by ZIP code
    entries.sort(key=lambda x: x["zip"])

    # Pretty-print JSON entries
    print(json.dumps(entries, indent=2))
