#!/usr/bin/env python3
import argparse
import subprocess
import csv
import json, jsonschema
from pathlib import Path
import xml.etree.ElementTree as ET

class Data:
    """
    The Data class represents a data object that stores information about data
    read from various files.

    Attributes:
        dir (list): A list of directories.
        files (list): A list of files.
        data (list): raw data in json-like format.
        schema (dict): A dictionary containing the JSON schema.

    Methods:
        parse_xml(file: str): Parses an XML file and extracts data to create a JSON object.
        parse_txt(file: str): Parses a TXT file and extracts data to create a JSON object.
        parse_tsv(file: str): Parses a TXT file and extracts data to create a JSON object.
        process_data(): Processes the data and creates a JSON object.
        validate_json(): Validates the data against the JSON schema.
        verify_file_type(file: str, fileType: str): Verifies the file type.
        populate_files(): extracts files from the directories provided.
        add_data_to_json(): adds data to the JSON object.
        add_directory(dir: str): adds a directory to the list of directories.
        add_file(file: str): adds a file to the list of files.
    """
    # def __init__(self, name: list, street: str, city: str, county: str, state: str, zipcode: str):
    def __init__(self) -> None:
        self.directory = []
        self.files = []
        self.data = []

        self.schema: dict = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "minLength": 1
                },
                "organization": {
                    "type": "string"
                },
                "address": {
                    "type": "string"
                },
                "city": {
                    "type": "string"
                },
                "county": {
                    "type": "string"
                },
                "state": {
                    "type": "string"
                },
                "zip": {
                    "type": "string"
                },
            },
            "required": ["street", "city", "state", "zip"]
        }

    def parse_xml(self, file: str) -> bool:
        """
        Parses an XML file and extracts data to create a JSON object.
        
        Parameters:
            file (str): The path to the XML file to be parsed.
        
        Returns:
            bool: True if the file was parsed successfully, False otherwise.
        """

        print(f"Parsing XML file: {file}")

        # parse xml file
        try:
            tree = ET.parse(file)
        except ET.ParseError as e:
            print(f"Error parsing XML file: {e}")
            return False

        root = tree.getroot()
        # Extract data from XML and store it in a list of dictionaries
        xml_data: list = []

        # Extract data from XML and store it in json format
        for ent in root.findall('.//ENT'):
            ent_data: dict = {}
            for child in ent:
                ent_data[child.tag] = child.text.strip()
            xml_data.append(ent_data)

        # normalize XML data
        for d in xml_data:
            data: dict = {
                "name": str,
                "organization": str,
                "street": str,
                "city": str,
                "state": str,
                "zip": str,
            }
            data['name'] = d['NAME']
            data['organization'] = d['COMPANY']
            data['city'] = d['CITY']
            data['state'] = d['STATE']

            # combine street address into one field
            data['street'] = d['STREET'] + ' ' + d['STREET_2'] + ' ' + d['STREET_3']
            data['street'] = data['street'].rstrip(" ")

            # combine postal code into one field if needed
            data['zip'] = d['POSTAL_CODE'].replace(' - ', '-').rstrip(' -')

            # remove empty fields
            keys_to_remove = []
            for key, value in data.items():
                if value == "":
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                data.pop(key)            # print(f'Data: {data}')

            self.add_data_to_json(data)

        return True


    def parse_tsv(self, file: str) -> bool:
        """
        Parses a TSV (Tab-Separated Values) file and extracts data to create a JSON object.

        Parameters:
            file (str): The path to the TSV file to be parsed.

        Returns:
            None
        """
        print(f"Parsing TSV file: {file}")

        try:
            with open(file, mode ='r', encoding='utf-8') as f:    
                csv_file = csv.DictReader(f , delimiter='\t')

                for line in csv_file:
                    data: dict = {
                        "name": str,
                        "organization": str,
                        "street": str,
                        "city": str,
                        "state": str,
                        "zip": str,
                    }

                    #  check if there's a name, or an organization
                    if line["first"] == "":
                        data['name'] = ''
                        data['organization'] = line['organization']
                    # check if there's a middle name
                    elif line['middle'] == "N/M/N":
                        data['name'] = line['first'] + " " + line['last']
                        data['organization'] = ''
                    else:
                        data['name'] = line['first'] + " " + line['middle'] + " " + line['last']
                        data['organization'] = ''

                    data['street'] = line['address']
                    data['city'] = line['city']
                    data['state'] = line['state']

                    # check if there's a full zip, or short zip
                    if line['zip4'] == "":
                        data['zip'] = line['zip']
                    else:
                        data['zip'] = line['zip'] + "-" + line['zip4']

                    # remove empty keys
                    keys_to_remove = []
                    for key, value in data.items():
                        if value == "":
                            keys_to_remove.append(key)

                    for key in keys_to_remove:
                        data.pop(key)

                    self.add_data_to_json(data)
        except FileNotFoundError as e:
            print(f"Cannot open TSV file: {e}")
            return False
        except csv.Error as e:
            print(f"Error reading TSV file: {e}")
            return False
        return True


    def parse_txt(self, file: str):
        """
        Parses a TXT file and extracts data to create a JSON object.

        Parameters:
            file (str): The path to the TXT file to be parsed.

        Returns:
            None
        """
        print(f"Parsing TXT file: {file}")

        # define fields to load into df
        names: list = []
        # organizations: list = []
        streets: list = []
        counties: list = []
        cities: list = []
        states: list = []
        postal_codes: list = []

        # read txt file
        with open(file, 'r', encoding='utf-8') as file:
            lines: list = file.readlines()

        #  parse each record
        current_record: list = []

        for line in lines:
            # Remove leading/trailing whitespaces
            line = line.strip()
            # If the line is not empty
            if line:
                current_record.append(line)
            # If the line is empty, it's the end of the current record
            else:
                #  if record has 3 lines, no county is provided
                if len(current_record) == 3 and current_record:

                    names.append(current_record[0])
                    streets.append(current_record[1])
                    counties.append('')
                    city_state_zip = current_record[2].rsplit(',', 1)  # Split city and state/ZIP
                    cities.append(city_state_zip[0].strip())
                    state_zip = city_state_zip[1].rsplit(' ', 1)  # Split state and ZIP
                    states.append(state_zip[0].strip())
                    if len(state_zip[1]) == 6:
                        # Remove trailing hyphen from ZIP
                        postal_codes.append(state_zip[1].strip('-'))
                    else: 
                        postal_codes.append(state_zip[1])

                    current_record = []
                # if record has 4 lines, county is provided
                elif len(current_record) == 4 and current_record:
                    names.append(current_record[0])
                    streets.append(current_record[1])
                    counties.append(current_record[2])
                    city_state_zip = current_record[3].rsplit(',', 1)  # Split city and state/ZIP
                    cities.append(city_state_zip[0].strip())
                    state_zip = city_state_zip[1].rsplit(' ', 1)  # Split state and ZIP
                    states.append(state_zip[0].strip())
                    postal_codes.append(state_zip[1])  # Remove trailing hyphen from ZIP
                    current_record = []

            for i, name in enumerate(names):
                if counties[i] == "":
                    self.add_data_to_json({
                        "name": name,
                        "street": streets[i],
                        "city": cities[i],
                        "state": states[i],
                        "zip": postal_codes[i]
                    })
                else:
                    self.add_data_to_json({
                        "name": name,
                        "street": streets[i],
                        "city": cities[i],
                        "county": counties[i],
                        "state": states[i],
                        "zip": postal_codes[i]
                    })

    def process_files(self) -> None:
        """
        Processes a list of files and performs different actions based on their file extension.

        This function iterates over each file in the `self.files` list and checks its file 
        extension. The function then checks the file type to ensure it matches the expected
        file type and then calls the appropriate parsing function to extract data from the file.
        Parameters:
            self (object): The current instance of the class.

        Returns:
            None
        """
       
        for file in self.files:
            if file.endswith(".xml"):
                self.verify_file_type(file, "XML")
                self.parse_xml(file)
            elif file.endswith(".txt"):
                self.verify_file_type(file, "txt")
                self.parse_txt(file)
            elif file.endswith(".tsv"):
                self.verify_file_type(file, "TSV")
                self.parse_tsv(file)
        
    def verify_file_type(self, file: str, fileType: str) -> bool:
        """
        Verifies the type of the file by checking its extension against the specified fileType.
        
        Parameters:
            self (object): The current instance of the class.
            file (str): The path to the file to be verified.
            fileType (str): The expected file type to be verified.
        
        Returns:
            bool: True if the file type matches the expected type, False otherwise.
        """
        result = subprocess.run(["file", file], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        f_type = output.split(": ")[1]
        match fileType.upper():
            case "XML":
                if 'XML' not in f_type:
                    print("Error: File type is not XML")
                    exit(1)
                return True
            case "TXT":
                if f_type != 'ASCII text':
                    print("Error: File type is not ASCII")
                    exit(1)
                return True
            case "TSV":
                if f_type != 'ASCII text, with CRLF line terminators':
                    print("Error: File type is not TSV")
                    exit(1)
                return True
            case _:
                print("Error: Invalid file type")
                return False
        

    def add_data_to_json(self, newData: dict):
        """
        Adds validated data to the JSON object. If the new data passes validation,
        it is appended to the existing data. Otherwise, an error message is printed.
        
        Parameters:
            newData (dict): The new data to be added to the JSON object.
        
        Returns:
            None
        """
        if self.validate_json(newData):
            self.data.append(newData)
        else:
            print("Error: Invalid JSON data")
            

    def populate_files(self, directory: Path):
        """
        Populates the `files` list with all the files in the given directory.
        Parameters:
            directory (Path): The directory path from which to retrieve the files.
        Returns:
            None
        """

        # get all files in directory
        directory = Path(directory)
        for f in directory.glob('*'):
            f = str(f)
            # ensure no duplicate files
            if f not in self.files:
                self.files.append(f)

    def add_directory(self, directory: Path):
        """
        Add a directory to the objects `dir` list and populate its `files` list.
        Parameters:
            directory (Path): The directory path to add.
        Returns:
            None
        """
        # ensure no duplicate directories
        if directory not in self.directory:
            self.directory.append(directory)
            self.populate_files(directory)

    def validate_json(self, data):
        """
        Validates the given JSON data against the schema stored in the `schema` attribute of the object.
        Parameters:
            data (dict): The JSON data to be validated.
        Returns:
            bool: True if the JSON data is valid according to the schema, False otherwise.
        Raises:
            jsonschema.exceptions.ValidationError: If the JSON data is invalid according to the schema.
        Prints:
            str: An error message indicating that the JSON data is invalid and the specific validation error.
        """
        try:
            jsonschema.validate(data, self.schema)
            # print("JSON data is valid.") 
            return True
        except jsonschema.exceptions.ValidationError as e:
            print(f"Error: Invalid JSON data: {e}")
            return False

def main(args) -> None:
    """
    Executes the main function of the program.
    Parameters:
        args (argparse.Namespace): The command line arguments passed to the program.
    Returns:
        None
    """
    my_data = Data()
    for d in args.dirs[0]:
        my_data.add_directory(d)
    my_data.process_files()
    
    # Sort data by zipcode
    sorted_data = sorted(my_data.data, key=lambda x: x.get('zip', ''))

    # Convert sorted data to JSON
    j_data = json.dumps(sorted_data, indent=4)
    # print data as python object
    # print(f'Data: {my_data.data}')

    # print data as json object
    print(f"Data: \n{j_data}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d","--dirs",
                        required=True,
                        type=str,
                        action='append', 
                        nargs='+', 
                        help="Directory to parse - can provide multiple dirs")
    args = parser.parse_args()

    main(args)
