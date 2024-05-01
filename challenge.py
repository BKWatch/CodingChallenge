from pathlib import Path
import xml.etree.ElementTree as ET
import json
import csv
import re
from argparse import ArgumentParser
import sys


class ProcessError(Exception):
    """
    Custom Exception Class
    """
    pass


class FileProcessorBase:
    """
    Base class for file processors
    """

    extension = None

    def __init__(self, filename: str):
        file = Path(filename)
        if not file.is_file():
            raise ProcessError(f"File not found: {filename}")
        self.filename = filename

    def process(self) -> list[dict]:
        raise NotImplementedError

    @staticmethod
    def _strip_list(data: list[str]) -> list[str]:
        """
        Apply strip() to each element of the list
        """
        return list(map(str.strip, data))

    @staticmethod
    def _parse_address(address: str) -> list[str]:
        """
        Parse address like "Des Plaines, IL 60018-1715"
        """
        res = re.findall("(.*?)\,\s+(.*)\s(\d+\-?\d+)", address)[0]
        if len(res) != 3:
            print(res)
            raise ProcessError(f"Wrong address format: {address}")
        return res

    @staticmethod
    def _normalize_zip(zip_code: str) -> str:
        """
        Remove spaces, strip trailing "-"
        """
        zip_code = zip_code.replace(" ", "")
        if zip_code[-1] == "-":
            zip_code = zip_code[:-1]
        return zip_code


class XMLFileProcessor(FileProcessorBase):
    extension = ".xml"

    def process(self) -> list[dict]:
        result = []
        root = ET.parse(self.filename).getroot()
        for ent in root.findall("./ENTITY/ENT"):
            item = {}
            for child in ent:
                item[child.tag.lower()] = child.text.strip()

            item = self.validate_item(item)
            result.append(item)
        return result

    def validate_item(self, item: dict):
        res = {}
        if item.get("name"):
            res["name"] = item["name"]
        else:
            if item.get("company"):
                res["organization"] = item["company"].replace("&amp;", "&")
            else:
                raise ProcessError(
                    f"Wrong record format: {item}. A personal name or organization name should be present"
                )
        try:
            res["street"] = item["street"]
            res["city"] = item["city"]
            res["county"] = item.get("county", "")
            res["state"] = item["state"]
            res["zip"] = FileProcessorBase._normalize_zip(item["postal_code"])
        except KeyError as e:
            raise ProcessError(f"Wrong record format: {item}. Missing {str(e)} key")

        return res


class TSVFileProcessor(FileProcessorBase):
    extension = ".tsv"

    def process(self) -> list[dict]:
        result = []
        with open(self.filename) as f:
            tsv_file = csv.reader(f, delimiter="\t")
            header = FileProcessorBase._strip_list(next(tsv_file))
            for row in tsv_file:
                row = FileProcessorBase._strip_list(row)
                item = dict(zip(header, row))
                item = self.validate_item(item)
                result.append(item)
        return result

    def validate_item(self, item: dict):
        res = {}
        # special case: some records in input2.tsv have last name instead of organization
        if (
            not item["first"]
            and not item["middle"]
            and item["last"]
            and item["organization"] == "N/A"
        ):
            item["organization"] = item["last"]
            item["last"] = ""

        full_name = FileProcessorBase._strip_list(
            [item["first"], item["middle"], item["last"]]
        )
        if item["organization"] == "N/A":
            if all(i == "" for i in full_name):
                raise ProcessError(
                    f"Wrong record format: {item}. A personal name or organization name should be present"
                )
            res["name"] = " ".join(full_name)
        else:
            res["organization"] = item["organization"]

        res["street"] = item["address"]
        res["city"] = item["city"]
        res["county"] = item["county"]
        res["state"] = item["state"]
        res["zip"] = FileProcessorBase._normalize_zip(f"{item['zip']} - {item['zip4']}")

        return res


class TXTFileProcessor(FileProcessorBase):
    extension = ".txt"

    def process(self) -> list[dict]:
        result = []
        with open(self.filename) as f:
            item = []
            for line in f:
                line = line.strip()
                if line == "":
                    if not item:
                        continue
                    item = self.validate_item(item)
                    result.append(item)
                    item = []
                else:
                    item.append(line)

        return result

    def validate_item(self, item: list[str]):
        city, state, zip_code = FileProcessorBase._parse_address(item[-1])
        if len(item) not in (3, 4):
            raise ProcessError(f"Wrong record format: {item}")

        if len(item) == 4:
            return {
                "name": item[0],
                "street": item[1],
                "city": city,
                "county": item[2],
                "state": state,
                "zip": FileProcessorBase._normalize_zip(zip_code),
            }
        return {
            "name": item[0],
            "street": item[1],
            "city": city,
            "state": state,
            "zip": FileProcessorBase._normalize_zip(zip_code),
        }


file_processors = [XMLFileProcessor, TSVFileProcessor, TXTFileProcessor]


def process_file(filename: str) -> list[dict]:
    extenstion = Path(filename).suffix
    result = []
    for file_processor in file_processors:
        if file_processor.extension == extenstion:
            processor = file_processor(filename)
            result = processor.process()
            break
    else:
        raise ProcessError(f"Unknown file format: {extenstion}")

    return result


def main(filenames: list[str]):
    result = []
    for filename in filenames:
        res = process_file(filename)
        result.extend(res)

    result.sort(key=lambda x: x["zip"])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Parse files and print results sorted by ZIP code "
    )
    parser.add_argument("filenames", nargs="+", help="list of input files")
    args = parser.parse_args()
    try:
        main(args.filenames)
        sys.exit(0)
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
