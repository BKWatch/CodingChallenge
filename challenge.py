import sys
import pandas as pd
import xml.etree.ElementTree as ET
import re
import json


class ErrorManager:
    def __init__(self):
        self.errors = []

    def add_error(self, message):
        self.errors.append(message)

    def has_errors(self):
        return bool(self.errors)


error_manager = ErrorManager()
# this helps to load all the errors that were generated


def print_help():
    print("Usage: python challlenge.py <paths>")
    print("Arguments:")
    print("  paths: lists all file paths to read from")
    print("ex: python challenge.py <input_path1> <input_path2> ...")


def read_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    meta_element = root.find("META")
    if meta_element is not None:
        assigned = meta_element.find("ASSIGNED").text
        phone = meta_element.find("PHONE").text
        date = meta_element.find("DATE").text
        print("META:")
        print("Assigned:", assigned)
        print("Phone:", phone)
        print("Date:", date)
    else:
        print("META element not found.")
    entity_data = [{child.tag: child.text for child in ent
                    } for ent in root.findall("ENTITY/ENT")]
    df = pd.DataFrame(entity_data)
    return df


def replace_dash(text):
    # Replace ' - ' with '-' between numbers
    text = re.sub(r'(\d)\s*-\s*(\d)', r'\1-\2', text)
    # Remove trailing hyphen
    text = re.sub(r'(\d) -\s*$', r'\1', text)
    return text


def read_txt_file(input_file):
    with open(input_file, "r") as file:
        text = file.read()
    data_l = []
    blocks = text.split("\n\n")  # \n\n inidcates new line
    patterns = {
        "name": r"(.+)",
        "street": r"(\d+ .+)",
        "city": r"(.+),",
        "State_ZIP": r"([A-Za-z ]+)(\d{5}(?:-\d{4})?)",
        "county": r"([A-Za-z ]+) COUNTY"
        }
    for block in blocks:
        # for loop not efficient but it helps to load data into df
        if (block != ''):
            block_data = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, block)
                if match:
                    if key == "State_ZIP":
                        block_data["state"] = match.group(1).strip()
                        block_data["zip"] = match.group(2).strip()
                    elif key == "county":
                        block_data["county"] = match.group(1).strip()
                    else:
                        block_data[key] = match.group(1).strip()
                else:
                    block_data[key] = None
            data_l.append(block_data)
        else:
            print('skipped line')  # accounts for unkown blank lines
    df = pd.DataFrame(data_l)
    return df


def file_load(input_file):
    if (input_file.endswith(".xml")):  # case 1
        try:
            df = read_xml(input_file)
            df = df.rename(columns={"NAME": "name",
                                    "COMPANY": "organization", "CITY": "city",
                                    "STREET": "street", "STATE": "State",
                                    "POSTAL_CODE": "zip"})
            df['zip'] = df['zip'].apply(replace_dash)
            return df
        except Exception as e:
            print("An error occurred:", e, file=sys.stderr)
            error_manager.add_error(e)
            return None
    elif (input_file.endswith(".tsv")):  # case 2
        try:
            df = pd.read_csv(input_file, delimiter='\t')
            df['name'] = df[['first', 'middle', 'last']].apply(
                lambda x: ' '.join(x.dropna()), axis=1)
            df['zip_new'] = df.apply(
                lambda row: f"{int(row['zip'])}-{int(row['zip4'])}"
                if pd.notnull(row['zip4']) else row['zip'], axis=1)
            df.drop(columns=['zip', 'zip4'], inplace=True)
            df['zip'] = df['zip_new']
            df['zip'] = df['zip'].astype(str)
            df = df.rename(columns={"address": "street"})
            df.drop(columns=['zip_new', 'first', 'middle', 'last'],
                    inplace=True)
            return df
        except Exception as e:
            print("An error occurred:", e, file=sys.stderr)
            error_manager.add_error(e)
            return None
    elif (input_file.endswith(".txt")):  # case 3
        try:
            df = read_txt_file(input_file)
            return df
        except Exception as e:
            print("An error occurred:", e, file=sys.stderr)
            error_manager.add_error(e)
            return None
    else:
        print(
            """An error occurred: file type not supported
              or its not formated correctly""",
            file=sys.stderr)
        error_manager.add_error("""file type not supported or
                                 its not formated correctly""")
        return None


def union_df(df1, df2):
    common_columns = df1.columns.intersection(df2.columns)
    df2_filtered = df2[common_columns]
    combined_df = pd.concat([df1, df2_filtered])
    return combined_df


def main():
    # Check if there are arguments provided
    if "--help" in sys.argv:
        print_help()
        sys.exit(0)
    if len(sys.argv) < 2:
        print(
            "Usage: python challenge.py <input_path1> <input_path2> ...",
            file=sys.stderr)
        error_manager.add_error(
            "Usage: python challenge.py <input_path1> <input_path2> ..."
                                )
        sys.exit(1)
    # Extract inputs from command line arguments
    inputs = sys.argv[1:]
    data = pd.DataFrame(columns=['name',
                                 'organization', 'street', 'city', 'county',
                                 'state', 'zip'])
    # Process each input
    for item_path in inputs:
        tem = file_load(item_path)  # function to load data
        if tem is not None:
            data = union_df(data, tem)  # help to merges all data loaded
        else:
            continue
    data.replace('', pd.NA, inplace=True)
    data = data.sort_values(by='zip')
    json_data_cleaned = [
        {key: value for key, value in row.items() if pd.notnull(value)}
        for _, row in data.iterrows()
        ]
    print(json.dumps(json_data_cleaned, indent=4))
    if error_manager.has_errors():
        sys.exit(1)
    else:
        print("No errors occurred")
        sys.exit(0)


if __name__ == "__main__":
    main()
