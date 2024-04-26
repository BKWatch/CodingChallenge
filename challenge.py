import xml.etree.ElementTree as et
import sys, re, csv, argparse, json

##############
# MODELS & CLASSES
##############
class Address():
    def __init__(self, data=None, **kwargs) -> None:
        if data is None:
            data = kwargs
        self.street = data.get("street").strip() if data.get("street") else None
        self.city = data.get("city").strip() if data.get("city") else None
        self.county = data.get("county").strip() if data.get("county") else None
        self.state = data.get("state").strip() if data.get("state") else None
        self.zip = data.get("zip")
        self.name = data.get("name")
        self.organization = data.get("organization")
    
    def view_dict(self) -> dict:
        raw_dict = {
            "name" : self.name,
            "organization" : self.organization,
            "street" : self.street,
            "city" : self.city,
            "county" : self.county,
            "state" : self.state,
            "zip" : self.zip,
        }
        return {k:v for k, v in raw_dict.items() if v}

class ParsingError(Exception):
    def __init__(self, message):
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(1)

##############
# PARSING
##############
class Parser():
    """
    Will determine file format and call relevent parser
    """

    BAD_NAMES = ["N/A", "N/M/N",]

    def parse_file(self, file_path: str) -> list[Address]:
        file_extension = file_path[-3:].lower()
        if file_extension == "txt":
            return self._parse_txt(file_path)
        if file_extension == "tsv":
            return self._parse_tsv(file_path)
        if file_extension == "xml":
            return self._parse_xml(file_path)

        raise ParsingError("Unhandled file extension - expecting txt, tsv, or xml")
    
    ### XML 
    def _parse_xml(self, file_path: str) -> list[Address]:
        """
        Parses an xml file and returns a list of Address objects
        based on the data in the file.

        Args:
        file_path (str): The path to the xml file.

        Returns:
        list: A list of Address objects.
        """
        try:
            tree = et.parse(file_path)
        except et.ParseError:
            raise ParsingError("Failed to load XML file. Check format & try again.")
        
        root = tree.getroot()
        entity_list = []

        for ent in root.findall(".//ENT"):
            name = ent.find("NAME").text.strip() if ent.find("NAME") is not None else None
            company = ent.find("COMPANY").text.strip() if ent.find("COMPANY") is not None else None
            street_1 = ent.find("STREET").text.strip() if ent.find("STREET") is not None else None
            street_2 = ent.find("STREET_2").text.strip() if ent.find("STREET_2") is not None else None
            street_3 = ent.find("STREET_3").text.strip() if ent.find("STREET_3") is not None else None
            street = street_1 + street_2 + street_3
            city = ent.find("CITY").text.strip() if ent.find("CITY") is not None else None
            county = ent.fine("COUNTY").text.strip() if ent.find("COUNTY") is not None else None
            state = ent.find("STATE").text.strip() if ent.find("STATE") is not None else None
            country = ent.find("COUNTRY").text.strip() if ent.find("COUNTRY") is not None else None
            postal_code = ent.find("POSTAL_CODE").text.strip() if ent.find("POSTAL_CODE") is not None else None

            data = {
                "name": name,
                "organization" : company,
                "street": street,
                "city": city,
                "county" : county,
                "state": state,
                "zip": self._parse_zip(postal_code),
                "country": country,
            }
            address = Address(data=data)
            entity_list.append(address)
        return entity_list
        
    ### TSV
    def _parse_tsv(self, file_path: str) -> list[Address]:
        """
        Parses a tsv file and returns a list of Address objects
        based on the data in the file.

        Args:
        file_path (str): The path to the tsv file.

        Returns:
        list: A list of Address objects.
        """
        entity_list = []
        with open(file_path, "r") as file:
            reader = csv.DictReader(file, delimiter="\t")
            
            for row in reader:
                first = row.get("first").strip() if row.get("first") else None
                middle = row.get("middle") if row.get("middle") else None
                last = row.get("last") if row.get("last") else None
                
                full_name = None
                if first and last:
                    full_name = " ".join([first, middle, last])

                # 'organization' row in source file is mostly misaligned
                organization = row.get("organization") if row.get("organization") else None
                if organization in self.BAD_NAMES:
                    organization = last

                zip5 = row.get("zip")
                zip4 = row.get("zip4")

                data = {
                    "name" : self._parse_name(full_name),
                    "organization": self._parse_name(organization),
                    "street": row.get("address"),
                    "city": row.get("city"),
                    "state": row.get("state"),
                    "county": row.get("county"),
                    "zip": self._parse_zip(f"{zip5}-{zip4}"),
                }
                
                address = Address(data=data)
                entity_list.append(address)
        return entity_list

    ### TXT
    def _parse_txt(self, file_path: str) -> list[Address]:
        """
        Parses a txt file and returns a list of Address objects
        based on the data in the file.

        Args:
        file_path (str): The path to the txt file.

        Returns:
        list: A list of Address objects and my tears.
        """
        entity_list = []
        
        with open(file_path, 'r') as file:
            data = file.read().strip().split('\n\n')
        
        for entry in data:
            lines = entry.split('\n')
            
            if len(lines) == 4:
                # Entry with 4 lines (includes county)
                name = lines[0]
                street = lines[1]
                county = lines[2]
                city_state_zip = lines[3]
            elif len(lines) == 3:
                # Entry with 3 lines (does not include county)
                name = lines[0]
                street = lines[1]
                city_state_zip = lines[2]
                county = None
            else:
                raise ParsingError("Failed to parse txt file. Check format & try again.")
            
            city_state_zip_split = city_state_zip.split(',')
            city = city_state_zip_split[0].strip()
            state_zip_split = city_state_zip_split[1].strip().rsplit(' ', 1)
            state = state_zip_split[0]
            postal_code = state_zip_split[1]
            
            data = {
                'name': self._parse_name(name),
                'street': street,
                'county': county,
                'city': city,
                'state': state,
                'zip': self._parse_zip(postal_code)
            }
            
            # Create a Person object and add it to the list
            address = Address(data=data)
            entity_list.append(address)
        
        return entity_list

    ### UTILITIES
    def _parse_zip(self, zip: str) -> str | None:
        if zip is None:
            return None
        zip = zip.strip()
        # 00000-0000 format
        pattern = r"^\d{5}-\d{4}$"
        if re.match(pattern, zip):
            return zip
        # 00000 format
        if zip[:5].isdigit():
            return zip[:5]
        # uh oh
        raise ParsingError(f"Unable to parse zip code: {zip}")
    
    def _parse_name(self, name: str) -> str | None:
        #TODO: maybe take another pass at this
        if not name or name in self.BAD_NAMES:
            return None
        scrubbed_name = []
        for n in name.split(" "):
            n = n.strip()
            if n and not n in self.BAD_NAMES:
                scrubbed_name.append(n)
        return " ".join(scrubbed_name)

##############
# APP
##############

def main():
    """
    Hello, world!
    """
    arg_parser = argparse.ArgumentParser(
        description="Parse files in XML, TSV, or TXT format and print them as json.",
        epilog = "Example usage: python challenge.py ./path/to/file.xml ./path/to/file.tsv",
    )
    arg_parser.add_argument("files", nargs="+", help="List of file paths to parse.")
    
    args = arg_parser.parse_args()

    file_parser = Parser()
    
    entities = []
    for file_path in args.files:
        entities += file_parser.parse_file(file_path)

    cli_print(entities)
    sys.exit(0)

def cli_print(entities: list[Address]) -> None:
    """
    Pretty print a list of Address objects
    """
    print(json.dumps(entities, default=lambda obj: obj.view_dict(), indent=4))

if __name__ == "__main__":
    main()