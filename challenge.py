import sys
import json
import xml.etree.ElementTree as ET


def extract_xml(file_name) -> list:
    """ Loops over a XML file of entities and converts it into a list of JSON objects """
    user_objects = []
    file_tree = ET.parse(file_name)
    root = file_tree.getroot()
    for entity in root.findall("ENTITY/ENT"):
        user = {}
        name = entity.find("NAME").text.strip()
        if name:
            user["name"] = name
        else:
            user["organization"] = entity.find("COMPANY").text

        street = entity.find("STREET").text.strip()
        street_2 = entity.find("STREET_2").text.strip()
        street_3 = entity.find("STREET_3").text.strip()
        street += f" {street_2}" if street_2 else ""
        street += f" {street_3}" if street_3 else ""

        user["city"] = entity.find("CITY").text
        user["state"] = entity.find("STATE").text
        user["zip"] = entity.find("POSTAL_CODE").text.replace(" ", "").rstrip("-")

        user_objects.append(user)
    return user_objects


def format_tsv(lines: list) -> dict:
    """ Takes an ordered list of user information and formats it into a JSON object """
    user = {}
    if lines[3] != "N/A":
        user["organization"] = lines[3]
    else:
        first_name = f"{lines[0]} " if lines[0] else ""
        mid_name = f"{lines[1]} " if lines[1] and lines[1] != "N/M/N" else ""
        user["name"] = f"{first_name}{mid_name}{lines[2]}"

    user["street"] = lines[4]
    user["city"] = lines[5]
    user["state"] = lines[6]
    if lines[7]:
        user["county"] = lines[7]

    zip_code_extension = ("-" + lines[9]) if lines[9] else ""
    user["zip"] = lines[8] + zip_code_extension
    return user


def extract_tsv(file_name: str) -> list:
    """ Loops over a tsv file to format and store its data as a list of JSON objects """
    file_results = []
    top_skipped = False
    with open(file_name, "r") as tsv_file:
        entry = []
        for line in tsv_file:
            if not top_skipped:
                top_skipped = True
                continue

            user_lines = line.strip(" \n").split("\t")
            file_results.append(format_tsv(user_lines))
        return file_results


def format_txt(lines: list) -> dict:
    """ Takes an ordered list of user info and formats it into a JSON object"""
    user = {}
    user["name"] = lines[0]
    user["street"] = lines[1]
    split_addr = lines[-1].split(",")
    user["city"] = split_addr[0]
    # if 4 lines given, the third wil be county
    if len(lines) > 3:
        user["county"] = lines[2]
    remaining_addr = split_addr[1].split(' ')
    user["state"] = ' '.join(remaining_addr[1:-1])
    user["zip"] = remaining_addr[-1]
    return user


def extract_txt(file_name: str) -> list:
    """ Loops over a txt file of user entities and converts it into a list of JSON objects """
    file_results = []
    with open(file_name, "r") as txt_file:
        user_lines = []
        for line in txt_file:
            line = line.strip(" \n-")
            if line:
                user_lines.append(line)
            elif user_lines:
                file_results.append(format_txt(user_lines))
                user_lines = []
    return file_results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Error: Please provide at least one argument")
        exit(0)

    if sys.argv[1] == "--help":
        print("usage: python challenge.py [options] input_file [input_files ...]\n")
        print("Processes one or more input files and returns file data in JSON sorted by zip code\n")
        print("arguments: ")
        print("input_files: one or more paths to xml, tsv, or txt input files\n")
        print("options:")
        print("--help: display help message\n")
        exit(1)

    for arg in sys.argv[1:]:
        split_name = arg.split(".")
        if len(split_name) < 2 or split_name[-1] not in ["xml", "tsv", "txt"]:
            sys.stderr.write(
                "Error: Please only provide files with the extensions xml, tsv, or txt"
            )
            exit(0)

    user_objects = []
    for file_name in sys.argv[1:]:
        file_extension = file_name.split(".")[-1]
        if file_extension == "xml":
            user_objects += extract_xml(file_name)
        elif file_extension == "tsv":
            user_objects += extract_tsv(file_name)
        elif file_extension == "txt":
            user_objects += extract_txt(file_name)

    sorted_user_objects = sorted(user_objects, key=(lambda x: x["zip"]))
    print(json.dumps(sorted_user_objects, indent=2))
    exit(1)
