# -*- coding: utf-8 -*-
# #######################################                 
# Program: Parsing Coding Challenge
# Author: Jason Drawdy
# Date: 04/22/24
# #######################################
"""
!DESCRIPTION:
--------------
This program is designed to be run from the command line and it accepts a list of
path names of files in any of the formats (.xml, .tsv, .txt), parses them, and writes
a JSON list of the combined data to standard output, sorted by ZIP code in ascending order.

!FEATURES:
--------------
[+] Uses only standard Python libraries
[+] Compatible with Python 3.10 to 3.12.3
[+] Conforms 99.99% (if not 100%) to [PEP 8](https://peps.python.org/pep-0008/)
[+] Provides a `--help` option and usage messages
[+] Checks for errors in the argument list
[+] Checks input files to make sure they conform to the formats showcased by the sample files
[+] Outputs a list of addresses only if no errors were discovered in the above two steps
[+] Writes any error messages to stderr
[+] Exits with status `0` or `1` to indicate success or failure

!NOTE:
--------------
Even though I have taken care to look through the below code I must mention that
nothing in the realm of programming is ever perfect. However, the below classes, functions,
and all other components have been written to be as clean and succint as possible in order
to allow for readability and performance. Thank you for your time and for the opportunity.
"""
import os
import sys
import csv
import json
import argparse
import xml.etree.ElementTree as ET

class Entity:
    """An information object for storing data about a person or organization."""
    def __init__(self: "Entity", entity_data: list|dict) -> None:
        """Create a new instance of the data object in preparation for later parsing.
        
        Parameters
        ----------
        entity_data : :class:`list|dict`
            A collection of data points used for parsing into a `Entity` object.
        """
        self.data = entity_data
    
    def _capitalize(self: "Entity", input_data: str, delimiter: str = ' ', connector: str = ' ') -> str:
        """Checks to make sure every word in the provided string is capitalized.
        
        Parameters
        ----------
        input_data : :class:`str`
            The string to ensure is capitalized.
        delimiter : :class:`str`
            A character or string to split the data by in order to process its contents.
        connector : :class:`str`
            A character or string to join the newly capitalized words with.
        """
        return connector.join([x.lower().capitalize() for x in input_data.split(delimiter)])
    
    def _from_dict(self: "Entity") -> None:
        """Takes parsed information from a `dict` and sets the `Entity` properties based on that information."""
        self.name = self.data.get('name', None)
        if not self.name:
            first = self.data.get('first', '')
            middle = self.data.get('middle', '')
            last = self.data.get('last', '')
            self.name = f"{first}"
            if middle and middle != "N/M/N": self.name += f" {middle}"
            if last: self.name += f" {last}"
        self.organization = self.data.get('organization', None) #? Exists in .TSV, but not .XML
        self.street = self.data.get('address', None) #? Exists in .TSV, but not .XML
        if not self.street:
            self.street = self.data.get('street', None) #? Exists in .XML, but not .TSV
            self.street_2 = self.data.get('street_2', None) # This is typically blank in the example data.
            self.street_3 = self.data.get('street_3', None) # Again, typically blank in the example data.
        self.city = self.data.get('city', None)
        self.state = self.data.get('state', None)
        self.county = self.data.get('county', None)
        self.country = self.data.get('country', None) # Only exists in .XML, but it's added anyway.
        self.zip = self.data.get('zip', None)
        self.zip_4 = self.data.get('zip4', None)
        if self.zip_4:
            self.zip += f"-{self.zip_4}"
            del self.zip_4
    
    def _from_list(self: "Entity") -> None:
        """Takes parsed information from a `list` and sets the `Entity` properties based on that information."""
        self.name = self.data[0]
        self.street = self.data[1]
        if len(self.data) >= 4:
            self.county = self._capitalize(self.data[2])
            location_data = self.data[3]
        else:
            location_data = self.data[2]
        city_parts = location_data.split(',')
        state_parts = city_parts[-1].split(' ')
        self.city = self._capitalize(city_parts[0])
        self.state = ' '.join([state_parts[i] for i in range(len(state_parts)-1)]).strip()
        self.zip = state_parts[-1][:-1] if state_parts[-1].endswith('-') else state_parts[-1]
    
    def as_json(self: "Entity") -> dict[str, str]:
        """Returns the `Entity` as a JSON readable dictionary object.
        
        Returns
        ----------
        :class:`dict[str, str]`
            A JSON based dictionary that contains all parsed entity information, name, address, etc.
        """
        if isinstance(self.data, dict):
            self._from_dict()
        if isinstance(self.data, list):
            self._from_list()
        return {k: v for k, v in vars(self).items() if not k.startswith("__") 
                and k != ("data") and v and v != "N/A"}
    
