import argparse
import os
import xml.etree.ElementTree as ET
import sys
import json
import re
import csv

ordered_keys = ["name", "organization", "street", "city", "state", "county", "zip"]


def create_empty_entity():
    return {key: None for key in ordered_keys}


def clean_none_values(entity):
    return {k: v for k, v in entity.items() if v is not None}


# Some ZIP codes have a trailing hyphen, this function removes it
def clean_and_validate_zip(zip_code):
    if zip_code.endswith("-"):
        return zip_code[:-1]
    if not re.match(r"^\d{5}(-\d{4})?$", zip_code):
        raise ValueError(f"Invalid ZIP code: {zip_code}")
    return zip_code


class FileTypeChecker(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        _ = option_string
        valid_extensions = (".txt", ".xml", ".tsv")
        for value in values:
            ext = os.path.splitext(value)[1]
            if ext not in valid_extensions:
                parser.error(f"file '{value}' does not end with {valid_extensions}")
        setattr(namespace, self.dest, values)


def xml_validate_structure(root):
    entity_exists = root.find("ENTITY")
    ent_exists = root.findall("ENT")
    if entity_exists is None:
        raise ValueError("ENTITY section is missing")
    if ent_exists is None:
        raise ValueError("ENT sections are missing")


def xml_extract_entity_data(entity, fields):
    entity_data = create_empty_entity()
    street = []

    for field in fields:
        element = entity.find(field)
        assigned_field = field.lower()
        value = (
            element.text.strip()
            if element is not None and element.text is not None
            else None
        )

        if assigned_field == "postal_code":
            value = value.replace(" ", "")
            value = clean_and_validate_zip(value)
            assigned_field = "zip"
        if assigned_field == "company":
            assigned_field = "organization"
        if "street" in field.lower():
            if value:
                street.append(value)
        else:
            if value:
                entity_data[assigned_field] = value if value else None

    entity_data["street"] = ", ".join(street)
    return clean_none_values(entity_data)


def parse_xml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        xml_validate_structure(root)

        entities = []

        fields = [
            "NAME",
            "COMPANY",
            "STREET",
            "STREET_2",
            "STREET_3",
            "CITY",
            "COUNTY",
            "STATE",
            "POSTAL_CODE",
        ]
        for entity in root.findall(".//ENT"):
            entity_data = xml_extract_entity_data(entity, fields)
            entities.append(entity_data)
        return entities
    except FileNotFoundError as e:
        print(f"File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def text_split_address(address):
    # Assuming the address is in the format "city, state ZIP code"
    city, state_and_zip = map(str.strip, address.strip().split(","))
    match = re.search(r"\d", state_and_zip)
    if match:
        index = match.start()
        state = state_and_zip[:index].strip()
        zip_code = clean_and_validate_zip(state_and_zip[index:].strip())
    else:
        raise ValueError("Invalid address format: ZIP code not found in address")
    return city, state, zip_code


def text_validate_entry_structure(entry):
    #  An entry should have 3 or 4 lines
    if len(entry) not in [3, 4]:
        raise ValueError("Invalid number of lines in", entry)


def text_extract_entity_data(entry):
    entity_data = create_empty_entity()
    entry = entry.split("\n")
    text_validate_entry_structure(entry)
    entry_contains_county = len(entry) == 4
    entity_data["name"] = entry[0].strip()
    entity_data["street"] = entry[1].strip()
    if entry_contains_county:
        entity_data["county"] = entry[2].replace("COUNTY", "").strip()
        city, state, zip = text_split_address(entry[3])
    else:
        city, state, zip = text_split_address(entry[2])
    entity_data["city"] = city
    entity_data["state"] = state
    entity_data["zip"] = zip
    return clean_none_values(entity_data)


def parse_txt(file_path):
    try:
        with open(file_path, "r") as file:
            content = file.read()
        entries = content.split("\n\n")
        entries = [entry.strip() for entry in entries if entry]
        entities = []
        for entry in entries:
            entities.append(text_extract_entity_data(entry))
        return entities

    except FileNotFoundError as e:
        print(f"File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def tsv_extract_entity_data(row):
    entity = create_empty_entity()

    is_organization = row["first"].strip() == ""
    if is_organization:
        if row["organization"].strip() != "N/A":
            entity["organization"] = row["organization"].strip()
        else:
            entity["organization"] = row["last"].strip()
    else:
        name = []
        name.append(row["first"].strip())
        middle_name = row["middle"].strip()
        if middle_name != "N/M/N" and middle_name:
            name.append(middle_name)
        name.append(row["last"].strip())
        entity["name"] = " ".join(name).replace(",", "")

    county = row["county"].strip()
    if county:
        entity["county"] = county
    entity["street"] = row["address"].strip()
    entity["city"] = row["city"].strip()
    entity["state"] = row["state"].strip()
    entity["zip"] = clean_and_validate_zip(
        row["zip"].strip() + "-" + row["zip4"].strip()
    )
    entity = clean_none_values(entity)
    return entity


def tsv_validate_structure(reader, fields):
    if not all(field in reader.fieldnames for field in fields):
        raise ValueError("TSV file does not contain all required fields")


def parse_tsv(file_path):
    try:
        with open(file_path, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            tsv_validate_structure(
                reader,
                [
                    "first",
                    "middle",
                    "last",
                    "organization",
                    "address",
                    "city",
                    "state",
                    "county",
                    "zip",
                    "zip4",
                ],
            )
            entities = []
            for row in reader:
                entities.append(tsv_extract_entity_data(row))
            return entities
    except FileNotFoundError as e:
        print(f"File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except csv.Error as e:
        print(f"Error parsing TSV file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing TSV file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="BW Challenge")
    parser.add_argument(
        "files",
        nargs="+",
        action=FileTypeChecker,
        help="List of file paths (txt, xml, tsv)",
    )
    args = parser.parse_args()
    all_entities = []
    for file in args.files:
        _, ext = os.path.splitext(file)
        if ext == ".xml":
            entities = parse_xml(file)
        elif ext == ".txt":
            entities = parse_txt(file)
        elif ext == ".tsv":
            entities = parse_tsv(file)
        all_entities.extend(entities)

    # Sort entities by zip code
    all_entities = sorted(all_entities, key=lambda x: x["zip"])

    json_output = json.dumps(all_entities, indent=4)
    print(json_output)
    sys.exit(0)


if __name__ == "__main__":
    main()
