""" 
#############################################################
# File:
#   $Id : challenge.py Tue Apr 30 15:56:40 CEST 2024
#   $Date : Tue Apr 30 15:56:40 CEST 2024
#   $Author : Befekadu Debebe Mengesha
#
# Purpose: A python script designed to parse  a list of
#           input files with different extention and return
#           a JSON enconded combined addresses to standared 
#            output
#
# Functions:
#    main : main function to run script
#   read_files : retrieve file paths and pass based on the file type
#           parse_input_xml : parse contact address from xml file 
#           parse_input_tsv : parse contact address from tsv file
#           parse_input_txt : parse and manuplate contact from text file
#           zip_format_utils : utility function to format zip code 
#           string_utils : utiliy function to retrieve contact detail from raw text line 
#   write_json : prints the combined contact lists to pretty-printed JSON serialized format 
# 
# Usage:
# python3 challenge.py "input1.xml" "input2.tsv" "input3.txt"
#
#############################################################
"""
import json
import sys
from os import path
import xml.etree.ElementTree as ET
from typing import List, Dict
import argparse

CONTACT_PROFILE: List[Dict] = list()

 
def string_utils(txt_lines :str) -> List[List[str]] :
    """script to retrieve and subdivide contact detail from raw
        text line
    Args:
        txt_lines (str): total txt line read from input file

    Returns:
        List[List[str]]: a list of contacts each a list of string
    """

    # list of contact address which equals to the number of empty line - 2
    tot_contact_list = list()
        
    # store each line till empty line is found   
    contact_list = list()
         
    for line in txt_lines:
            
        contact_list.append(line.strip())
        if line.strip() == "":
            tot_contact_list.append(contact_list)
            contact_list = list() 
            continue
    # remove the first 2 empty lines   
    return tot_contact_list[2:] 

def parse_input_xml(file_path :str, contacts : List[Dict]) -> None:
    """
    Parse xml contact addresses as dictionary  
    and append to the global contacts list

    Args:
        file_path (str):  input file string 
        contacts (List[Dict]): List of contacts from other inputs 
    
    """
    

    try :
        tree = ET.parse(file_path)
        
    except FileNotFoundError:
        sys.exit("xml FILE NOT FOUND !!!")
        
    root = tree.getroot()
    # Drop meta data
    entities = root[1]
    
    # traverse for each child contact
    for child in entities:
        
        contact = dict() # dictionary to store each contact address 
        
        # iterate to extract tag (key) and text (value) and store in contact dictionary 
        for i in range(len(child)):
            if child[i].text == ' ':
                continue
            elif child[i].tag == "COMPANY":
                
                contact["organization"] = child[i].text.strip()
                continue
            elif child[i].tag == "POSTAL_CODE" :
                    zip_code = child[i].text.strip()
                    if zip_code :
                        if len(zip_code) == 6:
                            zip_code = zip_code[:5]
                        contact["zip"] = zip_code
                    continue
            else:
                contact[(child[i].tag).lower()] = child[i].text.strip()
                
        # append each contact address to the global contacts list        
        contacts.append(contact)
        

def parse_input_tsv(file_path : str , contacts : List[Dict]) -> None:
    """
    Parse the input tabular  contact addresses to dictionary  
    and append to the global contacts list

    Args:
        file_path (str):  input file string 
        contacts (List[Dict]): List of contacts from other inputs 
        
    """
    
    # convert the input tabular file into data frame, exit if the file is not found 
    try :
        with open(file_path,'r') as file:
            reader = file.readlines()

    except FileNotFoundError:
        sys.stderr.write("txt FILE NOT FOUND !!!")
        sys.exit(1)
    
    # extract keys from the table head 
    key_contact =  reader[0].split("\t") 
    
    # extract list of contact details as value
    val_contact= reader[1:]
    val_contact_list = [val.split("\t") for val in val_contact]
    
    # convert to the list of dictionary each
    contact_dict = [{key_contact[i].strip(): val_contact_list[v][i].strip() for i in range(len(key_contact))} 
                    for v in range(len(val_contact_list))]
 
    for cont in range(len(contact_dict)):
        
        new_contact_dict = dict()
        contact = contact_dict[cont]
        
        full_name = "" # concatenate full name , start , middle and last keys to name 
        zip_val = ""
        for key , val in contact.items():
            
            if val == None :
                continue
            if val == "N/A" :
                continue
            if val == "":
                continue
                #print(val )
     
            if key.startswith("first") or key.startswith("middle") or key.startswith("last"):
                if "N/M/N" in str(val):
                    continue
                full_name += " " + str(val)
                new_contact_dict['name']= full_name

            if key.startswith("zip"):
                key = "zip"
                zip_val +=  val + "-"
                new_contact_dict[key] = zip_val[:-1]
            else:
                new_contact_dict[key] = val
                
                
        
        # add each contact to the list of contact         
        contacts.append(new_contact_dict)
        