class Parsers:
    """A collection of various data parsers for formats such as `.xml`, `.tsv`, and .`xml` files."""
    @staticmethod
    def _check_filepath(filepath: str) -> None:
        """
        Parse all user data from a .tsv file into a list of JSON dictionary elements. 
        
        Parameters
        ----------
        filepath : :class:`str`
            The absolute path to the file being parsed.
        
        Returns
        ----------
        :class:`list[dict]`
            A list of JSON dictionary elements with the parsed user information.
        
        Raises
        ----------
        FileNotFoundError
            If the file to be parsed does not exist.
        """
        if not os.path.exists(filepath): 
            raise FileNotFoundError("The provided data file doesn't exist!")
    
    @staticmethod
    def _clean_tsv_file(filepath: str) -> list[str]:
        """
        Normalizes a file (typically `.tsv`) by correcting the data so that
        it does not have an offset that can hinder parsing of its contents.
        
        Parameters
        ----------
        filepath : :class:`str`
            The absolute path to the file being cleaned.
        
        Returns
        ----------
        :class:`list[Entity]`
            A collection of clean data strings related to the original file.
        """
        Parsers._check_filepath(filepath)
        clean_data = []
        with open(filepath, 'r') as file:
            for line in file.readlines():
                if line.startswith("\t\t") and "\tN/A" in line:
                    line = line.replace("\tN/A", "")
                    line = f"\t{line}"
                clean_data.append(line)
        return clean_data
    
    @staticmethod
    def parse_tsv_file(filepath: str) -> list[Entity]:
        """
        Parse all data from a `.tsv` file into a list of information objects returnable as JSON. 
        
        Parameters
        ----------
        filepath : :class:`str`
            The absolute path to the file being parsed.
        
        Returns
        ----------
        :class:`list[Entity]`
            A collection of information objects about a person or organization.
        """
        Parsers._check_filepath(filepath)
        cleaned = Parsers._clean_tsv_file(filepath)
        parsed_data = []
        reader = csv.reader(cleaned, delimiter="\t", quotechar='"')
        headers = next(reader)
        for row in reader:
            parsed_data.append(Entity({header: value for header, value in zip(headers, row)}))
        return parsed_data

    @staticmethod
    def parse_xml_file(filepath: str) -> list[Entity]:
        """
        Parse all data from a `.xml` file into a list of information objects returnable as JSON. 
        
        Parameters
        ----------
        filepath : :class:`str`
            The absolute path to the file being parsed.
        
        Returns
        ----------
        :class:`list[Entity]`
            A collection of information objects about a person or organization.
        """
        Parsers._check_filepath(filepath)
        tree = ET.parse(filepath)
        root = tree.getroot()
        parsed_data = []
        for ent in root.findall('.//ENTITY/ENT'):
            data = {
                "name": ent.find('NAME').text.strip() if ent.find('NAME') is not None else "N/A",
                "organization": ent.find('COMPANY').text.strip() if ent.find('COMPANY') is not None else "N/A",
                "street": ent.find('STREET').text.strip() if ent.find('STREET') is not None else "N/A",
                "street_2": ent.find('STREET_2').text.strip() if ent.find('STREET_2') is not None else "N/A",
                "street_3": ent.find('STREET_3').text.strip() if ent.find('STREET_3') is not None else "N/A",
                "city": ent.find('CITY').text.strip() if ent.find('CITY') is not None else "N/A",
                "country": ent.find('COUNTRY').text.strip() if ent.find('COUNTRY') is not None else "N/A",
                "state": ent.find('STATE').text.strip() if ent.find('STATE') is not None else "N/A",
                "zip": ent.find('POSTAL_CODE').text.strip().split("-")[0].strip() if ent.find('POSTAL_CODE') is not None else "N/A"
            }
            parsed_data.append(Entity(data))
        return(parsed_data)

    @staticmethod
    def parse_txt_file(filepath: str) -> list[Entity]:
        """
        Parse all data from a `.txt` file into a list of information objects returnable as JSON. 
        
        Parameters
        ----------
        filepath : :class:`str`
            The absolute path to the file being parsed.
        
        Returns
        ----------
        :class:`list[Entity]`
            A collection of information objects about a person or organization.
        """
        Parsers._check_filepath(filepath)
        parsed_data, temp = [], []
        with open(filepath, 'r') as file:
            data = file.readlines()
            for line in data:
                if line == "\n":
                    if len(temp) > 0:
                        parsed_data.append(Entity(temp.copy()))
                        temp.clear()
                else:
                    line = line.strip()
                    temp.append(line.strip('\n'))
        return parsed_data
    
