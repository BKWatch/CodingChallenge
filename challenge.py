#Jason Yu
import argparse
import xml.etree.ElementTree as ET
import json
import csv

#Returns a list of filePaths from the commandline
def get_files(argv: list) -> list:
    files = [fileName for fileName in argv]
    return files

#Returns the extension of a filePath
def get_extension(fileName: str) -> str:
    return fileName[fileName.rindex('.')+1:]

def isCounty(line: str) -> bool:
    for letter in line:
        if letter.islower():
            return False
    return True

def parse_location(line: str) -> (str, str, str):
    city = line[0:line.index(',')]
    stateStart = line[line.index(',')+2:]
    state = stateStart[:stateStart.index(' ')]
    zip = parse_zip(line[line.rindex(' '):])
    return city, state, zip

def parse_zip(zipcode_str: str) -> str:
    try:
        index = zipcode_str.index("-")
    except ValueError:
        return zipcode_str
    if index+1 == (len(zipcode_str)-1):
        return zipcode_str[0:index-1]
    return zipcode_str

def parse_xml(file: "File") -> None:
    json_data = []
    tree = ET.parse(file)
    root = tree.getroot().find("ENTITY")

    for entity in root.findall("ENT"):
        info_dict = dict()
        streetStr = ""
        for child in entity:
            if child.text != " ":
                if child.tag == "STREET":
                    streetStr+=child.text
                if child.tag == "STREET_2":
                    streetStr += ", " + child.text
                if child.tag == "STREET_3":
                    streetStr += ", " + child.text
                if child.tag == "POSTAL_CODE":
                    info_dict["zip"] = parse_zip(child.text)
                elif child.tag != "STREET" and child.tag != "STREET_2" and child.tag != "STREET_3":
                    info_dict[child.tag.lower()] = child.text
            if child.tag == "STREET_3":
                info_dict["street"] = streetStr
        json_data.append(info_dict)

    json_str = json.dumps(json_data, indent=4)
    print(json_str)

def parse_tsv(file: "File") -> None:
    tsv_file = csv.reader(file, delimiter="\t")
    raw_data_list = []
    json_data = []

    for line in tsv_file:
        raw_data_list.append(line)

    keyList = raw_data_list[0]
    raw_data_list[1:]

    for line in raw_data_list:
        info_dict = dict()
        name = ""
        for index, value in enumerate(line):
            if index == 0 or (index ==1 and value != "N/M/N") or index ==2:
                if index == 2 and name == "":
                    info_dict["organization"] = value
                elif value != "":
                    name+=" "+value
                if index ==2 and name != "":
                    info_dict["name"] = name
            if value!= '' and index != 0 \
            and index != 1 and index != 2 \
            and value != "N/A":
                if keyList[index] == "address":
                    info_dict["street"] = value
                elif keyList[index] == "zip4":
                    info_dict["zip"] += " - " + value
                else:
                    info_dict[keyList[index]] = value
        json_data.append(info_dict)
    
    json_str = json.dumps(json_data, indent=4)
    print(json_str)


def parse_txt(file: "File") -> None:
    json_data = []
    temp_dict = dict()
    lineCount = 0

    while True:
        line = file.readline()
        
        if not line:
            break
        if line != "\n":
            line = line.strip()
        if line == "\n":
            if len(temp_dict) > 0:
                json_data.append(temp_dict)
            temp_dict = dict()
            lineCount = 0
        elif lineCount == 1:
            temp_dict["name"] = line
        elif lineCount == 2:
            temp_dict["street"] = line
        elif lineCount == 3 and isCounty(line):
            temp_dict["county"] = line
        elif lineCount == 3 or lineCount == 4:
            city, state, zip = parse_location(line)
            temp_dict["city"] = city
            temp_dict["state"] = state
            temp_dict["zip"] = zip
        lineCount+=1

    json_str = json.dumps(json_data, indent=4)
    print(json_str)
    

def main(argv: list) -> int:
    files = get_files(argv.files)
    files_index = 0

    while(files_index<len(files)):
        try:
            with open(files[files_index]) as file:
                extension = get_extension(files[files_index])
                if extension == "xml":
                    parse_xml(files[files_index])
                if extension == "tsv":
                    parse_tsv(file)
                if extension == "txt":
                    parse_txt(file)
        except FileNotFoundError:
            print(f"FileNotFound: {files[files_index]}")
            return 1
        files_index+=1
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog= "challenge.py", description="""
        The challenge.py script accepts a list of paths. It will parse the arguments
        and print a JSON encoded list if there are no
        errors in the input.
        """)
    parser.add_argument("--files", nargs='+', required=True, help="list of files")
    argv = parser.parse_args()
    main(argv)