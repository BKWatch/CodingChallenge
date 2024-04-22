import argparse
import json
import os
import sys
import csv
import xml.etree.ElementTree as ET
from collections import defaultdict


def parse_xml(fp):
    """Parses an xml file and extracts entity records.

    Args:
        fp: The filepath of the txt file.
    Returns:
        A list of entity defaultdicts.
    Raises:
        Exception: if fp is unable to be parsed.
    """
    records = []
    try:
        tree = ET.parse(fp)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing {fp}\n{e}", file=sys.stderr)
        sys.exit(1)
    for ent in root.findall(".//ENT"):
        record = defaultdict()
        for element in ent:
            tag = element.tag
            text = element.text.strip()
            if text:
                if tag == "NAME":
                    record["name"] = text
                elif tag == "COMPANY":
                    record["organization"] = text
                elif tag == "STREET":
                    record["street"] = text
                elif tag == "STREET_2":
                    record["street"] = ", ".join([record["street"], text])
                elif tag == "STREET_3":
                    record["street"] = ", ".join([record["street"], text])
                elif tag == "CITY":
                    record["city"] = text
                elif tag == "STATE":
                    record["state"] = text
                elif tag == "POSTAL_CODE":
                    zip = text.replace(" ", "")
                    if zip[-1] == "-":
                        zip = zip[:-1]
                    record["zip"] = zip
        records.append(record)
    return records


def parse_tsv(fp):
    """Parses a tsv file and extracts entity records.

    Args:
        fp: The filepath of the txt file.
    Returns:
        A list of entity defaultdicts.
    Raises:
        Exception: if fp is unable to be parsed.
    """
    records = []
    try:
        with open(fp, 'r') as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader)  # to skip the headers
            for row in reader:
                record = defaultdict()
                if row[0] == "" and row[3] == "N/A":
                    row[3] = row[2]
                    row[2] = ""
                if row[3] == "N/A":
                    row[3] = ""
                if row[1] == "N/M/N":
                    row[1] = ""
                if row[0]:
                    record["name"] = " ".join(filter(None, row[:3]))
                if row[3]:
                    record["organization"] = row[3]
                record["street"] = row[4]
                record["city"] = row[5]
                if row[7]:
                    record["county"] = row[7]
                record["state"] = row[6]
                if row[9]:
                    record["zip"] = "-".join(row[8:])
                else:
                    record["zip"] = row[8]
                records.append(record)
    except Exception as e:
        print(f"Error parsing {fp}\n{e}", file=sys.stderr)
        sys.exit(1)
    return records


def parse_txt(fp):
    """Parses a txt file and extracts entity records.

    Args:
        fp: The filepath of the txt file.
    Returns:
        A list of entity defaultdicts.
    Raises:
        Exception: if fp is unable to be parsed.
    """
    records = []
    try:
        with open(fp, 'r') as f:
            entities = f.read().split("\n\n")[1:-1]
            entities = [i.strip().split("\n  ") for i in entities]
            for ent in entities:
                record = defaultdict()
                record["name"] = ent[0]
                record["street"] = ent[1]
                # insert the key/values in order to make life easy
                if len(ent) == 4:
                    location = txt_address_splitter(ent[3])
                    record["city"] = location[0]
                    record["county"] = ent[2][:-7]
                    record["state"] = location[1]
                    record["zip"] = location[2]
                else:
                    location = txt_address_splitter(ent[2])
                    record["city"] = location[0]
                    record["state"] = location[1]
                    record["zip"] = location[2]
                records.append(record)
    except Exception as e:
        print(f"Error parsing {fp}\n{e}", file=sys.stderr)
        sys.exit(1)
    return records


def txt_address_splitter(text):
    """splits a given location string and returns a list"""
    city, _ = text.split(", ")
    _ = _.split()
    zipcode = _[-1]
    state = " ".join(_[:-1])
    if zipcode[-1] == "-":
        zipcode = zipcode[:-1]
    return [city, state, zipcode]


def main():
    parser = argparse.ArgumentParser(
        description="~~~~~BankruptcyWatch file processor~~~~~"
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=str,
        metavar="file",
        help="file to be processed; accepted formats are .xml, .tsv, .txt",
    )
    args = parser.parse_args()

    # check for invalid input files before parsing
    invalids = []
    for fp in args.files:
        _, ext = os.path.splitext(fp)
        if not os.path.exists(fp):
            invalids.append([fp, "No such file or directory."])
        elif ext not in [".xml", ".tsv", ".txt"]:
            invalids.append(
                [fp, "Unsupported file extension; use --help for details."])
    if invalids:
        for i in invalids:
            print(f"Invalid input file {i[0]}: {i[1]}", file=sys.stderr)
        sys.exit(1)

    # parse through all files
    records = []
    for fp in args.files:
        _, ext = os.path.splitext(fp)
        if ext == ".xml":
            records.extend(parse_xml(fp))
        elif ext == ".tsv":
            records.extend(parse_tsv(fp))
        elif ext == ".txt":
            records.extend(parse_txt(fp))

    # sort and dump as json
    records.sort(key=lambda record: record["zip"])
    output = json.dumps(records, indent=2)
    print(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
