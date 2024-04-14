import argparse
import json
import os
import sys
import mmap
import re
import pandas as pd


def parse_xml(file_path):
    """
    Parse XML file containing addresses.
    """
    try:
        xml_data = pd.read_xml(file_path, xpath=".//ENTITY/ENT")
        xml_data.rename(
            columns={
                "NAME": "name",
                "STREET": "street",
                "CITY": "city",
                "STATE": "state",
                "COUNTY": "county",
                "COMPANY": "company",
            },
            inplace=True,
        )
        # Modify zip column from xxxxx - xxxx to xxxxx-xxxx
        xml_data["zip"] = xml_data["POSTAL_CODE"].apply(lambda x: x.split(" -")[0])
        xml_data["zip4"] = xml_data["POSTAL_CODE"].apply(
            lambda x: x.split("- ")[1] if "- " in x else None
        )
        xml_data.drop(
            columns=["STREET_2", "STREET_3", "COUNTRY", "POSTAL_CODE"], inplace=True
        )
        return xml_data
    except Exception as e:
        sys.stderr.write(f"Error parsing XML file {file_path}: {str(e)}\n")
        sys.exit(1)


def parse_tsv(file_path):
    """
    Parse TSV file containing addresses.
    """
    try:
        data = pd.read_csv(file_path, sep="\t")
        data["name"] = data["first"] + " " + data["middle"] + " " + data["last"]
        data.drop(columns=["first", "middle", "last"], inplace=True)
        data.rename(
            columns={
                "address": "street",
                "organization": "company",
            },
            inplace=True,
        )
        return data
    except Exception as e:
        sys.stderr.write(f"Error parsing TSV file {file_path}: {str(e)}\n")
        sys.exit(1)


def extract_city_state_zip(input_string):
    """
    Extract city, state, and zip from a string.
    """
    pattern = r"(?P<city>[A-Za-z\s]+),\s*(?P<state>[A-Za-z\s]+)\s*(?P<zip>\d{5})(?:-(?P<zip4>\d{4}))?"
    match = re.search(pattern, input_string)
    if match:
        return (
            match.group("city"),
            match.group("state").strip(),
            match.group("zip"),
            match.group("zip4"),
        )
    else:
        return None, None, None, None


def parse_txt(file_path):
    """
    Parse TXT file containing addresses.
    """
    try:
        dict_data = {
            "name": [],
            "street": [],
            "city": [],
            "state": [],
            "zip": [],
            "zip4": [],
            "county": [],
            "company": [],
        }
        with open(file_path, "r") as file:
            mm = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
            while mm.tell() < mm.size():
                line = mm.readline().decode("utf-8").strip()
                if line:
                    # First line is name
                    dict_data["name"].append(line)
                    dict_data["company"].append(None)
                    # Read next line for address
                    line = read_next_line(file_path, mm)

                    dict_data["street"].append(line)
                    # Read next line for county
                    line = read_next_line(file_path, mm)
                    if "COUNTY" in line:
                        dict_data["county"].append(line.replace(" COUNTY", ""))
                        line = read_next_line(file_path, mm)
                    else:
                        dict_data["county"].append(None)
                    # The line would be 'city, state zip', using regex to extract city, state, and zip
                    city, state, zip, zip4 = extract_city_state_zip(line)
                    dict_data["city"].append(city)
                    dict_data["state"].append(state)
                    dict_data["zip"].append(zip)
                    dict_data["zip4"].append(zip4)
        return pd.DataFrame(dict_data)
    except Exception as e:
        sys.stderr.write(f"Error parsing TXT file {file_path}: {str(e)}\n")
        sys.exit(1)


def read_next_line(file_path, mm):
    line = mm.readline().decode("utf-8").strip()
    # if not line, then throw error
    if not line:
        sys.stderr.write(f"Error parsing TXT file {file_path}: address is missing\n")
        sys.exit(1)
    return line


def main():
    parser = argparse.ArgumentParser(
        description="Parse US names and addresses from different file formats and output as JSON."
    )
    parser.add_argument(
        "files", metavar="FILE", type=str, nargs="+", help="input file(s) to parse"
    )

    args = parser.parse_args()

    all_addresses = []
    for file_path in args.files:
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == ".xml":
            addresses = parse_xml(file_path)
        elif file_ext == ".tsv":
            addresses = parse_tsv(file_path)
        elif file_ext == ".txt":
            addresses = parse_txt(file_path)
        else:
            sys.stderr.write(f"Unsupported file format: {file_ext}\n")
            sys.exit(1)

        if addresses is not None:
            all_addresses.append(addresses)

    if all_addresses:
        # Merge all addresses
        dt: pd.DataFrame = pd.concat(all_addresses, axis=0, ignore_index=True)

        #  if zip is none, throw error
        if dt["zip"].isnull().any():
            sys.stderr.write("Error: zip code is missing in some addresses\n")
            sys.exit(1)

        # Change zip to int
        dt["zip"] = dt["zip"].astype(int)
        # Sort by zip
        dt.sort_values(by=["zip"], inplace=True, ignore_index=True)
        # Reset index
        dt.reset_index(drop=True, inplace=True)
        # Mix columns zip and zip4
        dt["zip"] = dt.apply(
            lambda x: (
                str(x["zip"])
                + (("-" + str(int(x["zip4"]))) if not pd.isnull(x["zip4"]) else "")
            ),
            axis=1,
        )
        # Drop zip4 column
        dt.drop(columns=["zip4"], inplace=True)
        print(
            json.dumps(list(dt.agg(lambda x: x.dropna().to_dict(), axis=1)), indent=2)
        )
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
