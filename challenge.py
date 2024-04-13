import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
import csv
import json

from collections import namedtuple


Address = namedtuple(
    "Address",
    [
        "name",
        "organization",
        "street",
        "city",
        "county",
        "state",
        "zip",
    ],
)

# Set default values for all fields that can be None
Address.__new__.__defaults__ = (None,) * len(Address._fields)


FILE_FORMATS = ["xml", "tsv", "txt"]


def create_address(entry):
    return Address(
        name=entry.get("name", None),
        organization=entry.get("organization", None),
        street=entry.get("street"),
        city=entry.get("city"),
        county=entry.get("county", None),
        state=entry.get("state"),
        zip=entry.get("zip"),
    )


def validate_address(data):
    if not all(data[field] for field in ["street", "city", "state", "zip"]):
        return False
    if not (data["name"] or data["organization"]):
        return False
    if not re.match(r"^\d{5}(-\d{4})?$", data["zip"]):
        return False
    return True


def parse_xml(filename):
    """Parses  XML file assumming specific format, validates against required tags"""
    addresses = []

    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        entity_tag = root.find("ENTITY")

        if entity_tag is None:
            raise Exception("xml doesnt have right root tag")

        for ent in entity_tag.findall("ENT"):
            address = parse_ent_and_validate_address(ent)
            if address is not None:
                addresses.append(address)

    except ET.ParseError as e:
        raise Exception(f"cant parse XML file {filename}: e")
    except Exception as e:
        raise Exception(f"unexpected error parsing XML {filename}: {e}")

    return addresses


def parse_ent_and_validate_address(ent):
    """Parses an ENT element from the XML and validates address fields
    returning a populated Address namedtuple or None if data or tag is missing.
    """
    name = ent.find("NAME")
    company = ent.find("COMPANY")
    street = ent.find("STREET")
    city = ent.find("CITY")
    state = ent.find("STATE")
    postal_code = ent.find("POSTAL_CODE")

    # check if it doesnt have all required tags
    if (
        name is None
        or company is None
        or street is None
        or city is None
        or state is None
        or postal_code is None
    ):
        return None

    processed_postal_code = process_postal_code(postal_code.text.strip())
    if not processed_postal_code:
        return None

    address = create_address(
        {
            "name": name.text.strip() if name.text.strip() else None,
            "organization": company.text.strip() if company.text.strip() else None,
            "street": street.text.strip(),
            "city": city.text.strip(),
            "state": state.text.strip(),
            "zip": processed_postal_code,
        }
    )

    if not validate_address(address._asdict()):
        return None

    return address


def process_postal_code(postal_code_str):
    """
    Processes a postal code string, splitting by hyphen, removing spaces,
    and returning the formatted code or None if the format is invalid.
    """
    # Remove non-digit characters
    processed_code = re.sub(r"\D", "", postal_code_str)

    # Check if the processed code is a valid 5-digit or 9-digit ZIP code
    if re.match(r"^\d{5}(?:\d{4})?$", processed_code):
        # Reformat the code to either 00000 or 00000-0000
        if len(processed_code) == 9:
            return f"{processed_code[:5]}-{processed_code[5:]}"
        else:
            return processed_code.zfill(5)
    else:
        return None


def parse_tsv(filename):
    """Read and parse addresses from TSV file format"""
    entries = []
    try:
        with open(filename, newline="") as file:
            reader = csv.DictReader(file, delimiter="\t")
            for row in reader:
                organization = (
                    row["organization"] if row["organization"] != "N/A" else None
                )
                county = row["county"] if row["county"] != "N/A" else None
                zip = f"{row['zip']}-{row['zip4']}" if row["zip4"] else row["zip"]

                name = None
                # misplace organization into last name
                if (
                    organization != None
                    and row["first"].strip() == ""
                    and row["middle"].strip() == ""
                    and row["last"].strip() != ""
                ):
                    organization = row["last"].strip()
                else:
                    name_parts = [
                        row["first"].strip(),
                        row["middle"].strip(),
                        row["last"].strip(),
                    ]
                    name = (
                        " ".join(filter(None, name_parts)) if any(name_parts) else None
                    )

                address = create_address(
                    {
                        "name": name,
                        "organization": organization,
                        "street": row["address"].strip(),
                        "city": row["city"].strip(),
                        "county": county,
                        "state": row["state"].strip(),
                        "zip": zip,
                    }
                )

                if validate_address(address):
                    entries.append(address)

    except Exception as e:
        raise Exception(e)

    return entries


