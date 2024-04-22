import argparse
import os
import xml.etree.ElementTree as ET
import sys
import json


class FileTypeChecker(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        _ = option_string
        valid_extensions = (".txt", ".xml", ".tsv")
        for value in values:
            ext = os.path.splitext(value)[1]
            if ext not in valid_extensions:
                parser.error(f"file '{value}' does not end with {valid_extensions}")
        setattr(namespace, self.dest, values)


def parse_xml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        entities = []

        def extract_entity_data(entity, fields):
            entity_data = {}
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
                    if value.endswith("-"):
                        value = value[:-1]
                if "street" in field.lower():
                    if value:
                        street.append(value)
                else:
                    if value != "" and value is not None:
                        entity_data[assigned_field] = value
            entity_data["street"] = ", ".join(street)
            return entity_data

        fields = [
            "NAME",
            "COMPANY",
            "STREET",
            "STREET_2",
            "STREET_3",
            "CITY",
            "STATE",
            "POSTAL_CODE",
        ]
        for entity in root.findall(".//ENT"):
            entity_data = extract_entity_data(entity, fields)
            entities.append(entity_data)
        return entities
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}", file=sys.stderr)
        sys.exit(1)


def parse_txt(file_path):
    # print("Parsing TXT file:", file_path)
    return []


def parse_tsv(file_path):
    # print("Parsing TSV file:", file_path)
    return []


def main():
    parser = argparse.ArgumentParser(description="BW Challenge")
    parser.add_argument(
        "files",
        nargs="+",
        action=FileTypeChecker,
        help="List of file paths (txt, xml, tsv)",
    )
    args = parser.parse_args()
    print("Validated file paths:", args.files)

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

    json_output = json.dumps(all_entities, indent=4)
    print(json_output)
    sys.exit(0)


if __name__ == "__main__":
    main()
