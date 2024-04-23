import xml.etree.ElementTree as ET
import json
import sys
sys.tracebacklimit = 0

### PARSE ###
# Option 1: .txt
# Take a text file, return a string containing the file's contents
def file_txt_contents(location):
    file_opened = open(location)
    file_contents = file_opened.read().strip()
    file_opened.close()

    return file_contents

# Take a text file's contents, return a list containing each individual entry
def file_txt_split_entries(contents):
    contents_entries = contents.split("\n\n")

    return contents_entries

# Take an entry's contents and split those by line
def file_txt_entry_split_line(entry):
    entry_lines = entry.split("\n")
    entry_cleaned = [e.strip() for e in entry_lines]

    return entry_cleaned

# Parse Address Line into City, State, Zip
def file_txt_entry_to_address(address):
    city_state = address.split(", ")
    state_zip = city_state[1].rsplit(" ", 1)
    city_state_zip = [city_state[0]] + state_zip

    return(city_state_zip)

# Prepare Full Entry
def file_txt_entry_prepare(entry):
    entry_split = file_txt_entry_split_line(entry)
    entry_csz = file_txt_entry_to_address(entry_split[-1])

    entry_split = entry_split[:-1]

    if len(entry_split) == 3:
        return(entry_split[0:2] + [entry_csz[0]] + entry_split[2:] + entry_csz[1:])
    else:
        return(entry_split + [entry_csz[0]] + [""] + entry_csz[1:])

# Takes a Prepared Entry and turns it into a Dictionary
def file_txt_prepared_to_dict(prepared):
    key = ["Name", "Street", "City", "County", "State", "Zip"]

    dictionary = dict(zip(key, prepared))

    return({key:entry for (key, entry) in dictionary.items() if entry != ""})

# Takes a text file and returns a list of dictionaries for each entry
def file_txt_parse(file):
    contents = file_txt_contents(file)
    entries = file_txt_split_entries(contents)
    prepared = list(map(file_txt_entry_prepare, entries))
    parsed = list(map(file_txt_prepared_to_dict, prepared))

    return parsed

# Option 2: .tsv

def file_tsv_get_text(tsv):
    file_opened = open(tsv)
    file_contents_lines = file_opened.read().strip().split("\n")
    file_contents_entries = [s.split("\t") for s in file_contents_lines[1:]]
    file_contents_entries_cleaned = []

    for s in file_contents_entries:
        if s[3] == "N/A" and s[0] == "":
            s.pop(3)
            s.insert(2, "")
            file_contents_entries_cleaned.append(s)
        else:
            file_contents_entries_cleaned.append(s)
            
    file_opened.close()

    return file_contents_entries_cleaned

def file_tsv_prepare_list(tsv_list):
    output_list = []
    output_list.append(' '.join(name for name in tsv_list[0:3] if name != 'N/M/N'))
    output_list.extend(tsv_list[3:8])
    output_list.append(tsv_list[8] + "-" + tsv_list[9])

    for i in range(len(output_list)):
        if output_list[i] == "N/A":
            output_list[i] = ""
    return(output_list)

def file_tsv_create_dict(prepared):
    key = ["Name", "Company", "Street", "City", "State", "County", "Zip"]
    
    dictionary = dict(zip(key, prepared))

    return({key:entry for (key, entry) in dictionary.items() if entry.strip() != ""})

def file_tsv_parse(tsv):
    entries = file_tsv_get_text(tsv)
    prepared = list(map(file_tsv_prepare_list, entries))
    parsed = list(map(file_tsv_create_dict, prepared))
    
    return parsed
    
# Option 3: .xml
def file_xml_get_text(entity):
    name = entity.find("NAME").text
    company = entity.find("COMPANY").text
    street = entity.find("STREET").text + entity.find("STREET_2").text + entity.find("STREET_3").text
    city = entity.find("CITY").text
    state = entity.find("STATE").text
    zip_code = entity.find("POSTAL_CODE").text

    text_list = [name, company, street, city, state, zip_code]
    return [s.strip() for s in text_list]
    
def file_xml_get_root(xml):
    tree = ET.parse(xml)
    root = tree.getroot()

    entities = root.findall(".//ENTITY/")

    return entities

