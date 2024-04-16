import sys
import xml.etree.ElementTree as E
import json

def parseTSV(file):
    addressesList = [] 
    tsv_file = open(file, 'r') 
    a = tsv_file.readline() 
        
    titles = [t.strip() for t in a.split('\t')] 
    for line in tsv_file: 
        addresses = {} 
        addresses['name'] = ""
        for t, f in zip(titles, line.split('\t')): 
            if t == "first":
                if f.strip() :
                    addresses['name'] = f.strip()
            if t == "middle":
                if addresses['name'] and f.strip() :
                    addresses['name'] = addresses['name'] + " " + f.strip() 
                elif f.strip():
                    addresses['name'] = f.strip()
            if t == "last":
                if addresses['name'] and f.strip() :
                    addresses['name'] = addresses['name'] + " " + f.strip() 
                elif f.strip():
                    addresses['name'] = f.strip()
            if t == "organization":
                if f.strip() != "N/A":
                    addresses['company'] = f.strip()
            if t == "address":
                if f.strip():
                    addresses['street'] = f.strip()
            if t == "city":
                if f.strip():
                    addresses['city'] = f.strip()
            if t == "state":
                if f.strip():
                    addresses['state'] = f.strip()
            if t == "county":
                if f.strip():
                    addresses['county'] = f.strip()
            if t == "zip":
                if f.strip() :
                    addresses['zip'] = f.strip() 
            if t == "zip4":
                if f.strip() :
                    addresses['zip'] = addresses['zip'] + " - " + f.strip() 

        #remove the default name key from the dictionary if empty
        if not addresses['name']:
            addresses.pop('name')  
        addressesList.append(addresses) 
    
    #sort addressess by zipcode
    sortedJson = sorted(addressesList, key=lambda x:x['zip'])
    print(json.dumps(sortedJson, indent=4))

def parseTXT(file):
    with open(file) as f:
        lines = f.readlines()
        record = {}
        output = []

        i = 0
        for line in lines:
            line = line.strip()
            if line:
                record[i] = line
                i = i + 1
            else:
                if len(record) > 1:
                    addresses = {}
                    addresses['name'] = record[0]
                    addresses['street'] = record[1]
                    if len(record) == 4:
                        addresses['county'] = record[2]
                        citycountryzip = record[3].split(',')
                        addresses['city'] = citycountryzip[0]
                        countryzip = citycountryzip[1].split(' ')
                        addresses['country'] = countryzip[1]
                        addresses['zip'] = countryzip[2]
                    else:
                        citycountryzip = record[2].split(',')
                        addresses['city'] = citycountryzip[0]
                        countryzip = citycountryzip[1].split(' ')
                        addresses['country'] = countryzip[1]
                        addresses['zip'] = countryzip[2]
                    
                    record = {}
                    i = 0
                    output.append(addresses)

    #sort addressess by zipcode
    sortedJson = sorted(output, key=lambda x:x['zip'])
    print(json.dumps(sortedJson, indent=4))

def parserXML(file):
    inputTree = E.parse(file)
    root = inputTree.getroot()
    jsonOutput = []

    for child in root:
       for child2 in child:
            if child2.tag == 'ENT':
                addresses = {}
                for child3 in child2:
                    if child3 not in addresses:
                        jsonKey = ""
                        if not child3.text.isspace():
                            if child3.tag.lower() == "company":
                                jsonKey = "organization" 
                            elif child3.tag.lower() == "postal_code":
                                jsonKey = "zip"
                            else:
                                jsonKey = child3.tag.lower()
                            addresses[jsonKey] = child3.text
                jsonOutput.append(addresses)

    #sort addressess by zipcode
    sortedJson = sorted(jsonOutput, key=lambda x:x['zip'])
    print(json.dumps(sortedJson, indent=4))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('No files passed', file=sys.stderr)
        exit(1)
    else:
        files = sys.argv
        for f in files[1:]:
            if f.endswith('.xml'):
                parserXML(f)
            elif f.endswith('.tsv'):
                parseTSV(f)
            elif f.endswith('.txt'):
                parseTXT(f)
            elif f == '--help':
                print('This program parses .tsv, .txt or .xml files and outputs them in JSON format')
            else:
                print('File path does not match .tsv, .txt or .xml', file=sys.stderr)
                exit(1)
        exit(0)