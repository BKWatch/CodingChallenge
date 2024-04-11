import sys
import os
import xml.etree.ElementTree as ET
import argparse


def find_first_digit_position(string):
    for i, char in enumerate(string):
        if char.isdigit():
            return i
    return -1


def txt_parser(path: str):

    with open(path, "r") as f:
        text = f.read()

    chunks = text.strip().split('\n\n')
    grouped_data = [chunk.split('\n') for chunk in chunks]

    combined_addresses = []

    for chank in grouped_data:

        country = ""
        name = chank[0]
        street = chank[1]
        try:
            last_row = chank[3]
            country = chank[2].strip().split(" ")[0]
        except:
            last_row = chank[2]

        pos = find_first_digit_position(last_row)

        zip_code = last_row[pos:]

        if not zip_code[-1].isdigit():
            zip_code = zip_code[:-1]

        state = last_row.split(", ")[1].split(" ")[0].join("")

        data = {
            "name": name.strip(),
            "street": street.strip(),
            "country": country.strip(),
            "state": state.strip(),
            "zip": zip_code.strip()
        }

        combined_addresses.append(data)

    return combined_addresses


def tsv_parser(path: str):
    grouped_data = []

    with open(path, "r") as file:
        for line in file:
            grouped_data.append(line.split("\t"))

    grouped_data = grouped_data[1:]

    combined_addresses = []
    for chank in grouped_data:

        if chank[0] != "":
            if chank[1] == "N/M/N":
                name = f"{chank[0]} {chank[2]}"
            else:
                name = f"{chank[0]} {chank[1]} {chank[2]}"
            street = chank[4]
            city = chank[5]
            country = chank[7]
            state = chank[6]
            if chank[9] != "\n":
                zip_code = f"{chank[8]}-{chank[9]}"
            else:
                zip_code = chank[8]

            data = {
                "name": name.strip(),
                "street": street.strip(),
                "city": city.strip(),
                "country": country.strip(),
                "state": state.strip(),
                "zip": zip_code.strip()
            }

        else:
            if chank[3] == "N/A":
                organization = chank[2]
            else:
                organization = chank[3]
            street = chank[4]
            city = chank[5]
            country = chank[7]
            state = chank[6]
            if chank[9] != "\n":
                zip_code = f"{chank[8]}-{chank[9]}"
            else:
                zip_code = chank[8]

            data = {
                "organization": organization.strip(),
                "street": street.strip(),
                "city": city.strip(),
                "country": country.strip(),
                "state": state.strip(),
                "zip": zip_code.strip()
            }

        combined_addresses.append(data)

    return combined_addresses


def xml_parser(path: str):

    root = ET.parse(path).getroot()
    combined_addresses = []
    for ent in root.findall('.//ENT'):
        entity = {}
        name = ent.find('NAME').text.strip()
        if name:
            entity['name'] = name
        else:
            entity['organization'] = ent.find('COMPANY').text.strip()
        entity['street'] = ent.find('STREET').text.strip()
        entity['city'] = ent.find('CITY').text.strip()
        entity['state'] = ent.find('STATE').text.strip()
        zip_code = ent.find('POSTAL_CODE').text.strip()
        zip_code = "".join(zip_code.split(" "))
        if zip_code[-1] == "-":
            zip_code = zip_code[:-1]
        entity['zip'] = zip_code
        combined_addresses.append(entity)

    return combined_addresses


def main():
    parser = argparse.ArgumentParser(description='Parse files and combine addresses.')
    parser.add_argument('paths', nargs='+', help='Paths to files to parse')
    args = parser.parse_args()

    all_parsed_data = []

    error_occurred = False

    for path in args.paths:

        if not os.path.exists(path):
            print(f"Error: File '{path}' not found", file=sys.stderr)
            error_occurred = True
            continue

        if path.endswith("txt"):
            parsed_data = txt_parser(path)

        elif path.endswith("tsv"):
            parsed_data = tsv_parser(path)

        elif path.endswith("xml"):
            parsed_data = xml_parser(path)

        else:
            print(
                f"Error: '{path}' has an invalid file extension", file=sys.stderr)
            error_occurred = True
            continue

        all_parsed_data.extend(parsed_data)
        all_parsed_data_sorted = sorted(all_parsed_data, key=lambda x: x['zip'])
        
    if error_occurred:
        sys.exit(1)

    for data in all_parsed_data_sorted:
        print(data)

    sys.exit(0)


if __name__ == '__main__':
    main()
