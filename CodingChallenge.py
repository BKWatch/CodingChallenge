import xml.etree.ElementTree as ET 
import re
import sys
from pathlib import Path
import json


class parserChallenge:
    """Class to parse the text, tsv, and xml files.
    Attributes: See each function documentation
    Example:
    terminal input: "python challenge.py Data/input1.xml  Data/input2.tsv Data/input3.txt"
    expected output:
                    [
                    {
                        "name": "David Scherrep",
                        "address": "12014 Cobblewood Lane North",
                        "city": "Jacksonville",
                        "state": "Florida",
                        "zip": "32225"
                    },
                    {
                        "name": "Sonji S Dixon-McCoy",
                        "address": "1222 East 146th Street",
                        "city": "Dolton",
                        "county": null,
                        "state": "Illinois",
                        "zip": "60419"
                    }, ..............
                    
    """
    def __init__(self):
            self.text_file_paths: list = []
            self.tsv_file_paths: list = []
            self.xml_file_paths: list = []
            self.error_list: list = []
            self.results: list = []

    def get_file_paths(self, filepaths):
        """Function to get the file paths of the given file type. The file type can be text, tsv, or xml.
        Args:
            file_paths (list): List of file paths.
            **kwargs (dict): Keyword arguments.
        """
        try:
            for file_path in filepaths:
                if file_path.endswith('.xml'):
                    self.xml_file_paths.append(file_path)
                elif file_path.endswith('.tsv'):
                    self.tsv_file_paths.append(file_path)
                elif file_path.endswith('.txt'):
                    self.text_file_paths.append(file_path)
            print("File paths separated")
        except Exception as e:
            print(f'Failed with the follow error {e}', file=sys.stderr)
            

    def load_files(self, filepath)->list[str]:
        """Helper function to load the given file paths.
        Args:
            file_paths (list): List of file paths.
        Returns:
            Lists of data.
        """
        with open(filepath, 'r') as f:
            return f.read()
              
    def parse_txt(self)-> None:
        """Function to parse the text files."""
        for filep in self.text_file_paths:
            file = self.load_files(Path(filep))
            lines = file.split('\n\n')

            for i in range(len(lines)):
 
                try:
                    if not lines[i]:
                        pass
                    elif len(lines[i].split('\n'))==3:
                        name, address, remaining = lines[i].split('\n')
                        city, remaining = remaining.split(',')
                        remaining = re.findall(r"([a-zA-Z]+|[a-zA-Z]+\s[a-zA-Z]|[0-9]+-[0-9]+|[0-9]+)", remaining)
                        state = remaining[0]
                        zip = remaining[1]
                        cur_info_dict = {}
                        cur_info_dict['name'] = name.strip() if name else None
                        cur_info_dict['address'] = address.strip() if address else None
                        cur_info_dict['city'] = city.strip() if city else None
                        cur_info_dict['county'] = county.strip() if county else None
                        cur_info_dict['state'] = state.strip() if state else None
                        cur_info_dict['zip'] = zip.strip() if zip else None
                        county = None
                        self.results.append(cur_info_dict)    
                    elif len(lines[i].split('\n'))==4:
                        name, address, county, remaining = lines[i].split('\n')
                        city, remaining = remaining.split(',')
                        remaining = re.findall(r"([a-zA-Z]+|[a-zA-Z]+\s[a-zA-Z]|[0-9]+-[0-9]+|[0-9]+)", remaining)
                        state = remaining[0] 
                        zip = remaining[1]
                        cur_info_dict = {}
                        cur_info_dict['name'] = name.strip() if name else None
                        cur_info_dict['address'] = address.strip() if address else None
                        cur_info_dict['city'] = city.strip() if city else None
                        cur_info_dict['state'] = state.strip() if state else None
                        cur_info_dict['zip'] = zip.strip() if zip else None
                        county = None
                        self.results.append(cur_info_dict)
                except Exception as e:
                    self.error_list.append(lines[i])
                    print(f'Failed with the follow error {e}', file=sys.stderr)
                

    def parse_tsv(self)-> None:
        """Function to parse the tsv files."""
        for file in self.tsv_file_paths:
            with open(file, 'r') as f:
                next(f)
                for line in f:
                    try:
                        cur_file = f.readline()
                        lines = cur_file.split('\t')
                        if not lines[0]:
                            while not lines[0]:
                                lines.pop(0)
                            organization = lines[0]
                            street = lines[2]
                            city = lines[3]
                            state = lines[4]
                            zip = lines[5] if not lines[6] else lines[5] + '-' + lines[6]

                            def create_current_org_dict(organization=None, street=None, city=None, state=None, zip=None)-> dict:
                                """Helper function to create dictionaries with the above information. - Organizations"""
                                cur_info_dict = {}
                                cur_info_dict['organization'] = organization.strip() if organization else None
                                cur_info_dict['street'] = street.strip() if street else None
                                cur_info_dict['city'] = city.strip() if city else None
                                cur_info_dict['state'] = state.strip() if state else None
                                cur_info_dict['zip'] = zip.strip("\n").strip("-") if zip else None
                                return cur_info_dict

                            self.results.append(create_current_org_dict(organization, street, city, state, zip))

                        else:
                            name = (lines[0] +" " + lines[2])
                            street = lines[4]
                            city = lines[5]
                            state = lines[6]
                            county = lines[7]
                            zip = lines[8].strip("\n") if not lines[9] else (lines[8] +"-" + lines[9].strip('\n'))

                            def create_current_name_dict(name=None, street=None, county=None, city=None, state=None, zip=None)-> dict:
                                """Helper function that creates a dictionary with the above information. - Indiviudual Names"""
                                cur_info_dict = {}
                                cur_info_dict['name'] = name.strip() if name else None
                                cur_info_dict['street'] = street.strip() if street else None
                                cur_info_dict['city'] = city.strip() if city else None
                                cur_info_dict['county'] = county.strip() if county else None
                                cur_info_dict['state'] = state.strip() if state else None
                                cur_info_dict['zip'] = zip.strip("-") if zip else None
                                return cur_info_dict

                            self.results.append(create_current_name_dict(name, street, county, city, state, zip))

                    except Exception as e:
                        self.error_list.append(lines)
                        print(f'Failed with the follow error {e}', file=sys.stderr)
    
    def parse_xml_file(self):
        """Function to parse the XML file."""
        for file in self.xml_file_paths:
            tree = ET.parse(file)
            root = tree.getroot()
            try:
                for i in range(len(root[1])):
                    if root[1][i].find('NAME').text != " ": 
                        name = (root[1][i].find('NAME').text)
                        street = (root[1][i].find('STREET').text)
                        city = (root[1][i].find('CITY').text)
                        state = (root[1][i].find('STATE').text)
                        zip = (root[1][i].find('POSTAL_CODE').text.strip().strip('-').strip())

                        def create_current_name_dict(name=None, street=None, county=None, city=None, state=None, zip=None)-> dict:
                            """Helper function that creates a dictionary with the above information. - Indiviudual Names"""
                            cur_info_dict = {}
                            cur_info_dict['name'] = name.strip() if name else None
                            cur_info_dict['street'] = street.strip() if street else None
                            cur_info_dict['city'] = city.strip() if city else None
                            cur_info_dict['county'] = county.strip() if county else None
                            cur_info_dict['state'] = state.strip() if state else None
                            cur_info_dict['zip'] = zip.strip("-") if zip else None
                            return cur_info_dict
                        
                        self.results.append(create_current_name_dict(name=name, street=street, city=city, state=state, zip=zip))

                    else:
                        organization = (root[1][i].find('COMPANY').text)
                        street = (root[1][i].find('STREET').text)
                        city = (root[1][i].find('CITY').text)
                        state = (root[1][i].find('STATE').text)
                        zip = (root[1][i].find('POSTAL_CODE').text.strip().strip('-').strip())

                        def create_current_org_dict(organization=None, street=None, city=None, state=None, zip=None)-> dict:
                            """Helper function to create dictionaries with the above information. - Organizations"""
                            cur_info_dict = {}
                            cur_info_dict['organization'] = organization.strip() if organization else None
                            cur_info_dict['street'] = street.strip() if street else None
                            cur_info_dict['city'] = city.strip() if city else None
                            cur_info_dict['state'] = state.strip() if state else None
                            cur_info_dict['zip'] = zip.strip("\n").strip("-") if zip else None
                            return cur_info_dict

                        self.results.append(create_current_org_dict(organization=organization, street=street, city=city, state=state, zip=zip))

            except Exception as e:
                self.error_list.append(root[1][i])
                print(f'Failed with the follow error {e}', file=sys.stderr)
                
    def main(self)->list[dict]:
        """Class manager function."""
        filepaths = sys.argv[1:]
 
        self.get_file_paths(filepaths)
        try:
            self.parse_txt()
            print("Text files parsed")
            self.parse_tsv()
            print("TSV files parsed")
            self.parse_xml_file()
            parsed = json.dumps(self.results, indent=4)
            print(parsed)
            exit(0)
        except Exception as e:
            print(f'Failed with the follow error {e}', file=sys.stderr)
            exit(1)
            
if __name__ == "__main__":
    parser = parserChallenge()
    parser.main()
