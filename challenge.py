"""Parse a list of address files and output sorted addresses.

SYNTAX
    challenge.py [file1] [Optional: Additional files]
    Input a series of one or more filenames using xml, tsv, or txt
    extensions as arguments.

OPTIONS
    --help: Provides syntax, options, and description.

DESCRIPTION
    This program accepts files containing properly formatted 
    address data through a few file formats, and prints the 
    JSON encoded data out organized by zip code in ascending 
    order. Each address needs either a name or organization, 
    as well as a street, city, state, and zip code, and may 
    have a county as well.
"""

import sys
import json

def addAddress(address):
    """Validate and add address to public list."""
    if not "name" in address and not "organization" in address:
        print(address)
        sys.stderr.write("Format Error, address missing name/organization\n")
        exit(1)
    for attribute in ["street", "city", "state", "zip"]:
        if not attribute in address:
            sys.stderr.write(
                "Format Error, address missing attribute: "
                + attribute + "\n"
                )
            exit(1)
    addresses.append(address)

def addAttribute(address, attribute, value):
    """Validate and add attribute to input address."""
    value = value.strip()
    if value == "" or value == "N/A":
        return
    if attribute in address:
        sys.stderr.write(
            "Format Error, duplicate attribute found: "
            + attribute + "\n"
            )
        exit(1)
    if attribute == "zip":
        if value[-1] == '-':
            value = value[:-1].strip()
        if ((len(value) != 5 and len(value) != 10) or not 
            value.split('-')[0].isdigit() or not 
            value.split('-')[-1].isdigit()):
            sys.stderr.write(
                "Format error, found zip code: \"" + value
                + "\". Zip must be in one of the following formats: "
                + "00000 or 00000-0000\n"
                )
            exit(1)
    address[attribute] = value

def parseFileXml(fileName):
    """Parse an input xml file and add addresses to public list.
    
    Arguments:
    fileName -- name of file to be parsed

    Return:
    None

    Exceptions:
    OSError if file cannot be read
    """
    file = open(fileName)
    state = 0
    address = {}
    for line in file.readlines():
        if state == 0:
            if line.strip() == "<ENT>":
                state = 1
        elif state == 1:
            if line.strip() == "</ENT>":
                addAddress(address)
                address = {}
                state = 0
            attribute = line.split('<')[1].split('>')[0]
            value = line.split('>')[1].split('<')[0]
            if value.strip() != "":
                if attribute == "NAME":
                    addAttribute(address, "name", value)
                elif attribute == "COMPANY":
                    addAttribute(address, "organization", value)
                elif attribute == "STREET":
                    addAttribute(address, "street", value)
                elif attribute == "STREET_2":
                    if not "street" in address:
                        sys.stderr.write(
                            "Format error, "
                            + "<STREET_2> found before <STREET>\n"
                            )
                        exit(1)
                    address["street"] += ", " + value
                elif attribute == "STREET_3":
                    if not "street" in address:
                        sys.stderr.write(
                            "Format error, "
                            + "<STREET_3> found before <STREET>\n"
                            )
                        exit(1)
                    address["street"] += ", " + value
                elif attribute == "CITY":
                    addAttribute(address, "city", value)
                elif attribute == "STATE":
                    addAttribute(address, "state", value)
                elif attribute == "POSTAL_CODE":
                    if value.split('-')[1].strip() == "":
                        addAttribute(address, "zip", value.strip()[:5])
                    else:
                        addAttribute(address, "zip", 
                                        value.strip()[:5] + "-"
                                        + value.strip()[-4:])
                elif attribute != "COUNTRY":
                    sys.stderr.write(
                        "Format Error, "
                        + "unexpected attribute: " + attribute + "\n"
                        )
                    exit(1)
    file.close()

