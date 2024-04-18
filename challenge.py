import argparse
import sys
import json
import csv
from xml.etree import ElementTree as ET


def parse_xml(path):
    """
    Parses an xml file of addresses and returns them as a list of dicts
    """
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        addresses = []
        for item in root.findall(".//ENT"):
            try:
                address = {"name": item.find("NAME").text.strip(), "organization": item.find("COMPANY").text.strip(),
                           "street": f"{item.find("STREET").text.strip()} {item.find("STREET_2").text.strip()} "
                                     f"{item.find("STREET_3").text.strip()}".strip(),
                           "city": item.find("CITY").text,
                           "state": item.find("STATE").text, "zip": item.find("POSTAL_CODE").text.strip(" - ")}
                # Remove values that aren't present
                address = {key: address[key] for key in address if address[key] != ""}
            except AttributeError as ae:
                print(f"Error parsing file {path}. Please ensure that it is formatted correctly", file=sys.stderr)
                sys.exit(1)

            # Sample XML input has a country tag, but this is not asked for in the instructions
            # address["country"] = item.find("COUNTRY").text
            addresses.append(address)
    except FileNotFoundError:
        print(f"File {path} could not be found", file=sys.stderr)
        sys.exit(1)
    except ET.ParseError:
        print(f"Error parsing file {path}. Please ensure that it is formatted correctly", file=sys.stderr)
        sys.exit(1)
    return addresses


def parse_tsv(path):
    """
    Parses a tsv file of addresses and returns them as a list of dicts
    """
    try:
        with open(path) as fd:
            rd = csv.reader(fd, delimiter="\t", quotechar='"')
            next(rd)
            addresses = []
            for row in rd:
                address = {}
                name = ""
                if row[0] != " ":
                    name += row[0]
                if row[1] != " " and row[1] != "N/M/N":
                    name += " " + row[1]
                # In some cases, a company name is listed in the last name column. I think it makes more sense
                # to treat this as an input error rather than an edge case to handle for the organization field.
                if row[2] != " " and row[2] != "N/A":
                    name += " " + row[2]
                if name.strip() != "":
                    address["name"] = name
                if row[3] != "N/A":
                    address["organization"] = row[3]
                address["street"] = row[4]
                address["city"] = row[5]
                address["state"] = row[6]
                address["country"] = row[7]
                zip_code = row[8]
                if row[9].strip != "":
                    zip_code += "-" + row[9]
                address["zip"] = zip_code
                addresses.append(address)
    except FileNotFoundError:
        print(f"File {path} could not be found", file=sys.stderr)
        sys.exit(1)
    except IOError:
        print(f"Error parsing file {path}. Please ensure that it is formatted correctly", file=sys.stderr)
        sys.exit(1)

    return addresses


def parse_txt(path):
    """
        Parses a tsv file of addresses and returns them as a list of dicts
    """
    try:
        with open(path) as fd:
            addresses = []
            for line in fd:
                if line != "\n":
                    address = {"name": line.strip(), "street": next(fd).strip()}
                    county_or_city = next(fd)
                    if county_or_city.endswith("COUNTY\n"):
                        # Assuming "COUNTY" should be left in
                        address["county"] = county_or_city.strip()
                        city_state_zip = next(fd).strip().split(",")
                    else:
                        city_state_zip = county_or_city.strip().split(",")
                    address["city"] = city_state_zip[0].strip()
                    state_zip = city_state_zip[1].strip().split(" ")
                    address["state"] = state_zip[0]
                    address["zip"] = state_zip[1].strip("-")
                    addresses.append(address)
            return addresses
    except FileNotFoundError:
        print(f"File {path} could not be found", file=sys.stderr)
        sys.exit(1)
    except IOError:
        print(f"Error parsing file {path}. Please ensure that it is formatted correctly", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Parse addresses from files in XML, TSV, and TXT formats and output them in JSON format.')
    parser.add_argument(
        'paths', nargs='*',
        help='List of file paths to process')
    paths = parser.parse_args().paths
    addresses = []
    for path in paths:
        if path.endswith(".xml"):
            addresses.extend(parse_xml(path))
        elif path.endswith(".tsv"):
            addresses.extend(parse_tsv(path))
        elif path.endswith(".txt"):
            addresses.extend(parse_txt(path))
        else:
            print("All files must be in XML, TSV, or TXT format", file=sys.stderr)
            sys.exit(1)

    print(json.dumps(addresses, indent=4))
