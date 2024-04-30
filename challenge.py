import argparse
import csv
import json
import os
import pathlib
import re
import xml.etree.ElementTree as ET

# Set up args and help dialogue
parser = argparse.ArgumentParser(
    description='Aggregate one or more XML, TSV, or TXT files to a single JSON output')
parser.add_argument(
    'filenames',
    nargs='*',
    help='a list of 1 or more XML, TSV, or TXT absolute filepaths')

# List of valid file extensions
valid_extensions = ['.txt', '.tsv', '.xml']
unwanted_data = ["", "N/A", None]


def checkFile(path):
    '''Check that a filepath points to a valid location, and has a valid extension.
    Does NOT read file or verify file content'''
    if not os.path.isfile(path):
        raise FileNotFoundError(f'Invalid path {path}: No file found')
    if pathlib.Path(path).suffix not in valid_extensions:
        raise ValueError(
            f'Invalid file extension {path}: Valid extension types are {valid_extensions}')


class Entry:
    '''Standardized class for output'''
    name: str
    org: str
    street: str
    city: str
    county: str
    state: str
    zip: str

#####
# TSV Functionality
#####


def getNameFromTSV(item):
    '''Construct & return the provided name from first, middle, and last'''
    first = item["first"]
    middle = item["middle"]
    last = item["last"]
    name = ""

    if first != "":
        name += first + " "
    if middle != "" and middle != "N/M/N":
        name += middle + " "
    if last != "":
        name += last + " "
    name = name.strip()
    if name != "":
        return name
    return


def parseTSV(path):
    '''Takes a filepath to a .tsv file & Returns a list of Entry objects'''
    entries = []
    with open(path, "r", encoding="utf8") as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter="\t")
        for item in reader:
            entry = Entry()
            entry.name = getNameFromTSV(item)
            entry.org = item["organization"]
            entry.street = item["address"]
            entry.city = item["city"]
            entry.county = item["county"]
            entry.state = item["state"]
            if item["zip4"] != "":
                entry.zip = '-'.join([item["zip"], item["zip4"]])
            else:
                entry.zip = item["zip"]
            entries.append(entry)
    return entries


#####
# TXT Functionality
#####

# Regexes
# to isolate city state & zip from a formatted line
cityStateZipRegex = re.compile(
    r'(?P<city>[\w\s]+), (?P<state>[\w\s]+) (?P<zip>\d+-?\d*)')

# to detect and isolate county entries in text files
# match only if only caps and whitespace followed by the word COUNTY
countyTextFileRegex = re.compile(r'[A-Z\s]+(?=COUNTY)')


def parseCityStateZip(cityStateZip, entry):
    match = re.search(cityStateZipRegex, cityStateZip)
    entry.city = match.group("city")
    entry.state = match.group("state")
    entry.zip = match.group("zip").rstrip('-')

    return entry


def createNewEntryFromTxt(lines, i):
    entry = Entry()

    entry.name = lines[i].strip()
    entry.street = lines[i+1].strip()

    countyMatch = re.search(countyTextFileRegex, lines[i+2].strip())
    if countyMatch != None:
        entry.county = countyMatch.group().strip()
        cityStateZip = lines[i+3].strip()
    else:
        cityStateZip = lines[i+2].strip()

    entry = parseCityStateZip(cityStateZip, entry)

    return entry


def parseTXT(path):
    entries = []
    reset = True

    with open(path, "r", encoding="utf8") as txt_file:
        lines = txt_file.readlines()
        txt_file.close()

    for i in range(len(lines)):
        # skip empty lines & reset for new entry
        if lines[i] == '\n':
            reset = True
            continue

        if reset:
            reset = False
            entry = createNewEntryFromTxt(lines, i)

            entries.append(entry)

    return entries


# XML Functionality

def parseXML(path):
    entries = []

    tree = ET.parse(path)
    root = tree.getroot()
    for item in root.iter('ENT'):
        entry = Entry()
        for child in item:
            match child.tag:
                case "NAME":
                    entry.name = child.text.strip()
                case "COMPANY":
                    entry.org = child.text.strip()
                case "STREET":
                    entry.street = child.text.strip()
                case "STREET_2":
                    entry.street += " " + child.text.strip()
                case "STREET_3":
                    entry.street += " " + child.text.strip()
                case "CITY":
                    entry.city = child.text.strip()
                case "STATE":
                    entry.state = child.text.strip()
                case "POSTAL_CODE":
                    entry.zip = child.text.replace(" ", "")

        entry.street = entry.street.strip()
        entry.zip = entry.zip.rstrip(" -")
        entries.append(entry)

    return entries


if __name__ == "__main__":
    # Collect args
    args = parser.parse_args()

    # Quick check for errors in args list
    for file in args.filenames:
        checkFile(file)

    results = []
    # Actual data processing iteration
    for file in args.filenames:
        fileType = pathlib.Path(file).suffix
        match fileType:
            case '.tsv':
                entries = parseTSV(file)
            case '.txt':
                entries = parseTXT(file)
            case '.xml':
                entries = parseXML(file)
        if entries != []:
            results += entries
        results.sort(key=lambda x: x.zip)

        for result in results:
            cleanResult = {}
            for k, v in result.__dict__.items():
                if v in unwanted_data:
                    continue
                cleanResult[k] = v

            jsonstr = json.dumps(cleanResult, indent=4)
            print(jsonstr)
