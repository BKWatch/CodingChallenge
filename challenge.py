import sys
import csv
import json
import xml.etree.ElementTree as ET
import pathlib
import re

helptxt = ("BankruptcyWatch Coding Challenge\n"
           "Merges and sorts address data from xml, tsv, and txt file by zip code\n\n"
           "add file paths as arguments you would like to include with the execution of this program")

no_county_err = ("Insure your file is properly formatted and each entry looks like this\n" +
                 "EXAMPLE:\n\n" + "NAME\nSTREET\n(OPTIONAL)COUNTY\nCITY, STATE, ZIP")


def option_handler(opt):
    """
    handles .
    :param opt: command line options like "--help"
    :return: void
    """
    match opt:
        case "help":
            print(helptxt)

        case _:
            print("unrecognized options.\n"
                  "Use --help to see what you can do!")


def file_handler(files):
    """
    calls the correct function according to filename.
    :param files: list of files that are verified to exist
    :return void: 
    """
    for filename in files:
        match filename[-3:]:
            case "txt":
                txt_handler(filename)
            case "xml":
                xml_handler(filename)
            case "tsv":
                tsv_handler(filename)
            case _:
                print(filename +
                      " is not suitable for this program.\n please use files with txt, tsv, or xml extensions")
                sys.exit()


def txt_handler(path, ):
    """
    reads input from txt file and stores data in array
    :param path: filename the user provided in the list of arguments
    :return void: 
   """
    i = 0
    with open(path) as file:
        lines = file.readlines()

        while i < len(lines):
            county = False
            step = 1

            # found name row
            if not lines[i] == "\n":

                # doesn't have county
                if lines[i + 3] == "\n":
                    step = 4
                else:
                    county = True
                    step = 5

                city, other = lines[i + step - 2].split(',')
                state, _, zip_code = other[1:].rpartition(" ")

                if not city or not state or not zip_code:
                    print("There was something wrong with your address values at line " + str(i + 3 + county)
                          + " in file: " + path)
                    sys.exit(1)

                var = {
                    "name": lines[i][2:-1],
                    "street": lines[i + 1][2:-1],
                    "city": city[2:],
                    "state": state,
                    "zip": zip_code[:5] if len(zip_code) < 10 else zip_code[:10]
                }

                if county:
                    var["county"] = lines[i + 2][2:-1]
                    test = var["county"].split(" ")
                    if not test[1] == "COUNTY":
                        print("there was something wrong with " + path + "at line " + (i + 2) + "\n" + no_county_err)
                        sys.exit()

                result.append(var)

            i = i + step


def xml_handler(path):
    tree = ET.parse(path)
    root = tree.getroot()

    for ent in root[1]:
        var = {}
        for child in ent:
            if child.text == ' ' or child.tag == "COUNTRY" or child.tag[:-1] == "STREET_":
                continue

            if child.tag == "POSTAL_CODE":
                if len(child.text) < 10:
                    var["zip"] = child.text[:5]
                else:
                    var["zip"] = child.text[:5] + "-" + child.text[-4:]
            else:
                var[child.tag.lower()] = child.text
        result.append(var)


def tsv_handler(path):
    with open(path) as file:
        tsv = csv.reader(file, delimiter="\t")
        next(tsv)

        for line in tsv:
            # Selects name or org. Cannot have both, must have one
            if line[0] == line[2] == line[3]:
                print("didn't have a name or organization at line " + str(tsv.line_num))
                sys.exit()

            if line[0] == "":
                name_or_org = line[2]
                key = "organization"
            else:
                key = "name"
                if line[1] == "N/M/N":
                    name_or_org = line[0] + " " + line[2]
                else:
                    name_or_org = line[0] + " " + line[1] + " " + line[2]
            var = {key: name_or_org,
                   "street": line[4],
                   "city": line[5],
                   "county": line[7],
                   "state": line[6],
                   "zip": line[8] if line[9] == "" else line[8] + "-" + line[9]}

            # Remove county if its empty.
            if line[7] == "":
                var.pop("county")
            result.append(var)


def check_file_helper(file_name):
    if not pathlib.Path(file_name).is_file():
        print("file: '" + file_name + "' is not a file")
        exit(1)

    verified_files.append(file_name)


def zip_sort_helper(entry):
    return entry["zip"][:5]


if __name__ == '__main__':
    """
    main loop of script.
    loops through each of the arguments and performs actions based on what it is.
    """
    result = []
    verified_files = []

    # If no arguments given, give default output
    if len(sys.argv) == 1:
        option_handler("Default")

    # Check Inputs before expensive task
    for arg in sys.argv[1:]:

        # is option
        if arg[0:2] == "--":
            option_handler(arg[2:])
            sys.exit()
        else:
            check_file_helper(arg)

    file_handler(verified_files)
    result.sort(key=zip_sort_helper)

    # Print Result
    formatted_result = json.dumps(result, indent=2)
    print(formatted_result)
