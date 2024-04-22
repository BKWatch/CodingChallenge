import xml.etree.ElementTree as ET
import csv
import json


def parse_xml(file_path):
    addresses = []
    tree = ET.parse(file_path)
    root = tree.getroot()
    for record in root.findall("record"):
        address = {}
        for field in record:
            tag = field.tag.lower()
            if tag == "name":
                address["name"] = field.text
            elif tag == "organization":
                address["organization"] = field.text
            elif tag == "address":
                address["street"] = field.find("street").text
                address["city"] = field.find("city").text
                address["county"] = field.find("county").text
                address["state"] = field.find("state").text
                address["zip"] = field.find("zip").text
        addresses.append(address)
    return addresses


def parse_tsv(file_path):
    addresses = []
    with open(file_path) as file:
        reader = csv.DictReader(file, delimiter="\t")
        for row in reader:
            addresses.append(row)
    return addresses


def parse_txt(file_path):
    addresses = []
    with open(file_path) as file:
        for line in file:
            parts = line.strip().split(",")
            address = {}
            address["name"] = parts[0]
            address["organization"] = parts[1] if len(parts) > 1 else ""
            address["street"] = parts[2] if len(parts) > 2 else ""
            address["city"] = parts[3] if len(parts) > 3 else ""
            address["county"] = parts[4] if len(parts) > 4 else ""
            address["state"] = parts[5] if len(parts) > 5 else ""
            address["zip"] = parts[6] if len(parts) > 6 else ""
            addresses.append(address)
    return addresses


def combine_add(xml_file, tsv_file, txt_file):
    xml_add = parse_xml(xml_file)
    tsv_add = parse_tsv(tsv_file)
    txt_add = parse_txt(txt_file)
    combined_add = xml_add + tsv_add + txt_add
    return combined_add


# Example usage:
xml_file = "input1.xml"
tsv_file = "input2.tsv"
txt_file = "input3.txt"
all_addresses = combine_add(xml_file, tsv_file, txt_file)
print(json.dumps(all_addresses, indent=3))