def file_xml_create_list(xml):
    entities = file_xml_get_root(xml)
    xml_list = []

    for entry in entities:
        xml_list.append(file_xml_get_text(entry))

    return xml_list

def file_xml_create_dict(prepared):
    key = ["Name", "Company", "Street", "City", "State", "Zip"]
    
    dictionary = dict(zip(key, prepared))

    return({key:entry for (key, entry) in dictionary.items() if entry != ""})

def file_xml_parse(xml):
    lists = file_xml_create_list(xml)
    parsed = list(map(file_xml_create_dict, lists))

    return parsed

### Dict to Json ###

def json_from_data(data):
    json_file = open("output.json", "w")

    json.dump(data, json_file, indent=1)

### Check File Formatting ###

# I am so sorry for what follows
def test_txt(txt):
    try:
        t = open(txt)
    except:
        sys.stderr.write("Error: issue opening txt file \"%s\" \n" % txt)
        sys.exit(1)
    else:
        ts = t.read().strip().split("\n\n")
        tss = []
        
        for e in ts:
            tsl = []
            for ee in e.split("\n"):
                tsl.append(ee.strip())
            tss.append(tsl)

    for e in tss:
        try:
            assert len(e) in [3, 4]
        except:
            sys.stderr.write("Error: issue parsing txt file \"%s\": incorrect entry format \n" % txt)
            sys.exit(1)

        for char in e[0]:
            try:
                assert char.isdigit() == False
            except:
                sys.stderr.write("Error: issue parsing txt file \"%s\": incorrect name format \n" % txt)
                sys.exit(1)

        for char in e[-1].split(", ")[-1].split(" ")[-1]:
            try:
                assert char.isalpha() == False
            except:
                sys.stderr.write("Error: issue parsing txt file \"%s\": incorrect zip format \n" % txt)
                sys.exit(1)
    t.close()

def test_tsv(tsv):
    cols = "first\tmiddle\tlast\torganization\taddress\tcity\tstate\tcounty\tzip\tzip4"

    try:
        t = open(tsv)
    except:
        sys.stderr.write("Error: issue opening tsv file \"%s\" \n" % tsv)
        sys.exit(1)
    else:
        ts = open(tsv).read().split("\n")

    try:
        assert ts[0] == cols
    except:
        sys.stderr.write("Issue parsing \"%s\": incorrect column structure\n" % tsv)
        sys.exit(1)
    else:
        t.close()

def test_xml(xml):
    try:
        t = ET.parse(xml)
    except:
        sys.stderr.write("Error: issue opening xml file \"%s\" \n" % xml)
        sys.exit(1)
    else:
        ts = t.getroot()
        tss = ts.findall(".//ENTITY/")

    for entry in tss:
        structure = ['NAME', 'COMPANY', 'STREET', 'STREET_2', 'STREET_3', 'CITY', 'STATE', 'COUNTRY', 'POSTAL_CODE']
        tags = []
        
        for child in entry:
            tags.append(child.tag)

        try:
            assert tags == structure
        except:
            sys.stderr.write("Issue parsing xml file \"%s\": incorrect column structure\n" % xml)
            sys.exit(1)

### Terminal Arguments ###

def print_help():
    print(f"""Usage: parse.py [FILES] \nTakes xml, tsv, or txt files of given format and parses them to JSON\n\nExample:
    parse.py input1.xml\tTakes input1.xml and parses text to JSON""")
 
args = sys.argv[1:]

list_dict = []
for arg in args:
    if arg == '-h' or arg == '--help':
        print_help() 
    elif arg.endswith(".tsv"):
        test_tsv(arg)
        list_dict.extend(file_tsv_parse(arg))
    elif arg.endswith(".txt"):
        test_txt(arg)
        list_dict.extend(file_txt_parse(arg))
    elif arg.endswith(".xml"):
        test_xml(arg)
        list_dict.extend(file_xml_parse(arg))
    else:
        sys.stderr.write("ERROR: not a supported filetype; please check parse.py --help for more info\n")
        sys.exit(1)
    
list_dict_sorted = sorted(list_dict, key = lambda x:x['Zip'])
json_from_data(list_dict_sorted)
sys.exit(0)
