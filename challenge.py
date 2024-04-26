"""Read address information from various file formats and output it as JSON.

Read name, organization, street, city, county, state, and zip information from
TSV, XML, and plain text files and output them as pretty-printed JSON.
"""

import dataclasses
import json
import csv
import argparse
import os
import xml.etree.ElementTree as ET
from typing import Optional, TextIO, cast

####
## Argument parsing prerequisites
####


class FileExtensionChoices:
    "Allows only files that have the extensions passed in when the object was created."

    def __init__(self, *choices: str) -> None:
        self.choices = choices

    def __contains__(self, choice: TextIO):
        return any(choice.name.endswith(ext) for ext in self.choices)

    def __iter__(self):
        return iter(f"<yourfilename>{ext}" for ext in self.choices)


parser = argparse.ArgumentParser(
    prog="CodingChallenge",
    description=__doc__,
    epilog="Try with any number of files!",
)

parser.add_argument(
    "files",
    nargs="+",
    type=argparse.FileType("r"),
    choices=FileExtensionChoices(".txt", ".tsv", ".xml"),
    help="TXT, TSV, or XML files to parse for data",
)

####
## Data structures
####


@dataclasses.dataclass
class AddressInformation:
    """Extracted address information.

    Properties:
     - `name`: The person's full name, if present, consisting of a list of one or more given names followed by the family name
     - `organization`: The company or organization name, if present
     - `street`: The street address, often just a house number followed by a direction indicator and a street name
     - `city`: The city name
     - `county`: The county name, if present
     - `state`: The US state name or abbreviation
     - `zip`: The ZIP code or ZIP+4, in the format 00000 or 00000-0000

    Note: A personal name or organization name will always be present, but not both.
    """

    name: Optional[str]
    organization: Optional[str]
    street: str
    city: str
    county: Optional[str]
    state: str
    zip: str


####
## Data collection and normalization utilities
####


def normalize_zip_code(zip: str) -> str:
    "Make sure dashes are only being used to separate actual numbers, not empty things."
    return "-".join(filter(lambda x: len(x) > 0, zip.split("-")))


def split_at_first_number(string: str) -> tuple[str, str]:
    "Split the given string at the first number from left to right."

    for i, c in enumerate(string):
        if c.isnumeric():
            break

    return (string[:i], string[i:])


def extract_name(
    first: str, middle: str, last: str, organization: str
) -> tuple[Optional[str], Optional[str]]:
    "Returns (name, None) if the given data adds up to a person's name, (None, org) if it adds up to an organization."
    if organization != "N/A":
        return (None, organization)
    elif first == "" and middle == "" and last != "":
        return (None, last)
    elif middle == "N/M/N" or middle == "":
        return (f"{first} {last}", None)
    else:
        return (f"{first} {middle} {last}", None)


####
## Data collection code for: TSV, XML, TXT
####


def process_tsv_file(fhandle: TextIO) -> list[AddressInformation]:
    # Just setting strict=True should validate the tab-delimited CSV file for us
    reader = csv.DictReader(fhandle, delimiter="\t", strict=True)

    def row_to_address(row: dict) -> AddressInformation:
        name, org = extract_name(
            row["first"], row["middle"], row["last"], row["organization"]
        )

        expected_keys = [
            "city",
            "state",
            "zip",
            "zip4",
            "address",
            "county",
            "first",
            "middle",
            "last",
            "organization",
        ]
        if not set(expected_keys).issubset(row.keys()):
            raise ValueError(
                f'Some keys missing in XML entity: expected {", ".join(expected_keys)}. Got: {row.keys()}'
            )

        return AddressInformation(
            name=name,
            organization=org,
            street=row["address"],
            county=row["county"].upper() if row["county"] != "" else None,
            city=row["city"],
            state=row["state"],
            zip=(
                "-".join([row["zip"], row["zip4"]]) if row["zip4"] != "" else row["zip"]
            ),
        )

    return list(map(row_to_address, reader))


def process_xml_file(fhandle: TextIO) -> list[AddressInformation]:
    tree_root = ET.fromstring(fhandle.read())
    entities = tree_root.findall("./ENTITY/ENT")
    if len(entities) == 0:
        raise ValueError("No entities in XML file in the expected position!")

    def entity_to_address(entity: ET.Element) -> AddressInformation:
        entity_dict = {
            line.tag.lower(): line.text
            for line in entity
            if cast(str, line.text).strip() != ""
        }

        expected_keys = ["city", "state", "postal_code", "street"]

        if not set(expected_keys).issubset(entity_dict.keys()) or (
            "name" not in entity_dict and "company" not in entity_dict
        ):
            raise ValueError(
                f'Some keys missing in XML entity: expected {", ".join(expected_keys)} and either name or company. Got: {entity_dict.keys()}'
            )

        return AddressInformation(
            name=entity_dict.get("name"),
            organization=entity_dict.get("company"),
            street=", ".join(
                filter(
                    None,
                    [
                        entity_dict["street"],
                        entity_dict.get("street_2"),
                        entity_dict.get("street_3"),
                    ],
                )
            ),
            city=cast(str, entity_dict["city"]),
            state=cast(str, entity_dict["state"]),
            county=None,
            zip=normalize_zip_code(
                "".join([c for c in cast(str, entity_dict["postal_code"]) if c != " "])
            ),
        )

    return list(map(entity_to_address, entities))


def process_text_file(fhandle: TextIO) -> list[AddressInformation]:
    total_contents = fhandle.read()

    # Addresses appear to be separated by one blank line, which means two
    # newline characters.
    blocks = total_contents.split("\n\n")

    def block_to_address(lines: list[str]) -> AddressInformation:

        # Do the basic amount of validation we can do on the text-block file
        if len(lines) < 3 or len(lines) > 4:
            raise ValueError(f"Invalid number of lines in block: {len(lines)}")

        # The final line is always the 'City, STate zip' line
        (city, state_zip) = lines[-1].split(",")
        state, zip = split_at_first_number(state_zip)

        return AddressInformation(
            # Blocks only seem to be people, not organizations, and there is no
            # principled way to differentiate between person names and
            # organiation names without added semantic information like in the
            # XML or TSV file so I'd rather not introduce unnecessary error into
            # the data if I haven't been told to
            name=lines[0],
            organization=None,
            street=lines[1],
            county=lines[2].upper() if len(lines) == 4 else None,
            city=city.strip(),
            state=state.strip(),
            zip=normalize_zip_code(zip.strip()),
        )

    return list(
        map(
            block_to_address,
            map(
                lambda b: [line.strip() for line in b.split("\n")],
                filter(lambda x: x != "", blocks),
            ),
        )
    )


####
## Main
####

if __name__ == "__main__":
    args = parser.parse_args()

    information: list[AddressInformation] = []
    for fhandle in args.files:
        _, ext = os.path.splitext(fhandle.name)
        match ext:
            case ".txt":
                information.extend(process_text_file(fhandle))
            case ".tsv":
                information.extend(process_tsv_file(fhandle))
            case ".xml":
                information.extend(process_xml_file(fhandle))
            case _:
                # NOTE: This should never be reached, as file extension validation
                # is performed at argument parse time, but nevertheless ---
                raise ValueError(
                    f'Invalid file extension: {fhandle.name.split(".")[-1]}'
                )

    information.sort(key=lambda adr: int("".join(c for c in adr.zip if c.isnumeric())))
    print(json.dumps([dataclasses.asdict(x) for x in information], indent=2))
