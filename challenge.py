# Name : Mohil Devan Khimani
# Email : mkhimani@asu.edu

import sys
import pandas as pd
import xml.etree.ElementTree as ET
import re
import json

def parse_xml(file_path):
    """
    Parse an XML file containing address data and convert it into a pandas DataFrame.

    Args:
    - file_path (str): The path to the XML file.

    Returns:
    - pd.DataFrame: A DataFrame containing the parsed address data.
    """
    # Parse the XML file
    xml_tree = ET.parse(file_path)
    xml_root = xml_tree.getroot()
    
    # Initialize a list to store entity data
    entity_data = []
    
    # Iterate over each 'ENT' element in the XML tree
    for ent in xml_root.findall("ENTITY/ENT"):
        # Create a dictionary to store data for the current entity
        entity_dict = {}
        # Iterate over each child element of the current entity
        for child in ent:
            # Add the tag and text of the child element to the entity dictionary
            entity_dict[child.tag] = child.text
        # Append the entity dictionary to the list of entity data
        entity_data.append(entity_dict)
    
    # Create a DataFrame from the list of entity data
    df = pd.DataFrame(entity_data)
    
    return df



# Read

def read_txt(file_path):
    """
    Read a text file containing address data and convert it into a pandas DataFrame.

    Args:
    - txt_file_path (str): The path to the text file.

    Returns:
    - pd.DataFrame: A DataFrame containing the parsed address data.
    """
    # Read the text file
    with open(file_path, "r") as file:
        text = file.read()
    
    # Initialize a list to store data for each block in the text
    text_data = []

    # Define patterns for extracting address components from each block
    patterns = {
        "name": r"(.+)",
        "street": r"(\d+ .+)",
        "city": r"(.+),",
        "state_zip": r"([A-Za-z ]+)(\d{5}(?:-\d{4})?)",
        "county": r"([A-Za-z ]+) COUNTY"
    }
    
    # Split the text into data chunks based on empty lines
    data_chunks = text.split("\n\n")
    
    # Process each data chunk in the text using a helper function
    read_text_helper(data_chunks, patterns, text_data)
    
    # Create a DataFrame from the list of parsed data
    df = pd.DataFrame(text_data)
    
    return df

def pattern_matcher_util(input_patterns, data_dictionary, chunk):
    """
    Utility function to match patterns in a data chunk and populate a dictionary with the matched values.

    Args:
        input_patterns (dict): A dictionary containing patterns to match against the data chunk.
        data_dictionary (dict): A dictionary to store the matched values.
        chunk (str): The data chunk to search for patterns.

    Returns:
        None: The function updates the 'data_dictionary' in place.
    """
    # Iterate over each pattern in the input_patterns dictionary
    for key, pattern in input_patterns.items():
        # Search for the pattern in the current data chunk
        data_match = re.search(pattern, chunk)
        
        # If a match is found, extract the corresponding value
        if data_match:
            # If the pattern corresponds to 'county', extract and store the value
            if key == "county":
                data_dictionary["county"] = data_match.group(1).strip()
            # If the pattern corresponds to 'state_zip', extract and store the state and zip values separately
            elif key == "state_zip":
                data_dictionary["state"] = data_match.group(1).strip()
                data_dictionary["zip"] = data_match.group(2).strip()
            # For other patterns, extract and store the value
            else:
                data_dictionary[key] = data_match.group(1).strip()
        else:
            # If no match is found, set the value to None
            data_dictionary[key] = None

def read_text_helper(input_data, input_patterns, output_data_list):
    """
    Helper function to parse text blocks and extract address components.

    Args:
    - input_blocks (list): List of text blocks.
    - input_patterns (dict): Dictionary of regex patterns for extracting address components.
    - output_data_list (list): List to store parsed address data.
    """
    # Iterate over each data chunks in the text
    for chunk in input_data:
        # Check if the selected data chunk is not empty
        if chunk:
            # Initialize a dictionary to store data for the current data
            data_dictionary = {}
            
            pattern_matcher_util(input_patterns, data_dictionary, chunk)
            # Append the parsed data for the current block to the data list
            output_data_list.append(data_dictionary)



def format_zip_code(zip_code):
    """
    Format the ZIP code by replacing space-separated ZIP codes with hyphen-separated ZIP codes,
    and removing trailing hyphens.

    Args:
    - zip_code (str): The ZIP code to be formatted.

    Returns:
    - str: The formatted ZIP code.
    """
    # Replace space-separated ZIP codes with hyphen-separated ZIP codes
    zip_code = re.sub(r'(\d)\s*-\s*(\d)', r'\1-\2', zip_code)
    # Remove trailing hyphens
    zip_code = re.sub(r'(\d) -\s*$', r'\1', zip_code)
    return zip_code


