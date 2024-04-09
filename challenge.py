import xml.etree.ElementTree as ET
from os import path
from collections import defaultdict
import sys
import re
from csv import DictReader
from json import dumps
import argparse


OUTPUT_KEYS = ['company', 'name', 'street', 'city', 'county', 'state','zip']
ZIP_4_PAT = re.compile('\\d{5} ?- ?\\d{4}')
ZIP_PAT = re.compile("\\d{5} ?-? ?")
NULL_VALUES = ["N/M/N", "N/A", '']

def format_zip(raw_zip):
    """Format zip code to xxxxx or xxxxx-yyyy."""
    if re.match(ZIP_4_PAT, raw_zip):
        return raw_zip[:5]+'-'+raw_zip[-4:]
    elif re.match(ZIP_PAT, raw_zip):
        return raw_zip[:5]
    print("Bad zip formatting ", raw_zip, sys.stderr)
    sys.exit(1)

def tsv_row_to_dict(row:dict, ignore:bool) -> dict:
    """Turn row of tsv into dictionary."""
    tsv_entry = {}
    if row['first'] not in NULL_VALUES:
        tsv_entry['name'] = ' '.join(row[key] for key in 
                                    ['first', 'middle', 'last']
                                    if row[key] not in NULL_VALUES)
    elif row['last'] not in NULL_VALUES:
        print(f"Missing first name for family name \"{row['last']}\"",
                     file=sys.stderr)
        if not ignore:
            sys.exit(1)
        tsv_entry['company'] = row['last']
    else:
        tsv_entry['company'] = row['organization']
    for key1, val1 in row.items():
        if key1 in OUTPUT_KEYS and key1 != 'zip' and val1 != '':
            tsv_entry[key1] = val1
    if row['zip'] not in NULL_VALUES and row['zip4'] not in NULL_VALUES:
        tsv_entry['zip'] = row['zip']+'-'+row['zip4']
    else:
        tsv_entry['zip'] = row['zip']
    tsv_entry['street'] = row['address']
    return tsv_entry

def xml_to_dict(ent) -> dict:
    """Turn ENT object of xml hierarchy into dictionary."""
    xml_entry = defaultdict(str)
    for child in ent:
        tag, text = child.tag.lower(), child.text
        if tag.startswith('street') and text.strip() != '':
            xml_entry['street'] += text
        elif tag in OUTPUT_KEYS and text.strip() != '':
            xml_entry[tag.lower()] = text
        elif tag == 'postal_code':
            xml_entry['zip'] = format_zip(text)
    return xml_entry

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'files',
        nargs = '*',
        type = str,
        help = 'Data files to aggregate, containing addresses:'+\
                    'must be .xml, .tsv, or .txt'
    )
    parser.add_argument(
        '-i',
        '--ignore',
        action = "store_true",
        help = "ignore error in .tsv files where company name is"+\
                "in \"last\" column"
    )
    people = []
    args = parser.parse_args()
    for file in args.files:
        if not path.exists(file):
            print("File not found: ", file, file=sys.stderr)
            sys.exit(1)
        if file.endswith(".xml"):
            with open(file, mode = 'r', encoding = 'Latin-1') as f:
                tree = ET.parse(f)
                people += map(xml_to_dict,
                            tree.getroot().findall("./ENTITY/ENT"))
        elif file.endswith(".tsv"):
            with open(file, mode = 'r', encoding = 'utf-8') as f:
                tsvReader = DictReader(f, delimiter = '\t')
                people += map(lambda x : tsv_row_to_dict(x, args.ignore),
                                 tsvReader)
        elif file.endswith('.txt'):
            with open(path.join('input', 'input3.txt'), mode = 'r', \
                        encoding = 'utf-8') as f:
                entry, lineNo = defaultdict(str), 0
                for rawLine in f:
                    line = rawLine.strip()
                    if line == '':
                        if len(entry):
                            people.append(entry)
                        entry, lineNo = defaultdict(str), 0
                        continue
                    if lineNo == 0:
                        entry['name'] = line
                    elif lineNo == 1:
                        entry['street'] = line
                    elif line.lower().endswith('county'):
                        entry['county'] = line[:line.index(' ')]
                    elif re.search(ZIP_4_PAT, line) or \
                                    re.search(ZIP_PAT,line):
                        entry["city"], stateAndZip = line.split(', ')
                        startZip = stateAndZip.rfind(' ')
                        entry["zip"] = format_zip(stateAndZip[startZip+1:])
                        entry["state"] = stateAndZip[:startZip]
                    else:
                        print("Bad or mis-formatted input: ",
                                            line, file=sys.stderr)
                        sys.exit(1)
                    lineNo += 1
        else:
            print("Unrecognized file type", sys.stderr)
            sys.exit(1)
    # sort by zip.
    people.sort(key = lambda person : person['zip'])
    # fix capitalization.
    for person in people:
        for key, val in person.items():
            if key != 'state' or len(val) > 2:
                if all(not char.isalpha() or char.isupper() for char in val):
                    person[key] = ' '.join(word.capitalize()
                                         for word in val.split(' '))
    # make it so all dictionaries are in the same order.
    people =[{key:person[key] for key in OUTPUT_KEYS if key in person}
                                                     for person in people]
    print(dumps(people, indent=4))
    sys.exit(0)