def parse_input_txt(file_path : str , contacts : List[Dict]) -> None:
    """
    Parse and manuplate contact address from the input text 
    and combine to the global contacts list

    Args:
        file_path (str):  input file string 
        contacts (List[Dict]): List of contacts from other inputs 
        
    """
    
   
    try :
        with open(file_path,'r') as file:
            reader = file.readlines()

    except FileNotFoundError:
        sys.stderr.write("txt FILE NOT FOUND !!!")
        sys.exit(1)
        
    #     
    total_contact_list = string_utils(reader)   
    #contact_dict = dict()
    
    for contact in total_contact_list: 
        contact_dict = dict() #dictionary to store new contact list by key and value 
        if contact :
            for i in range(len(contact)):
                if i == 0:
                    if ("company" or "Ltd" )in contact[i]:
                        contact_dict["organization"] = contact[i]
                    else:
                        contact_dict["name"] = contact[i]
                elif i == 1:
                    contact_dict["street"] = contact[i]
                elif i > 1 and "country" in contact[i].lower():
                    contact_dict["country"] = contact[i]
                    
                elif i > 1 and "," in contact[i]:
                   
                    mini_address = contact[i].split(",")
                    contact_dict["city"] = mini_address[0]
                    states = mini_address[1].split(" ")
                    states.pop(0)
                    contact_dict["state"] = states[0]
                    zip_code = states[-1]
                
                    zip = zip_code
                   
                    if not zip:
                        continue
                    if len(zip) == 6:
                        zip = zip_code[:5]
                
                        
                    contact_dict["zip"] = zip
                       
        contacts.append(contact_dict)

def read_files(directory:str, files_name: List[str],contacts : List[Dict]) -> None:
    """read_files function parse and  filter file paths 
        to the dedicated parser functions

    Args:
        directory (str):  parent directory of the input files
        files_name (List[str]): list of input file 
        contacts (List[Dict]): list of dictionary of adresses per contact
        
    """
    
    # Extract the absolute path with the main file
    abs_file_path = path.abspath(__file__)
    
    # Extract base directory from the absolute path file 
    base_directory = path.dirname(abs_file_path)
   
   # traverse  and parse  each input files 
    for f in files_name:
        
        full_path = path.join(directory,f)
        # join the base directory and the file path
        
        file_path = path.join(base_directory, full_path)
          
 
        if f.endswith(".xml"):
                parse_input_xml(file_path,contacts)
                
                
        elif f.endswith("tsv"):
                parse_input_tsv(full_path,contacts)
                        
        elif ".txt" in f:
                
            parse_input_txt(full_path,contacts)
                
        else:
                return {}

def write_json(contacts : List[Dict]) ->None:
    """prints the combined contact lists to pretty-printed JSON serialized format 
    """
    # sort the combined contacts by zip in ascending 
    sorted_data = sorted(contacts, key=lambda x: x['zip'])
    print(json.dumps(sorted_data,indent=4))

   
    
def main():
    
    directory: str = "input"
    parser = argparse.ArgumentParser(description= "command usage ",add_help = True)
    parser.add_argument('input1.xml',nargs='?', help='input xml file')
    parser.add_argument('input2.tsv',nargs='?', help='tabular separate input file ')
    parser.add_argument('input3.txt',nargs='?', help='text ')
    
    args: List[Dict] = parser.parse_args()
    
    input_arguments: List[str] = sys.argv[1:]
    
    if len(input_arguments) < 3:
        sys.stderr.write("Input argument missed, Please check --help")
        sys.exit(1)
        
          
    read_files(directory, input_arguments,CONTACT_PROFILE)

    write_json(CONTACT_PROFILE)
    

    
if __name__=="__main__":
    main()