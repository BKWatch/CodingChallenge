import sys
import json
import argparse
import csv
import xml.etree.ElementTree as ET


class FileParser:
    """
     A class to encapsulate the parsing logic for different file formats.
     It supports TSV, XML, and plain text formats.
     """

    @staticmethod
    def parse_tsv(input_file):
        """
        Parses a TSV file and returns a list of address entries.

        Parameters:
        - input_file: Path to the TSV file to be parsed.

        Returns:
        - A list of dictionaries, each representing an address.
        """
        try:
            addresses = []
            with open(input_file, 'r', newline='') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    entry = FileParser._parse_row(row)
                    addresses.append(entry)
            return addresses
        except IOError as e:
            sys.stderr.write(f"Error reading file: {e}\n")
            sys.exit(1)

    @staticmethod
    def parse_xml(input_file):
        """
        Parses an XML file and returns a list of address entries.

        Parameters:
        - input_file: Path to the XML file to be parsed.

        Returns:
        - A list of dictionaries, each representing an address.
        """
        try:
            tree = ET.parse(input_file)
        except ET.ParseError as e:
            sys.stderr.write(f"XML parsing error: {e}\n")
            sys.exit(1)
        except IOError as e:
            sys.stderr.write(f"Error reading file: {e}\n")
            sys.exit(1)

        root = tree.getroot()

        addresses = []
        for entity in root.findall('.//ENT'):
            entry = {}
            for prop in entity:
                tag = prop.tag.upper()
                if tag in ['NAME', 'COMPANY', 'STREET', 'CITY', 'STATE', 'POSTAL_CODE']:
                    if tag == 'COMPANY':
                        if prop.text.strip():
                            entry['organization'] = prop.text.strip()
                    elif tag == "POSTAL_CODE":
                        if prop.text.strip(" -"):
                            entry["zip"] = prop.text.strip(" -")
                    elif prop.text.strip():
                        if prop.text.strip():
                            entry[tag.lower()] = prop.text.strip()
            addresses.append(entry)

        return addresses


    @staticmethod
    def parse_text(input_file):
        """
        Parses a plain text file into a list of address entries.

        Parameters:
        - input_file: Path to the text file to be parsed.

        Returns:
        - A list of dictionaries, each representing an address.
        """
        try:
            with open(input_file, 'r') as f:
                content = f.read()
        except IOError as e:
            sys.stderr.write(f"Error reading file: {e}\n")
            sys.exit(1)

        address_blocks = content.strip().split("\n\n")
        addresses = [FileParser._parse_address_block(block) for block in address_blocks]
        return addresses

    @staticmethod
    def _parse_address_block(address_block):
        """
        Parses a block of address text into a dictionary.

        Parameters:
        - address_block: A string block representing an address.

        Returns:
        - A dictionary representing the parsed address.
        """
        lines = [line.strip() for line in address_block.split("\n")]

        address = {"name": lines.pop(0), "street": lines.pop(0)}

        # More concise and clear way to handle optional county
        temp = lines.pop(0)
        if "COUNTY" in temp.upper():
            address["county"] = temp.replace(" COUNTY", "")
            temp = lines.pop(0)

        city_state_zip = temp.split(",")
        address["city"] = city_state_zip[0].strip()
        state_zip = city_state_zip[-1].strip()

        space_index = [i for i, char in enumerate(state_zip) if char == ' '][-1]

        address["state"] = state_zip[:space_index].strip()
        zip_value = state_zip[space_index:].strip()
        address["zip"] = zip_value[:-1] if zip_value[-1] == "-" else zip_value

        return address


    @staticmethod
    def _parse_row(row):
        """
        Parses a single row from a TSV/CSV file into a dictionary.

        Parameters:
        - row: A dictionary representation of a single CSV/TSV row.

        Returns:
        - A dictionary representing the parsed address.
        """
        entry = {}
        if row['first'].strip():
            if row['middle'] != 'N/M/N' and row['middle'].strip() != '':
                entry['name'] = r"{} {} {}".format(row['first'], row['middle'], row['last']).strip(',')
            else:
                entry['name'] = r"{} {}".format(row['first'], row['last']).strip(',')
        else:
            entry["organization"] = row['organization'] if row["organization"] !='N/A' else row['last']
        for key in row.keys():
            if key.lower() in ["address", "city", "state", "county"]:
                if row[key]:
                    entry[key] = row[key]
        if row['zip4']:
            entry['zip'] = r"{} - {}".format(row['zip'], row['zip4'])
        else:
            entry['zip'] = row['zip']
        return entry


def parse_file(file_path):
    """
    Determinates the file type and delegates to the appropriate parser.

    Parameters:
    - file_path: Path to the file to be parsed.

    Returns:
    - The parsed addresses as a list of dictionaries.
    """
    handlers = {'.xml': FileParser.parse_xml, '.tsv': FileParser.parse_tsv, '.txt': FileParser.parse_text}
    extension = file_path.split('.')[-1].lower()
    handler = handlers.get(f".{extension}")
    if handler:
        return handler(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")

def sort_addresses(addresses):
    """
    Sorts a list of address dictionaries by their zip codes.

    Parameters:
    - addresses: A list of dictionaries, each representing an address.

    Returns:
    - The sorted list of addresses.
    """
    return sorted(addresses, key=lambda x: x["zip"])

def main(files):
    """
    Main function to process the input files and output sorted addresses.

    Parameters:
    - files: A list of files to be processed.
    """
    data = []
    for file_path in files:
        try:
            data.extend(parse_file(file_path))
        except Exception as e:
            sys.stderr.write(f"Error processing file {file_path}: {e}\n")
            sys.exit(1)

    sorted_addresses = sort_addresses(data)
    print(json.dumps(sorted_addresses, indent=4))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse address files (XML, TSV, TXT) and output sorted JSON.")
    parser.add_argument('files', nargs='+', help='Paths to the data files')

    args = parser.parse_args()

    if not args.files:
        sys.stderr.write("Error: No files provided.\n")
        sys.exit(1)

    main(args.files)

