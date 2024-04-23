import argparse
import json
import sys
import csv
import xml.etree.ElementTree as ET


def parse_xml_to_json(file_path):
    """
    Parses XML file to extract address data.

    Args:
        file_path (str): The path to the XML file.

    Returns:
        list of dict: A list of dictionaries representing addresses.
    """
    json_dict = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        for item in root.findall('./ENTITY/ENT'):
            address = {}

            name = item.find('NAME').text.strip()
            if name:
                address['name'] = name

            organization = item.find('COMPANY').text.strip()
            if organization:
                address['organization'] = organization

            address['street'] = " ".join(
                [
                    item.find('STREET').text or "",
                    item.find('STREET_2').text or "",
                    item.find('STREET_3').text or "",
                ]
            ).strip()

            address['city'] = item.find('CITY').text.strip()
            country = item.find('COUNTRY').text.strip()
            if country:
                address['country'] = country

            address['state'] = item.find('STATE').text.strip()

            zip_code = item.find("POSTAL_CODE").text.strip()
            if zip_code:
                if zip_code.endswith("-"):
                    address["zip"] = zip_code[:5]
                else:
                    address["zip"] = zip_code.replace(" ", "")
            json_dict.append(address)

    except Exception as e:
        sys.stderr.write(
            f"Error occurred while parsing XML file: {file_path}\n")
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    return json_dict


def parse_tsv_to_json(file_path):
    """
    Parses TSV file to extract address data.

    Args:
        file_path (str): The path to the TSV file.

    Returns:
        list of dict: A list of dictionaries representing addresses.
    """
    json_data = []

    try:
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')

            for row in reader:
                first_name = row['first']
                middle_name = row['middle'] if row['middle'] != 'N/M/N' else None
                last_name = row['last']

                # Check if the first name exists and is not empty
                if first_name:
                    name = ' '.join(
                        filter(
                            None, [
                                first_name, middle_name, last_name]))
                    organization = row['organization'] or None
                else:
                    name = None
                    organization = ' '.join(
                        filter(None, [row['last'], row['organization']]))
                    if organization.endswith(' N/A'):
                        organization = organization[:-4].strip()

                street = ' '.join(filter(None, [row['address']]))
                city = row['city']
                county = row['county'] if row['county'] else None
                state = row['state']
                zip_code = row['zip'] + \
                    ('' if row['zip4'] == '' else '-' + row['zip4'])

                if name:
                    if county:
                        address = {
                            'name': name,
                            'street': street,
                            'city': city,
                            'county': county,
                            'state': state,
                            'zip': zip_code
                        }
                    else:
                        address = {
                            'name': name,
                            'street': street,
                            'city': city,
                            'state': state,
                            'zip': zip_code
                        }

                else:
                    address = {
                        'organization': organization,
                        'street': street,
                        'city': city,
                        'state': state,
                        'zip': zip_code
                    }

                json_data.append(address)

    except Exception as e:
        sys.stderr.write(
            f"Error occurred while parsing TSV file: {file_path}\n")
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    return json_data


def parse_txt_to_json(file_path):
    """
    Parses plain text file to extract address data.

    Args:
        file_path (str): The path to the plain text file.

    Returns:
        list of dict: A list of dictionaries representing addresses.
    """
    json_data = []
    company_types = ["llc", "inc.", "pvt.", "ltd."]
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        i = 0
        while i < len(lines):
            address = {}
            county = ""

            if not lines[i].strip():
                i += 1
                continue

            name_or_org = lines[i].strip()
            if any(key in name_or_org.lower() for key in company_types):
                address["organization"] = name_or_org
            else:
                address["name"] = name_or_org

            address["street"] = lines[i + 1].strip()

            if "," in lines[i + 2]:
                city_state_split = lines[i + 2].split(", ")
                i += 4
            else:
                county = lines[i + 2].strip()
                city_state_split = lines[i + 3].split(", ")
                i += 5

            address["city"] = city_state_split[0].strip()

            if county:
                address["county"] = county

            city_state_zip = city_state_split[1].split()
            address["state"] = city_state_zip[-2]

            zip_code = city_state_zip[-1]
            if zip_code.endswith('-'):
                zip_code = zip_code[:-1]  # Remove trailing hyphen

            address["zip"] = zip_code

            json_data.append(address)

    except Exception as e:
        sys.stderr.write(
            f"Error occurred while parsing TXT file: {file_path}\n")
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    return json_data


def main():
    """
    Main function to parse different file formats to JSON.

    Returns:
        int: 0 if successful, 1 if failed.
    """
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('files_path', 
                            type=str, 
                            nargs='+', 
                            help='Pass file or List of files (path) in the following file formats: .xml, .tsv, or .txt')
        args = parser.parse_args()
        output = []

        for file_path in args.files_path:
            try:
                if file_path.endswith(".xml"):
                    json_output = parse_xml_to_json(
                        file_path)  # Parse XML File to JSON
                elif file_path.endswith(".tsv"):
                    json_output = parse_tsv_to_json(
                        file_path)  # Parse TSV File to JSON
                elif file_path.endswith(".txt"):
                    json_output = parse_txt_to_json(file_path)
                else:
                    sys.stderr.write(
                        f"Error: Invalid file format detected: \"{file_path}\"\n")
                    sys.stderr.write(
                        "Please ensure the file format is one of the following: .xml, .tsv, or .txt\n")
                    return 1  # failure
                output.extend(json_output)
            except FileNotFoundError:
                sys.stderr.write(f"Error: File '{file_path}' not found.\n")
                return 1  # failure

        json_output = list(sorted(output, key=lambda x: x.get("zip")))
        json_output = json.dumps(json_output, indent=2)
        print(json_output)
        return 0  # success

    except Exception as e:
        sys.stderr.write(f"Error Occurred: {e}\n")
        return 1  # failure


if __name__ == '__main__':
    sys.exit(main())
