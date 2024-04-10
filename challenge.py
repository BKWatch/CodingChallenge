# Author:   Syed Abbas Shah
# Email:    s.4bbas@gmail.com
# Notes:    The required tasks were completed. Future improvements include:
#           - Consistent capitalization (i.e. CLAYTON COUNTY -> Clayton)
#           - Consistent states (i.e. IL and Illinois are both valid as of right now).
#           - Having an agreed upon list of valid organization identifier (e.g. LLC, Inc., etc.)

from argparse import ArgumentParser
import xml.etree.ElementTree as ET
from pathlib import Path
import json
import csv
import sys


def main():
    arguments = get_arguments()

    # Stores list of entities
    info_list = []

    for file_path in arguments.files:
        extension = Path(file_path).suffix

        match extension:
            case ".xml":
                info_list += parse_xml(file_path)
            case ".tsv":
                info_list += parse_tsv(file_path)
            case ".txt":
                info_list += parse_txt(file_path)
            case _:
                print("ERROR: invalid file extension: " +
                      extension, file=sys.stderr)
                sys.exit(1)

    sorted_list = sorted(info_list, key=lambda x: x["zip"][:10])
    print(json.dumps(sorted_list, indent=2))

    return 0


# Sets up --help and --files for commandline.
def get_arguments():
    parser = ArgumentParser(
        description="Combines information about individuals/organizations into a singular JSON string (sorted by ZIP)")
    parser.add_argument("--files", nargs="+", required=True,
                        help="List of file(s) containing information.")
    return parser.parse_args()


def parse_xml(file_path):
    info_list = []

    try:
        root = ET.parse(file_path).getroot()
    except ET.ParseError as e:
        print("ERROR: " + str(e) + file_path, file=sys.stderr)
        sys.exit(1)

    # Go through each entity and fill information into info_dict
    for entity in root.findall("ENT"):
        info_dict = {}

        for sub_info in entity:
            # Remove extra spaces from both zip formats: 00000-0000 & 00000
            # Also remove '-' from zip format: 00000
            if sub_info.tag.lower() == "postal_code":
                postal_code = sub_info.text.replace(" ", "")

                if postal_code.endswith("-"):
                    info_dict["zip"] = postal_code[:-1]
                else:
                    info_dict["zip"] = postal_code
            # Exclude country and empty sub_info
            elif sub_info.tag.lower() != "country" and sub_info.text.strip():
                info_dict[sub_info.tag.lower()] = sub_info.text.strip()

        if info_dict:
            info_list.append(info_dict)

    return info_list


def parse_tsv(file_path):
    info_list = []

    try:
        with open(file_path, "r") as file:
            reader = csv.DictReader(file, delimiter="\t")

            for row in reader:
                info_dict = {}

                # Organization has actual name
                if row.get("organization").strip() and row.get("organization").strip() != "N/A":
                    info_dict["organization"] = row.get("organization").strip()
                # Only last name exists, so likely to be an organization
                elif row.get("last").strip() and not row.get("first").strip() and not row.get("middle").strip():
                    info_dict["organization"] = row.get("last").strip()
                # Middle name is not-a-middle-name, so don't include it.
                elif row.get("middle").strip() == "N/M/N":
                    info_dict["name"] = row.get(
                        "first").strip() + " " + row.get("last").strip()
                # An actual valid name.
                else:
                    info_dict["name"] = row.get("first").strip(
                    ) + " " + row.get("middle").strip() + " " + row.get("last").strip()

                info_dict["street"] = row.get("address").strip()
                info_dict["city"] = row.get("city").strip()
                info_dict["state"] = row.get("state").strip()

                # zip4 is valid, include it.
                if row.get("zip4").strip():
                    info_dict["zip"] = row.get(
                        "zip").strip() + "-" + row.get("zip4").strip()
                # zip4 is invalid, exclude it.
                else:
                    info_dict["zip"] = row.get("zip").strip()

                if info_dict:
                    info_list.append(info_dict)
    except csv.Error as e:
        print("ERROR: " + str(e) + file_path, file=sys.stderr)
        sys.exit(1)

    return info_list


def parse_txt(file_path):
    info_list = []

    try:
        with open(file_path, "r") as file:
            entities = file.read().split("\n\n")

            for entity in entities:
                sub_info = entity.split("\n")

                # There must be 3-4 valid lines
                if len(sub_info) == 3 or len(sub_info) == 4:
                    entity_dict = {}

                    # If name has inc. llc or ltd. in it, then it's likely an organization.
                    name_lowercase = sub_info[0].lower().strip()
                    if name_lowercase.endswith("inc.") or name_lowercase.endswith("llc") or name_lowercase.endswith("ltd."):
                        entity_dict["organization"] = sub_info[0].strip()
                    else:
                        entity_dict["name"] = sub_info[0].strip()

                    entity_dict["street"] = sub_info[1].strip()

                    if len(sub_info) > 3:
                        entity_dict["county"] = sub_info[2].split()[0].strip()

                    # loc_index is the line # of: city, state zip-code
                    loc_index = len(sub_info) - 1
                    entity_dict["city"] = sub_info[loc_index].split(",")[
                        0].strip()
                    entity_dict["state"] = sub_info[loc_index].split(",")[1].split()[
                        0].strip()

                    # zip ends with "-", so remove it.
                    if sub_info[loc_index].split()[-1].strip().endswith("-"):
                        entity_dict["zip"] = sub_info[loc_index].split(
                        )[-1].strip()[:-1]
                    else:
                        entity_dict["zip"] = sub_info[loc_index].split()[-1]

                    info_list.append(entity_dict)
    except IOError as e:
        print("ERROR: " + str(e) + file_path, file=sys.stderr)

    return info_list


if __name__ == "__main__":
    main()
