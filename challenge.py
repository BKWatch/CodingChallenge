import sys
import csv
import json
import argparse
import traceback
import urllib.request
from typing import Dict, List, Generator
import xml.etree.ElementTree as ET
class Entity:
    def __init__(self) -> None:
        self.states = self.state_api() 
        

    def state_api(self) -> Dict[str, str]:
        """Using a public api to load US state abbrv data"""
        url = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/georef-united-states-of-america-state/records?select=ste_name%2C%20ste_name%2C%20ste_stusps_code&limit=56"
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        return data


    def get_state(self, condition: str) -> str:
        """Return a full state name given a state abbrv"""
        if len(condition) == 2:
            #when supplied with a 2 length string if a match is found in the dict return full state name
            state = next((item['ste_name'][0] for item in self.states['results'] if item['ste_stusps_code'] == condition))
            return state
        else:
            return condition 



    def create_json(self, data: Generator | ET.Element, ext: str) -> Dict[str, str] | None:
        """Return a formatted dictionary given some data and extention type"""
        datadict = {}
        if ext == 'xml':
            for item in data:
                if item.text and len(item.text.strip()) > 0: #create a dictionary no empty vals
                    datadict[f"{item.tag.lower()}"] = item.text

            state = self.get_state(datadict['state'])
            if len(datadict['postal_code']) < 9: #cleaning postal codes to remove - if no zip4
                zip = datadict['postal_code'].replace('-','').strip()
            else:
                zip = datadict['postal_code'].replace(' ','')
            if 'name' in datadict:
                return {'name': datadict['name'], 'street': datadict['street'], 'city': datadict['city'], 'state': state, 'zip': zip}
            else:
                return {'organization': datadict['company'], 'street': datadict['street'], 'city': datadict['city'], 'state': state, 'zip': zip}


        if ext == 'tsv':
            keys = ['first', 'middle', 'last', 'organization', 'address', 'city', 'state', 'county', 'zip', 'zip4']
            for key in keys: #generate a dictionary with the data
                datadict[key] = next(data)
            
            #Analyzing the data, I've noticed the information is misplaced. Switching 'last' to 'org' and removing names if an org exists
            if datadict['first'].strip() == '' and len(datadict['last'].strip()) > 0:
                datadict['organization'] = datadict['last']
                datadict['last'] = ''

            elif datadict['first'].strip() == '' and len(datadict['organization'].strip()) > 0:
                datadict['first'], datadict['middle'], datadict['last'] = '', '', ''

            else:
                name = {'name': f"{datadict['first']} {datadict['middle']} {datadict['last']}"}
                datadict['first'], datadict['middle'], datadict['last'] = '', '', ''

            if len(datadict['zip4']) > 0: #combining zip and zip4
                datadict['zip'] = f"{datadict['zip']}-{datadict['zip4']}"
                datadict['zip4'] = ''

            datadict['state'] = self.get_state(datadict['state']) 
            datadict = { k:v for k, v in datadict.items() if len(v.strip()) > 0 } #return a new dictionary without empty values
            try:
                if name: #reorganizing the dictionary 
                    return {**name, **datadict}
            except UnboundLocalError:
                return datadict

    def get_json(self, filename: str) -> List:
        jsondata = []
        ext = filename[-3:]
        if ext == 'xml':
            xml = ET.parse(filename)
            root = xml.getroot()
            for entities in root.iter('ENTITY'):
                for entity in entities:
                    jsondata.append(self.create_json(entity, ext))

        if ext == 'tsv':
            with open (filename) as file:
                data = csv.reader(file, delimiter="\t")
                for idx, line in enumerate(data):
                    if idx == 0:
                        continue
                    line = (items.replace('N/M/N','').replace('N/A', '') for items in line)
                    jsondata.append(self.create_json(line, ext))
           

        if ext == 'txt':
            with open(filename) as file:
                data = file.read()
                for addresses in data.split('\n\n'):
                    addresses = [x.strip() for x in addresses.splitlines()] #list of messy address
                    location = [x.strip() for x in ''.join(addresses[-1:]).split(",")] #location messy with City, State, zip, and potentially zip4 
                    state_zip = [self.get_state(x) for x in ''.join(location[-1:]).rsplit(" ", 1)] #In state_zip we convert state code to long name and right split to seperate the state and zipcode. 
                    name_street = addresses[:-1] #name street includes name, street addr, and sometimes county
                    try:
                        if len(name_street) == 3:
                            a = {'name': name_street[0], 'street': name_street[1], 'county': name_street[2]}
                        else:
                            a = {'name': name_street[0], 'street': name_street[1]}
                        city = location[:1][0]
                        b = {'city': city }
                        c = {'state': state_zip[0], 'zip': state_zip[1].replace('-', '') if len(state_zip[1]) < 9 else state_zip[1]}
                        #now that all parts of the information is properly seperated and formatted we join them together in order 
                        #a 'name', 'street', 'county'
                        #b 'city'
                        #c 'state', 'zip'
                        jsondata.append({**a, **b, **c})
                    except IndexError:
                        pass
     
        return jsondata

    def main(self, files: List):
        dataset = []
        try:
            for filename in files:
                if filename[-3:] not in ['txt', 'tsv', 'xml']:
                    raise NameError("one or more filenames you provided does not match the accepted extension")
                dataset.extend(self.get_json(filename))
            print(json.dumps(sorted(dataset, key=lambda k: k['zip']), indent=4))
            return 0
        except Exception:
            traceback.print_exc(file=sys.stderr)
            if args.files is None:
                print("Did you provide any arguments? check --help for more information", file=sys.stderr)
            return 1
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='BKWatch Coding Challenge',
                    description='Accepts a list of files and returns the data back in formated json',
                    epilog='Please use the correct arguments',
                    add_help=False)
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                    help='Double check input files to make sure they are the correct formats')
    parser.add_argument('--files', nargs="+", help="python challenge.py --files <pathToFile> <OptionalPathToFile>")
    args = parser.parse_args()
    entity = Entity()
    entity.main(args.files)
