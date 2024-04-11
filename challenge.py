import pandas as pd
import xml.etree.ElementTree as ET
import json
import sys 

# Process the TSV File
def tsv_output(input):
    df = pd.read_csv(input, sep="\t")
    
    df["zip"] = df["zip"].astype(str)
    df["zip"] = df["zip"].apply(lambda x: '0'*(5-len(x)) + x if len(x) < 5 else x)
    df["zip4"] = df["zip4"].astype(str).str.replace("\.0", "", regex=True)
    df["zip4"] = ["-" + x if x != 'nan' else "" for x in df["zip4"]]
    df["zip"] += df["zip4"]
    df = df.drop(columns=["zip4"])
    
    def row_convert(row):
        return {key: val for key, val in row.items() if pd.notnull(val)}
    
    df_people = df[df["first"].notnull()].drop(columns=["organization"])
    df_people['middle'] = df_people['middle'].replace("N/M/N", "", regex=True)
    df_people['first'] += ' ' + df_people['middle'] + ' ' + df_people['last']
    df_people['first'] = df_people['first'].replace("  ", " ", regex=True)
    df_people = df_people.rename(columns={"first": "name"})
    df_people = df_people.drop(columns=["last", "middle"])
    df_people_list = df_people.apply(row_convert, axis=1).tolist()
    
    df_orgs = df[~df["first"].notnull()].drop(columns=["first", "middle"])
    df_orgs['last'] = df_orgs['last'].fillna("")
    df_orgs['organization'] = df_orgs['organization'].fillna("")
    df_orgs['organization'] += df_orgs['last']
    df_orgs = df_orgs.drop(columns=["last"])
    df_orgs = df_orgs.apply(row_convert, axis=1).tolist()
    
    return df_people_list + df_orgs

# Process the XML File
def xml_output(input):
    tree = ET.parse(input)
    root = tree.getroot()
    data = []
    for ent in root.findall('.//ENTITY/ENT'):
        record = {
            'name': ent.findtext('NAME'),
            'organization': ent.findtext('COMPANY'),
            'street': (ent.findtext('STREET') 
                       + ent.findtext('STREET_2') 
                       + ent.findtext('STREET_3')).strip(),
            'city': ent.findtext('CITY'),
            'state': ent.findtext('STATE'),
            'country': ent.findtext('COUNTRY'),
            'zip': ent.findtext('POSTAL_CODE').replace(' - ', '-').strip()
        }
        if record['organization'] == " ":
            del record['organization']
        else:
            del record['name']
        if record['country'] == " ":
            del record['country']
        if record['zip'][-1] == "-":
            record['zip'] = record['zip'][:-1]
        data.append(record)

    return data

# Process the TXT File
def txt_output(input):
    input = open(input, "r")
    input = input.read().split("\n\n  ")
    input = [x.split("\n") for x in input if len(x) > 0]

    data = []
    for x in input:
        cur_dict = {}
        name = x[0]
        street = x[1].strip()
        
        pointer = 0
        county = ""
        if "COUNTY" in x[2]:
            county = x[2].strip()
            pointer += 1
            
        move_pointer = 2 + pointer
        zip_idx = x[move_pointer].rfind(" ")
        zipcode = x[move_pointer][zip_idx:].strip()
        if len(zipcode) < 7:
            zipcode = zipcode[:5]
        
        state_idx = x[move_pointer].rfind(",")
        state = x[move_pointer][state_idx+2:zip_idx].strip()
        city = x[move_pointer][:state_idx].strip()
        
        cur_dict["name"] = name
        cur_dict["street"] = street
        cur_dict["city"] = city
        cur_dict["state"] = state
        if len(county) > 0:
            cur_dict["county"] = county
        cur_dict["zip"] = zipcode
        
        data.append(cur_dict)
    
    return data

# Parse the input files
def parse(input):
    data = []
    for x in input[1:]:    
        if x[-4:] == ".tsv":
            data += tsv_output(x)
        elif x[-4:] == ".xml":
            data += xml_output(x)
        elif x[-4:] == ".txt":
            data += txt_output(x)
        else:
            print("Invalid file format", file=sys.stderr)
            sys.exit(1)
    return data

# Sort the data by zip code
def zip_sort(input):
    return sorted(input, key=lambda x: x["zip"])

# Main function
def main():
    input = sys.argv
    
    if "--help" in input:
        print("Script Usage: python challenge.py [input_files...]")
        sys.exit(0)

    if len(input) < 1:
        print("Must Provide File Input", file=sys.stderr)
        sys.exit(1)
        
    data = parse(input)
    if len(data) == 0:
        print("No data found in input files", file=sys.stderr)
        sys.exit(1)

    data = zip_sort(data)
    print(json.dumps(data, indent=2))
    sys.exit(0)

# Run the main function
if __name__ == "__main__":
    main()
