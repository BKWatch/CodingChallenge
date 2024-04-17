#
# BankruptcyWatch - Remote: Software Engineer - Natural Language Processing
#   Coding Challenge
#
# Submitted By: Ege Gunal
# Submitted On: 16-Apr-2024
#
# Given a list of files on the command line,
#   extract address information of people and companies
#   then sort by zip code
#


import argparse
import sys
import json
import xml.etree.ElementTree as ET
import csv


final_json = []

#
# Compare zip code of new entry to given index
#
def zip_comp(ind, ent):
    zip_arr = final_json[ind]["zip"]
    zip_ent = ent["zip"]
    # equality check
    if zip_arr == zip_ent:
        return 0
    # compare first 5 digits
    if int(zip_arr[:5]) > int(zip_ent[:5]):
        return +1
    elif int(zip_arr[:5]) < int(zip_ent[:5]):
        return -1
    # first 5 match. if only one is longer, that's the "bigger" one
    if len(zip_arr) > len(zip_ent):
        return +1
    elif len(zip_arr) < len(zip_ent):
        return -1
    # compare last 4 digits 
    if int(zip_arr[6:]) > int(zip_ent[6:]):
        return +1
    else:
        return -1

#   
# binary search for efficient sorted insertions
#
def bin_search(entry, start, end):
    # boundary comp
    if start == end:
        if zip_comp(start, entry) == 1:
            return start
        else:
            return start+1
    if start > end:
        return start
    # right half, left half, exact match
    mid = int((start+end)/2)
    midcomp = zip_comp(mid, entry)
    if midcomp == -1:
        return bin_search(entry, mid+1, end)
    elif midcomp == +1:
        return bin_search(entry, start, mid-1)
    else:
        return mid


#
# binary insertion
#
def bin_insert(entry):
    # first entry
    if len(final_json) == 0:
        final_json.append(entry)
    
    new_ind = bin_search(entry, 0, len(final_json)-1)
    final_json.insert(new_ind, entry)


# 
# Read XML file and turn it into a json object
# with valid fields
# 
def parse_xml(file_path: str):
    # jump directly into ENTITY array
    root = ET.parse(file_path).getroot()[1]
    for child in root:
        # for each ENT
        entry = {}
        for elem in child:
            # for each value in each ENT
            # skip empty or invalid
            if elem.text == " " or elem.tag in ["STREET_2", "STREET_3"]:
                continue
            # elements that require changes
            if elem.tag == "COMPANY":
                entry["organization"] = elem.text
            elif elem.tag == "POSTAL_CODE":
                entry["zip"] = elem.text[:5]
                if elem.text[-2] != "-":
                    entry["zip"] += "-" + elem.text[8:]
            else:
                entry[elem.tag.lower()] = elem.text
        # add to object
        bin_insert(entry)


#
# Read TSV file and turn it into a json object
# with valid fields
#
def parse_tsv(file_path: str, fix_org_people: bool=True):
    with open(file_path) as infile:
        reader = csv.DictReader(infile, delimiter='\t')
        for row in reader:
            entry = {}
            # name field
            if row["middle"] == "N/M/N":
                entry["name"] = " ".join([row["first"], row["last"]])
            elif row["middle"] != "":
                entry["name"] = " ".join([row["first"], row["middle"], row["last"]])
            elif row["organization"] == "N/A":
                # correct for companies that entered as people if selected
                if fix_org_people:
                    entry["organization"] = row["last"]
                else:
                    entry["name"] = row["last"]
            # company name
            if row["organization"] != "N/A":
                entry["organization"] = row["organization"]
            # location
            entry["street"] = row["address"] # rename
            entry["city"] = row["city"]
            entry["state"] = row["state"]
            if row["county"] != "":
                entry["county"] = row["county"]
            # zip merging
            entry["zip"] = row["zip"]
            if row["zip4"]:
                entry["zip"] += "-" + row["zip4"]
            # add to object
            bin_insert(entry)


#
# Read text file and turn it into a json object
# with valid fields
#
def parse_txt(file_path: str):
    # get each relevant blob, separated by empty lines
    with open(file_path) as infile:
        blocks = infile.read().split("\n\n")
    # format check
    if blocks[0] != "" or blocks[-1] != "":
        sys.stderr.write("File {} does not have correct spacing layout!\n".format(file_path))
        raise ValueError
    # go through data
    for block in blocks[1:-1]:
        lines = block.split("\n")
        if len(lines) > 4 or lines[0][:2] != "  ":
            sys.stderr.write("File {} has invalid data layout!\n".format(file_path))
            raise ValueError
        entry = {}
        # fill in values from lines of object
        entry["name"] = lines[0][2:]
        entry["street"] = lines[1][2:]
        # county value is not alwaus provided
        if len(lines) == 4:
            entry["county"] = lines[2][2:-7]
            lines.pop(2)
        # last line has multiple data points
        lastline = lines[2][2:].split(",")
        state_zip = lastline[1].strip().split(" ")
        entry["city"] = lastline[0]
        entry["state"] = " ".join(state_zip[:-1])
        entry["zip"] = state_zip[-1][:5] if len(state_zip[-1]) == 6 else state_zip[-1]
        # add to object
        bin_insert(entry)

#
# main function to call if file is included separately
#
def main():
    parser = argparse.ArgumentParser(description="Collect address information from multiple files and sort them")
    # required args
    parser.add_argument('files', metavar='-f', type=str, nargs="+", help="Path to input file(s)")
    # optional args
    parser.add_argument("-o", metavar="output", type=str, required=False,
                        help="If provided, json will be dumped into target file instead of console")
    parser.add_argument("-c", metavar="correct", type=int, required=False, default=0,
                        help="Correct/Fix companies in TSV registered as individuals")
    parser.add_argument("-i", metavar="indent", type=int, required=False, default=4,
                        help="JSON indentation level")
    args = parser.parse_args()

    # try to process each input file
    try:
        for file_path in args.files:
            if file_path.endswith('.xml'):
                parse_xml(file_path)
            elif file_path.endswith('.tsv'):
                parse_tsv(file_path, fix_org_people=args.c)
            elif file_path.endswith('.txt'):
                parse_txt(file_path)
            else:
                sys.stderr.write("Error: Unsupported file format: {}\n".format(file_path))
                raise TypeError
        # no exceptions, success
        if args.o:
            # write to file if argument is specified
            with open(args.o, "w") as outfile:
                json.dump(final_json, outfile, indent=args.i)
        else:
            print(json.dumps(final_json, indent=args.i))
        print("\nSuccessfully written JSON data onto {}\n".format("file" if args.o else "console"))
        return 0
    except Exception as e:
        # fail
        print("Something went wrong: {}".format(e))
        print("Aborting...")
        return 1


#
# don't run automatically file is called directly
#
if __name__ == "__main__":
    main()