def format_zip(row):
    """
    Formats the ZIP code based on the presence of the zip4 component.

    Args:
        row (pandas.Series): A row of data from a DataFrame containing at least 'zip' and 'zip4' columns.

    Returns:
        str: The formatted ZIP code.
    """
    # Check if the 'zip4' component is not null
    if pd.notnull(row['zip4']):
        # If 'zip4' is not null, concatenate 'zip' and 'zip4' components with a hyphen
        return f"{int(row['zip'])}-{int(row['zip4'])}"
    else:
        # If 'zip4' is null, return the original 'zip' value
        return row['zip']
    
def clean_data(data):
    """
    Clean JSON data by removing null values from each row.

    Args:
        data (pandas.DataFrame): DataFrame containing JSON data.

    Returns:
        list: A list of dictionaries with null values removed from each row.
    """
    cleaned_data = [{key: value for key, value in row.items() if pd.notnull(value)} for _, row in data.iterrows()]
    
    return cleaned_data
    
    
    
def load_file(file_path):
    """
    Load data from a file based on its extension.

    Args:
    - file_path (str): Path to the input file.

    Returns:
    - pd.DataFrame or None: DataFrame containing the loaded data, or None if an error occurs.
    """
    

    if file_path.endswith(".txt"):
        df = read_txt(file_path)

    # Load TSV file
    elif file_path.endswith(".tsv"):
        df = pd.read_csv(file_path, delimiter='\t')
        # Concatenate name columns and format ZIP codes
        name_columns = ['first', 'middle', 'last']
        df['name'] = df[name_columns].fillna('').apply(lambda x: ' '.join(x), axis=1)


        df['zip'] = df.apply(format_zip, axis=1)
        

        # Drop unnecessary columns
        df.drop(columns=['zip4', 'first', 'middle', 'last'], inplace=True)

        # Renaming the columns to follow the convention
        df = df.rename(columns={"address": "street"})
    
    
    # Load XML file
    elif file_path.endswith(".xml"):
        df = parse_xml(file_path)
        # Mapping column names and formatting ZIP codes
        column_mapping = {"NAME": "name", "COMPANY": "organization", "CITY": "city",
                        "STREET": "street", "STATE": "state", "POSTAL_CODE": "zip"}
        
        # Renaming the columns as per the column mapping
        df = df.rename(columns=column_mapping)

        # Formatting the zip as per the required conventions
        df['zip'] = df['zip'].apply(format_zip_code)
    
    else:
        # Unsupported file type
        print("Error : This file type is not supported. Please provide correct file.", file=sys.stderr)
        return None
    
    return df


def get_final_data(data):
    """
    Perform data cleaning operations to prepare the final data.

    Args:
        data (pandas.DataFrame): DataFrame containing the raw data.

    Returns:
        pandas.DataFrame: Cleaned and processed DataFrame.
    """

     # Convert zip code to string type
    data['zip'] = data['zip'].astype(str)

    # Replace empty strings with pd.NA
    data.replace('', pd.NA, inplace=True)
    
    # Sort data by zip code
    data = data.sort_values(by='zip')
    
    # Calling the clean data function that gives a list of dictionaries with null values removed from each row.
    data_cleaned = clean_data(data)
    

    return data_cleaned


def main():
    """
    Main function to process input arguments, load data from files, clean the data, and print the cleaned data.

    Usage:
        python3 challenge.py <FILE_PATH_1> ...

    Options:
        --help : Print usage information.

    Returns:
        None
    """

    # Check if the number of arguments is sufficient
    if len(sys.argv) < 2:
        print("To run this code run (for python3): python3 challenge.py <FILE_PATH_1> ... ", file=sys.stderr)
        print("Run for help : python3 challenge.py --help")
        sys.exit(1)


    # Check if help option is requested
    if "--help" in sys.argv:
        print_help()
        sys.exit(0)

    # Extract input file paths from command line arguments
    inputs = sys.argv[1:]

    # Initialize an empty DataFrame to store combined data
    data = pd.DataFrame(columns=['name', 'organization', 'street', 'city', 'county', 'state', 'zip'])

    # Iterate over input file paths
    for input_path in inputs:
        # Load data from file
        df = load_file(input_path)

        # Check if data is successfully loaded
        if df is not None:
            # Combine data with existing DataFrame based on common columns
            data = pd.concat([data, df[data.columns.intersection(df.columns)]])
        else:
            continue
    
    # get the final cleaned data as per requirements

    data_cleaned = get_final_data(data)
    
    # Print the cleaned data in JSON format with indentation
    print(json.dumps(data_cleaned, indent=4))

def print_help():
    print("To run this code run (for python2): python challenge.py <path_to_xml_file> <path_to_tsv_file> <path_to_txt_file>")
    print("To run this code run (for python3): python3 challenge.py <path_to_xml_file> <path_to_tsv_file> <path_to_txt_file>")
    print("Example: python3 challenge.py '../input/input.xml' '../input/input.tsv' '../input/input.txt'")

if __name__ == "__main__":
    main()