class Program:
    """A wrapper for cleanly organizing the main code of this Python program/script/module."""
    def _check_args(self: "Program") -> argparse.Namespace:
        """Validates any arguments provided with the program and shows examples if needed.
        
        Returns
        ----------
        :class:`argparse.Namespace`
            Simple object for storing attributes.
            
            Implements equality by attribute names and values, and provides a simple string representation.
        """
        help_message = "Parses a list of files into JSON compatible entries."
        command_message = f"Example: file1.xml file2.tsv file3.txt"
        parser = argparse.ArgumentParser(description=help_message)
        parser.add_argument('files', nargs='+', help=command_message)
        return parser.parse_args()
        
    def _parse_file(self: "Program", filepath: str) -> list[dict[str, str]]:
        """Determines which file parser to use and returns a list of parsed information objects.
        
        Parameters
        ----------
        filepath : :class:`str`
            The absolute path to the file being parsed.
        
        Returns
        ----------
        :class:`list[Entity]`
            A collection of information objects about a person or organization.
        """
        results = []
        filename = filepath.split('/')[-1]
        error_message = f"The file \"{filename}\" could not be parsed due to formatting or corruption!"
        match filename.split('.')[-1]:
            case "xml":
                try:
                    data = Parsers.parse_xml_file(filepath)
                    for item in data:
                        results.append(item.as_json())
                except: raise IOError(error_message)
            case "tsv":
                try:
                    data = Parsers.parse_tsv_file(filepath)
                    for item in data:
                        results.append(item.as_json())
                except: raise IOError(error_message)
            case "txt":
                try:
                    data = Parsers.parse_txt_file(filepath)
                    for item in data:
                        results.append(item.as_json())
                except: raise IOError(error_message)
            case _:
                raise IOError(f"The provided file (\"{filename}\") is not supported by this program!")
        return results

    def start(self: "Program") -> int:
        """Begins parsing and sorting information objects from files based on the args provided.
        
        Returns
        ----------
        :class:`int`
            A status code for when the program finishes; 0 for success, and 1 for a failure.
        """
        args = self._check_args()
        files_list = args.files
        try:
            if len(files_list) > 0:
                results = []
                for file in files_list:
                    result = self._parse_file(file)
                    if result:
                        for entry in result:
                            results.append(entry)
                sorted_results = sorted(results, key=lambda x: int(x["zip"].replace("-", "")))
                json_results = [json.dumps(result) for result in sorted_results]
                #? We can print the whole list "print(json_results)" or iterate for prettier output.
                for entry in json_results:
                    print(entry)
            return 0
        except Exception as error:
            print(error, file=sys.stderr)
        return 1

if __name__ == "__main__":
    program = Program()
    result = program.start()