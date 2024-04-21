import sys
import xml.etree.ElementTree as ET
import json

def get_name(first,middle,last):
    if middle == "" or middle == None or middle == "N/M/N":
        full_name = first + " " + last
    else:
        full_name = first + " " + middle + " " + last
    return full_name

def get_zip(zip):
    if len(zip) == 1:
        return zip[0]
    return zip[0]+"-"+zip[1]

def get_address_fields(data, line):
    # split the address into city, state, and zip
    address_fields = line.split(',')
    *state, zip = address_fields[1].strip().split(' ')
    
    # remove ending '-' from zip
    if zip[-1] == '-':
        zip = zip.strip().replace("-","")
    
    # add the address fields to the data dictionary
    data['city'] = address_fields[0].strip()
    data['state'] = " ".join(state).strip()
    data['zip'] = zip
    return data

def get_data_txt(details):
    data = {}
    
    for index, line in enumerate(details):     
        if index == 0:
            data['name'] = line.strip()
        if index == 1:
            data['street'] = line.strip()
        if index == 2:
            # check if the line contains a comma, if not then the line is the county
            if ',' not in line:
                data['county'] = line.strip()
            else:
               data['county'] = ""
               data = get_address_fields(data, line)
        if index == 3:
            data = get_address_fields(data, line)

    # remove any fields that are None, or ""
    data = remove_empty_fields(data)
    return data

def remove_empty_fields(data):
    return {k: v for k, v in data.items() if v is not None and v != ""}

def split_zip_xml(zip):
    zip_list = []
    zip = zip.split('-')
    for z in zip:
        if z.strip() == "":
            continue
        zip_list.append(z.strip())
    return zip_list

def parse_xml(file):
    json_output = []
    data = {}
    tree = ET.parse(file)
    root = tree.getroot()

    try:
        # Iterate over each 'entity' element
        for entity in root.findall('ENTITY'):
            # Iterate over each 'ent' element
            for ent in entity.findall('ENT'):
                name = ent.find('NAME').text.strip()
                company = ent.find('COMPANY').text.strip()
                street = ent.find('STREET').text.strip()
                city = ent.find('CITY').text.strip()
                country = ent.find('COUNTRY').text.strip()
                state = ent.find('STATE').text.strip()
                zip = ent.find('POSTAL_CODE').text.strip()

                new_zip = split_zip_xml(zip)
                
                # determine if name or organization should be used
                if name ==  None or name == "":
                    data["organization"] = company
                else:
                    data["name"] = name
                
                # add the data to the dictionary
                data = {
                    **data,
                    "street": street,
                    "city": city,
                    "country": country, 
                    "state": state,
                    "zip":  get_zip(new_zip),    
                }
                
                # remove any fields that are None, or ""
                data = remove_empty_fields(data)
                # add the data to the final_json list
                json_output.append(data)
                # reset the data dictionary
                data = {}
    except Exception as e:
        raise RuntimeError(f"Error parsing XML file '{file}': {e}")   
    return json_output

def parse_tsv(file):
    json_output = []
    data = {}
    try:
        with open(file, 'r') as file:
            lines = file.readlines()
            for index,line in enumerate(lines):
                # Split the line into fields using tab ('\t') as the delimiter
                fields = line.split('\t')
                # skip the first line because it contains the headers
                if index == 0:
                    continue
                # removes new line character from the last field, making zip4 = "" rather than "\n"
                field_length = len(fields)
                fields[field_length-1] =  fields[field_length-1].strip("\n")
                
                first, middle, last = fields[0:3]
                organization = fields[3].strip()
                address = fields[4].strip()
                name = get_name(first,middle,last) if first else ""
                name = "" if name == None else name
                
                # # ASSUMING THAT ERRORS IN FILES ARE NOT INTENTIONAL
                # if (first == "" or first == None) and organization == "N/A":
                #     organization = fields[2]
                    
                # if fields[9] == "": then zip = fields[8], else zip = fields[8] + "-" + fields[9]
                zip = get_zip(fields[8:10]) if fields[9] != "" else fields[8]
                
                postal_code = zip if zip else "" 
                
                if name == "":
                    data["organization"] = organization.strip()
                else:
                    data["name"] = name.strip()
                data = {
                        ** data,
                        "street": address,
                        "city": fields[5],
                        "county": fields[7],
                        "state": fields[6],
                        "zip": postal_code
                    }
                
                # remove any fields that are None, or ""
                data = remove_empty_fields(data)
                json_output.append(data)
                data = {}
    except Exception as e:
        raise RuntimeError(f"Error parsing TSV file '{file}': {e}")
    return json_output

def parse_txt(file):
    json_output = []
    try:
        with open(file, 'r') as file:
            entries = []
            for line in file:
                line = line.strip()

                # if the line is not empty, add it to the entries list
                if line:
                    entries.append(line)

                # if the line is empty AND there are entries in the list
                elif entries:
                    entry_data = get_data_txt(entries[0:])
                    # reset the entries list and add the data to the final_json list
                    entries = []
                    json_output.append(entry_data)


            # if there are entries in the list after the loop ends
            if entries:
                person_data = get_data_txt(entries[0:])
                entries = []
                json_output.append(person_data)
    except Exception as e:
        raise RuntimeError(f"Error parsing TXT file '{file}': {e}")

    return json_output

def main():
    json_output = []
    json_total = []
    # check if there are any files attached to the command line
    if len(sys.argv)<2:
        print("There are no files attached to the command. Please attach files to the command.")
        sys.exit(1)
    
    # get the files attached to the command
    file_list = sys.argv[1:]

    
    # iterate over the files
    for index, file in enumerate(file_list):
        file = file.strip()
        _, file_type = file.split('.')
        try:
            if file_type == 'xml':
                json_output = parse_xml(file)
            elif file_type == 'tsv':
                json_output = parse_tsv(file)
            elif file_type == 'txt':
                json_output = parse_txt(file)
            else:
                # write to stderr
                print( f"Error: {file} is not a valid file type. Please use a valid file type (xml, tsv, txt)")  
                sys.stderr.write(f"Error: {file} is not a valid file type. Please use a valid file type (xml, tsv, txt)\n")   
                sys.exit(1)

        except Exception as e:
            # write to stderr
            sys.stderr.write( str(e) + '\n')
            # UNSURE IF THIS IS THE CORRECT WAY TO EXIT THE PROGRAM
            sys.exit(1)
            
        # only print if no errors were discovered
        if len(json_output) > 0:  
            # sort the JSON by zip
            json_output.sort(key = lambda x: x["zip"])
            # Beautify the JSON
            formatted_json = json.dumps(json_output, indent=4)
            # Print the beautified JSON
            json_total.append(formatted_json)
            
        # if no data was found in the file
        if len(json_output) == 0:
            sys.stderr.write("Error: No data was found in the file: " + file + "\n")
            sys.exit(1)
    
    # print items of json_total ONLY if there are no errors
    if len(json_total) == len(file_list):
        for item in json_total:
            print(item)
            

    # exit the program successfully
    sys.exit(0)
    
if __name__ == "__main__":
    main()
    
# test: see if entering incorrect files or no files will return an error
# python challenge.py input/input1.xml input/input2.tsv input/input3.txt input/input4.txt = error
# python challenge.py input/input4.txt input/input1.xml input/input2.tsv input/input3.txt = error
# python challenge.py = error
# python challenge.py input/input1.xml = success
# python challenge.py  input/input2.tsv = success
# python challenge.py  input/input3.txt = success
# python challenge.py input/input1.xml input/input2.tsv input/input3.txt = success