import sys
import os
import json
from collections import OrderedDict
import xml.etree.ElementTree as ET


def convertXmlToJson(data):
    # This function takes the XML content as input and converts it into JSON format.
    
    rootdata = ET.fromstring(data)
    info = []
    for entity in rootdata.findall('.//ENTITY/ENT'):
        presentaddress = {}
        for element in entity:
            # Parse the individual tags of the XML elements and create corresponding properties for the present address.
            if element.text.strip():
                if element.tag == 'NAME':
                    presentaddress['name'] = element.text.strip()
                elif element.tag == 'COMPANY':
                    presentaddress['organization'] = element.text.strip()
                elif element.tag == 'STREET':
                    presentaddress['street'] = element.text.strip()
                elif element.tag == 'CITY':
                    presentaddress['city'] = element.text.strip()
                elif element.tag == 'STATE':
                    presentaddress['state'] = element.text.strip()
                elif element.tag == 'POSTAL_CODE':
                    presentaddress['zip'] = element.text.strip()
                    if (presentaddress['zip'][-1]=='-'):
                        presentaddress['zip'] = presentaddress['zip'][:-1]
                    if (presentaddress['zip'][-1]==' '):
                        presentaddress['zip'] = presentaddress['zip'][:-1]
        info.append(presentaddress)
    return info
            

def convertTextToJson(data):
    # This function takes the text content as input and converts it into JSON format.
    
    info = []
    presentaddress = {}
    count = 1
    for entry in data:
        entry = entry.strip()
        if len(entry)!=0:
            
            if count == 1:
                presentaddress['name'] = entry
            if count == 2:
                presentaddress['street'] = entry
            if count == 3:
                #Verify the county information.
                if(entry[-6:] == "COUNTY"):
                    county = entry.split()
                    presentaddress['county'] = county[0]
                else:
                    count += 1
            if count ==4:
                # #Verify the information related to city,state and zip.
                
                city,state = entry.split(',')
                presentaddress['city'] = city
                state = state[1:]
                sinfo = state.split(' ')
                pin = sinfo[-1]
                state = ' '.join(sinfo[x] for x in range(len(sinfo)-1))
                presentaddress['state'] = state
                if pin[-1]=='-':
                    pin = pin[:-1]
                presentaddress['zip'] = pin
            count += 1
        else:
            if presentaddress:
                info.append(presentaddress)
                presentaddress = {}
            count = 1
    if presentaddress:
        info.append(presentaddress)
    return info
                
def convertTsvToJson(data):
    # This function takes the Tsv content as input and converts it into JSON format.
    
    info = []
    headers = ["first","middle","last","organization","address","city","state","county","zip","zip4"]
    for entry in data:
        if entry[:5] == "first":
            continue
        fields = entry.split('\t')
        presentaddress = {}
        for idx,field in enumerate(fields):
            presentaddress[headers[idx]] = field.strip()
        # remove N/A fields and empty fields.
        presentaddress = {a:b for a,b in presentaddress.items() if b and b!= 'N/A'}
        # check for no middle name.
        if 'middle' in presentaddress and presentaddress['middle'] == 'N/M/N':
            del presentaddress['middle']
        #check for organisation.
        if 'first' not in presentaddress and 'last' in presentaddress:
            presentaddress['organization'] = presentaddress['last']
            presentaddress = reorganizeDict(presentaddress,'organization')
            del presentaddress['last']
        #check for zip4 and zip.
        if 'zip4' in presentaddress:
            presentaddress['zip'] += ('-'+presentaddress['zip4'])
            del presentaddress['zip4']
        # merge first,middle and last names.
        if 'first' in presentaddress and 'last' in presentaddress:
            if 'middle' in presentaddress:
                name = presentaddress['first'] +" "+presentaddress['middle']+" "+presentaddress['last']
            else:
                name = presentaddress['first'] +" "+presentaddress['last']
            presentaddress['name'] = name
            presentaddress = reorganizeDict(presentaddress,'name')
            del presentaddress['first']
            del presentaddress['last']
            if 'middle' in presentaddress:
                presentaddress['middle']
        info.append(presentaddress)
    return info

def reorganizeDict(dictionary,key):
    # function to reorganize the dictionary based on key provided.
    ordered_dict = OrderedDict([(key, dictionary[key])])
    for k,value in dictionary.items():
        if k!= key:
            ordered_dict[k] = value
    return ordered_dict

    
if __name__ == "__main__": 
    
    # This function takes the input of text files to be converted , checks the corresponding extesnion and converts the file into JSON format.
    if sys.argv[-1] == "--help":
        print("This challenge converts the content of txt,xml and tsv files into json format using file: challenge.py. Please provide the file names to be converted as input and the output is displayed after execution.")
        sys.exit(0)
    if len(sys.argv) < 2:
        print("Error: Files are not provided")
        sys.exit(1)
    res = []
    for file_path in sys.argv[1:]:
        if not os.path.isfile(file_path):
            print("File not Found")
            sys.exit(1)
        file_name,file_extension = os.path.splitext(file_path)
        print(file_name,file_extension)
        
        with open(file_path, "r") as f:
            data = f.readlines()
        if file_extension == ".xml":
            print("converting xml file")
            res.extend(convertXmlToJson(''.join(data)))
        elif file_extension == ".txt":
            res.extend(convertTextToJson(data))
        elif file_extension == ".tsv":
            res.extend(convertTsvToJson(data))
        else:
            print("File extension not supported")
            sys.exit(1)
        res.sort(key=lambda x: x['zip'][:5])
        print(json.dumps(res,indent=4))
