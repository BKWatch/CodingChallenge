''' How to run the code:
 cd to the codeChallenge directory where contains challenge.py and all the relevant input files, and run the following
 command:
 $ python challenge.py input/input1.xml input/input2.tsv input/input3.txt
'''

import csv
from typing import List, Dict
import xml.etree.ElementTree as ET
from collections import OrderedDict
import json
import argparse
import sys


def order_dict(data: Dict[str, str]) -> OrderedDict:
    '''
    :param data: a dict
    :return: an OrderedDict where key ordered in the following orders
    '''
    key_order = ['name', 'organization', 'street', 'city', 'county', 'state', 'zip']
    ordered_dict = OrderedDict((key, data[key]) for key in key_order if key in data)
    return ordered_dict


def construct_order_dict_list(all_info: List[Dict[str, str]]) -> List[OrderedDict]:
    '''
    :param all_info: a list of dict
    :return: a list of Ordered dict
    '''
    return [order_dict(info) for info in all_info]


def read_tsv(tsv_file: str) -> List[OrderedDict]:
    '''
    :param tsv_file: the path of the tsv_file
    :return: a list of Orderdict, where each dictionary corresponds to a row in the TSV and stores all the non-empty
             information, with adjusted column headers as keys and the keys are ordered.
    '''
    try:
        with open(tsv_file, 'r') as file:
            # Create a CSV reader object specifying the delimiter as a tab
            tsv_reader = csv.reader(file, delimiter='\t')

            # use header to map the index with field name
            header = next(tsv_reader)
            index_map = {k: v for k, v in enumerate(header)}
            index_map[4] = "street"

            all_info = []
            # Iterate over rows in the TSV file
            for row in tsv_reader:
                # Solve the disorder problem that occurs when the name is empty
                if not row[0] and not row[1] and row[2] and row[2] != "N/A":
                    row.insert(0, "")
                    row.pop(4)

                info = {}

                # parse name
                name = []
                for i in range(3):
                    if row[i] and row[i] != "N/M/N":
                        name.append(row[i])
                if name:
                    info['name'] = " ".join(name)

                # parse org, street, state, county
                for i in range(3, len(row)-1):
                    if row[i] and row[i] != "N/A":
                        info[index_map[i]] = row[i]

                # parse zip
                zip_code = []
                for i in range(len(row)-2, len(row)):
                    if row[i]:
                        zip_code.append(row[i])
                if zip_code:
                    info["zip"] = "-".join(zip_code)

                all_info.append(info)
        return construct_order_dict_list(all_info)
    except IOError as e:
        sys.stderr.write(f"Error reading TSV file: {e}\n")
        sys.exit(1)
    except csv.Error as e:
        sys.stderr.write(f"Error parsing TSV file: {e}\n")
        sys.exit(1)


def read_txt(txt_file: str) -> List[OrderedDict]:
    '''
    :param txt_file: the path of the txt_file
    :return: a list of OrderedDict, where each dictionary corresponds to a row in the TSV and stores all the non-empty
                 information, with adjusted column headers as keys and the keys are ordered.
    '''
    try:
        with open(txt_file, 'r', encoding='utf-8') as file:
            # split with "\n\n" fo find data blocks
            content = file.read().split("\n\n")
            all_info = []

            for data in content:
                if data:
                    doc = data.split("\n")
                    info = {}

                    # name - first line
                    info["name"] = doc[0].strip()
                    # street - second line
                    info["street"] = doc[1].strip()

                    # city, state, zip - last line
                    city, state_zip = doc[-1].split(",")
                    state_zip_list = state_zip.split()
                    state = " ".join(state_zip_list[:-1])
                    zip = state_zip_list[-1]
                    if zip[-1] == '-':
                        zip = zip[:-1]
                    info["city"] = city.strip()
                    info["state"] = state.strip()
                    info["zip"] = zip.strip()

                    # if there's county - second last line
                    if len(doc) == 4:
                        county = doc[-2].split()[0]
                        info["county"] = county.strip()

                    all_info.append(info)
        return construct_order_dict_list(all_info)
    except IOError as e:
        sys.stderr.write(f"Error reading TXT file: {e}\n")
        sys.exit(1)


def read_xml(xml_file: str) -> List[OrderedDict]:
    '''
    :param xml_file: the path of the xml_file
    :return: a list of OrderedDict, where each dictionary corresponds to a row in the TSV and stores all the non-empty
             information, with adjusted column headers as keys and the keys are ordered.
    '''
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        all_info = []
        for ent in root.find('ENTITY'):
            info = {}
            # name
            name = ent.find('NAME').text.strip()
            if name:
                info['name'] = name
            # organization
            company = ent.find('COMPANY').text.strip()
            if company:
                info['organization'] = company
            # street
            street = ent.find('STREET').text.strip()
            street2 = ent.find('STREET_2').text.strip()
            street3 = ent.find('STREET_3').text.strip()
            if street:
                if street2:
                    street += ", "+street2
                if street3:
                    street += ", " + street3
            if street:
                info['street'] = street
            # city
            city = ent.find('CITY').text.strip()
            if city:
                info['city'] = city
            # state
            state = ent.find('STATE').text.strip()
            if state:
                info['state'] = state
            # zip
            postal_code = ent.find('POSTAL_CODE').text.strip()
            zip_list = [code.strip() for code in postal_code.split("-") if code]
            zip = "-".join(zip_list)
            if zip:
                info['zip'] = zip
            all_info.append(info)
        return construct_order_dict_list(all_info)
    except IOError as e:
        sys.stderr.write(f"Error reading XML file: {e}\n")
        sys.exit(1)
    except ET.ParseError as e:
        sys.stderr.write(f"Error parsing XML file: {e}\n")
        sys.exit(1)


def parse_files(files: List[str]) -> List[OrderedDict]:
    '''
    Parse all file in the files list, exit if file does not exist or file has unknown extension type
    :param files: a list of file paths
    :return: a list of OrderedDict
    '''
    entries = []
    for file_path in files:
        if file_path.endswith('.xml'):
            entries.extend(read_xml(file_path))
        elif file_path.endswith('.tsv'):
            entries.extend(read_tsv(file_path))
        elif file_path.endswith('.txt'):
            entries.extend(read_txt(file_path))
        else:
            sys.stderr.write(f"Unsupported file format for {file_path}")
            sys.exit(1)

    return sorted(entries, key=lambda x: x['zip'])


def main():
    parser = argparse.ArgumentParser(description="Process XML, TSV, and TXT files to extract personal information.")
    parser.add_argument('files', nargs='+', help="List of file paths to process.")
    args = parser.parse_args()

    try:
        sorted_entries = parse_files(args.files)
        print(json.dumps(sorted_entries, indent=2))
        sys.exit(0)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