def parseFileTsv(fileName):
    """Parse an input tsv file and add addresses to public list.
    
    Arguments:
    fileName -- name of file to be parsed

    Return:
    None

    Exceptions:
    OSError if file cannot be read
    """
    file = open(fileName)
    header = file.readline()
    if (header.strip() != "first\tmiddle\tlast\torganization"
        + "\taddress\tcity\tstate\tcounty\tzip\tzip4"):
        sys.stderr.write(
            "Format error, missing/incorrectly formatted header "
            + "in tsv file\n")
        exit(1)
    for line in file.readlines():
        vals = line.split('\t')
        address = {}
        if vals[0].strip() != "":
            addAttribute(address, "name",
                            (vals[0].strip() + " " + vals[1].strip() + " "
                            + vals[2].strip()))
        else:
            addAttribute(address, "organization",
                            (vals[0].strip() + " " + vals[1].strip() + " "
                            + vals[2].strip()))
        if vals[3].strip() != "":
            addAttribute(address, "organization", vals[3])
        addAttribute(address, "street", vals[4])
        addAttribute(address, "city", vals[5])
        addAttribute(address, "state", vals[6])
        addAttribute(address, "county", vals[7])
        addAttribute(address, "zip", vals[8])
        if vals[9].strip() != "":
            if not "zip" in address:
                sys.stderr.write("Format error, "
                                    + "zip4 present with no zip\n")
                exit(1)
            if not vals[9].strip().isdigit() or len(vals[9].strip()) != 4:
                sys.stderr.write("Format error, "
                                    + "zip4 must be in format of 0000: \""
                                    + vals[9].strip() + "\"\n")
                exit(1)
            address["zip"] += "-" + vals[9].strip()
        addAddress(address)
    file.close()
    
def parseFileTxt(fileName):
    """Parse an input txt file and add addresses to public list.
    
    Arguments:
    fileName -- name of file to be parsed

    Return:
    None

    Exceptions:
    OSError if file cannot be read
    """
    file = open(fileName)
    address = {}
    state = 0
    county = ""
    for line in file.readlines():
        if line.strip() == "":
            if state > 0:
                addAddress(address)
                address = {}
                state = 0
        else:
            if state == 0:
                addAttribute(address, "name", line)
                state = 1
            elif state == 1:
                addAttribute(address, "street", line)
                state = 2
            elif state == 2:
                if line.find("COUNTY") != -1:
                    county = line.strip()[:-6].strip()
                else:
                    if (len(line.split(',')) != 2
                        or len(line.split(',')[1].split(' ')) < 2):
                        sys.stderr.write(
                            "Format error, txt file has "
                            + "incorrect/missing zip, state, or city\n"
                            )
                        exit(1)
                    addAttribute(address, "city",
                                    line.split(',')[0])
                    if county != "":
                        addAttribute(address, "county", county)
                        county = ""
                    addAttribute(address, "state",
                                    " ".join(line.split(',')[1]
                                            .split(' ')[:-1]))
                    addAttribute(address, "zip",
                                    line.split(',')[1].split(' ')[-1])
                    state = 3
    file.close()

addresses = []
if len(sys.argv) < 2:
    sys.stderr.write("Needs at least one argument to run, "
                     + "use --help for usage notes\n")
if "--help" in sys.argv:
    print(__doc__)
    exit(0)

for file in sys.argv[1:]:
    try:
        if file.split('.')[-1] == 'xml':
            parseFileXml(file)
        elif file.split('.')[-1] == 'tsv':
            parseFileTsv(file)
        elif file.split('.')[-1] == 'txt':
            parseFileTxt(file)
        else:
            sys.stderr.write("Unsupported file extension: "
                            + file.split('.')[-1] + "\n")
            sys.stderr.write("For usage notes, use --help" + "\n")
            exit(1)
    except OSError as e:
        sys.stderr.write("Could not open file " + file + "\n")
        sys.stderr.write("Error message: " + e.strerror + "\n")
        exit(1)

if len(addresses) > 0:
    addresses.sort(key=lambda x: x["zip"])
    print(json.dumps(addresses, indent=4))
exit(0)