def parse_txt(filename):
    try:
        with open(filename, "r") as file:
            content = file.read().strip()
            if not content:
                raise ValueError(f"file {filename} is empty or only contain whitespace")

            blocks = [block.strip() for block in content.split("\n\n") if block.strip()]

            entries = []
            for block in blocks:
                lines = block.split("\n")
                address = parse_txt_address_block(lines)
                if address is not None:
                    entries.append(address)

            return entries

    except Exception as e:
        raise Exception(f"unable to process TXT file {filename}: {e}")


def parse_txt_address_block(lines):
    """Process a block of 3-4 lines that contain address  into an Address entry"""
    if len(lines) == 3:
        name_or_org, street, csz = lines
        county = None
    elif len(lines) == 4:
        name_or_org, street, county, csz = lines
        county = county.strip()
    else:
        raise ValueError("TXT address block should have 3 or 4 lines")

    if name_or_org.isupper():
        organization = name_or_org.strip()
        name = None
    else:
        organization = None
        name = name_or_org.strip()

    city, state_zip = csz.split(",")
    state_zip = state_zip.strip()

    # split state and zip
    last_space_index = state_zip.rfind(" ")
    if last_space_index == -1:
        raise ValueError(
            "unable to find a space seprator, invalid state and zip code format"
        )

    state = state_zip[:last_space_index].strip()
    zip_code = state_zip[last_space_index + 1 :].strip()

    address = create_address(
        {
            "name": name,
            "organization": organization,
            "street": street.strip(),
            "city": city.strip(),
            "county": county,
            "state": state,
            "zip": process_postal_code(zip_code),
        }
    )

    if not validate_address(address._asdict()):
        return None

    return address


def main():
    parser = argparse.ArgumentParser(
        description="Combine and sort addreses from xml, tsv and txt file formats"
    )
    parser.add_argument(
        "files",
        metavar="file",
        type=str,
        nargs="+",
        help="path to files containing addresses",
    )

    args = parser.parse_args()

    addresses = []
    for filename in args.files:
        try:
            if not os.path.exists(filename):
                raise ValueError(f"file {filename} does not exist.")

            if not os.path.isfile(filename):
                raise ValueError(f"file {filename} is not a file.")

            ext = os.path.splitext(filename)[-1].lower()

            ext = filename.split(".")[-1]
            if ext not in FILE_FORMATS:
                raise ValueError(
                    f"unsupported file format for '{filename}'. Only {', '.join(FILE_FORMATS).upper()} are supported."
                )

            if ext == "xml":
                addresses.extend(parse_xml(filename))
            if ext == "tsv":
                addresses.extend(parse_tsv(filename))
            if ext == "txt":
                addresses.extend(parse_txt(filename))
        except Exception as e:
            # stderr error message and exit program
            sys.stderr.write(f"Error: {e}")
            sys.exit(1)

    # sort addresses and print out as json
    sorted_addresses = sorted(addresses, key=lambda addr: addr.zip)

    # convert each address to dictionary
    addresses_dict = [
        {k: v for k, v in addr._asdict().items() if v is not None and v != ""}
        for addr in sorted_addresses
    ]

    json.dump(addresses_dict, sys.stdout, indent=2)

    sys.exit(0)


if __name__ == "__main__":
    main()
