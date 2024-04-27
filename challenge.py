import xml.etree.ElementTree as ET
import csv
import json
import argparse
import sys

XML_MAP = {
    "NAME": "name",
    "COMPANY": "organization",
    "STREET": "street",
    "CITY": "city",
    "STATE": "state",
    "POSTAL_CODE": "zip"
}

XML_SCHEMA = set(
    [
        "NAME",
        "COMPANY",
        "STREET",
        "STREET_2",
        "STREET_3",
        "CITY",
        "STATE",
        "COUNTRY",
        "POSTAL_CODE"
    ]
)

TSV_SCHEMA = set(
    [
        "first",
        "middle",
        "last",
        "organization",
        "address",
        "city",
        "state",
        "county",
        "zip",
        "zip4"
    ]
)
def parse_xml(file_name):
    tree = ET.parse(file_name)
    root = tree.getroot()
    export_roots = root.iter("EXPORT")
    for export_root in export_roots:
        entity_roots = export_root.iter("ENTITY")
        for entity_root in entity_roots:
            ent_roots = entity_root.iter("ENT")
            data = []
            for ent_root in ent_roots:
                this_data = {}
                children = set()
                for child in ent_root:
                    children.add(child.tag)
                    if child.tag in XML_MAP and child.text.strip():
                        if child.tag == "POSTAL_CODE":
                            this_data[XML_MAP[child.tag]] = deal_with_zip(child.text.strip())
                        else:
                            this_data[XML_MAP[child.tag]] = child.text.strip()
                    if child.tag == "STREET_2" and child.text.strip():
                        this_data["street"] = this_data["street"] + "\n" + child.text
                    if child.tag == "STREET_3" and child.text.strip():
                        this_data["street"] = this_data["street"] + "\n" + child.text
                if children != XML_SCHEMA:
                    raise Exception("The schema of {0} is not correct. {1} is expected, but {2} is received.".format(file_name, XML_SCHEMA, children))
                check_valid(this_data)
                data.append(this_data)
    if not data:
        raise Exception("The content of {0} is either empty, or have wrong root name.".format(file_name))
    return generate_json(data)

def parse_tsv(file_name):
    with open(file_name, "r", newline="") as tsvfile:
        reader = csv.reader(tsvfile, delimiter="\t")
        header = next(reader)
        if TSV_SCHEMA != set(header):
            raise Exception("The schema of {0} is not correct. {1} is expected, but {2} is received.".format(file_name, TSV_SCHEMA, header))
        data = []
        for row in reader:
            this_data = {}
            if row[3] and row[3] != "N/A":
                this_data["organization"] = row[3]
            elif row[2] and (not row[0]):
                this_data["organization"] = row[2]
            else:
                this_data["name"] = " ".join(row[0: 2]).replace("N/M/N ", "")
            this_data["street"] = row[4]
            this_data["city"] = row[5]
            this_data["state"] = row[6]
            if row[7]:
                this_data["county"] = row[7]
            if row[9]:
                this_data["zip"] = row[8] + "-" + row[9]
            else:
                this_data["zip"] = row[8]
            check_valid(this_data)
            data.append(this_data)
    if not data:
        raise Exception("The content of {0} is either empty, or have wrong header name.".format(file_name))
    return generate_json(data)

def parse_txt(file_name):
    with open(file_name, "r") as file:
        this_person = []
        data = []
        for line in file:
            line = line.strip()
            if line:
                this_person.append(line)
            else:
                this_data = {}
                if len(this_person) == 0:
                    continue
                if len(this_person) <3 or len(this_person) > 4:
                    raise Exception("The schema of {0} is not correct. #Rows of each record is expected to be 3 to 4, but {1} is received.".format(file_name, len(this_person)))
                if len(this_person) == 4:
                    this_data["county"] = this_person.pop(2)
                this_data["name"] = this_person[0]
                this_data["street"] = this_person[1]
                this_data["city"] = this_person[2].split(",")[0]
                this_data["state"] = " ".join(this_person[2].split(",")[1].strip().split()[:-1])
                this_data["zip"] = this_person[2].split(",")[1].strip().split()[-1].strip("-")
                check_valid(this_data)
                data.append(this_data)
                this_person = []
        if this_person:
            this_data = {}
            if len(this_person) <3 or len(this_person) > 4:
                raise Exception("The schema of {0} is not correct. #Rows of each record is expected to be 3 to 4, but {1} is received.".format(file_name, len(this_person)))
            if len(this_person) == 4:
                this_data["county"] = this_person.pop(2)
            this_data["name"] = this_person[0]
            this_data["street"] = this_person[1]
            this_data["city"] = this_person[2].split(",")[0]
            this_data["state"] = " ".join(this_person[2].split(",")[1].strip().split()[:-1])
            this_data["zip"] = this_person[2].split(",")[1].strip().split()[-1].strip("-").replace(" ", "")
            check_valid(this_data)
            data.append(this_data)
    if not data:
        raise Exception("The content of {0} is either empty, or have wrong header name.".format(file_name))
    return generate_json(data)
        
def generate_json(data):
    sorted_data = sorted(data, key=lambda x: x.get('zip', ''))
    sorted_json_data = json.dumps(sorted_data, indent=2, sort_keys=True)
    return sorted_json_data

def deal_with_zip(zip):
    zip = zip.replace(" ", "")
    if zip[-1] == "-":
        zip = zip[: -1]
    return zip

def check_valid(this_data):
    if "name" in this_data and "organization" in this_data:
        raise Exception("Only one of name and organization should exist.")
    if ("name" not in this_data) and ("organization" not in this_data):
        raise Exception("name or organization should exist.")
    if "city" not in this_data:
        raise Exception("city should exist.")
    if "state" not in this_data:
        raise Exception("state should exist.")
    if "zip" not in this_data:
        raise Exception("zip should exist.")
    if "street" not in this_data:
        raise Exception("street should exist.")

def main(args):
    try:
        if args.xml_list:
            for xml_file in args.xml_list:
                print("Start parsing {0}".format(xml_file))
                sorted_json_data = parse_xml(xml_file)
                print("{0} finished, the result is:".format(xml_file))
                print(sorted_json_data)
        if args.tsv_list:
            for tsv_file in args.tsv_list:
                print("Start parsing {0}".format(tsv_file))
                sorted_json_data = parse_tsv(tsv_file)
                print("{0} finished, the result is:".format(tsv_file))
                print(sorted_json_data)
        if args.txt_list:
            for txt_file in args.txt_list:
                print("Start parsing {0}".format(txt_file))
                sorted_json_data = parse_txt(txt_file)
                print("{0} finished, the result is:".format(txt_file))
                print(sorted_json_data)
    except Exception as e:
        print("An error occurred: {0}".format(str(e)), file=sys.stderr)
        exit(1)
    exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This script extracts address of person or organization from input xml, tsv, or txt file. For detailed formation requirement, please check\
                                     https://github.com/BKWatch/CodingChallenge/tree/main')
    
    parser.add_argument('--xml', nargs='+', type=str, dest='xml_list', help='Space separate xml files input')
    parser.add_argument('--tsv', nargs='+', type=str, dest='tsv_list', help='Space separate tsv files input')
    parser.add_argument('--txt', nargs='+', type=str, dest='txt_list', help='Space separate txt files input')
    args = parser.parse_args()

    main(args)