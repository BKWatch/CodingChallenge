import xml.etree.ElementTree as ET
import sys

class XMLParser:
    @staticmethod
    def parse(file_path):
        addresses = []
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            for entry in root.findall('.//ENTITY/ENT'):
                address = {}
                for child in entry:
                    if child.tag == 'NAME':
                        address['name'] = child.text.strip()
                    elif child.tag == 'COMPANY':
                        address['organization'] = child.text.strip()
                    elif child.tag == 'STREET':
                        address['street'] = child.text.strip()
                    elif child.tag == 'STREET_2':
                        address['street'] += child.text.strip()
                    elif child.tag == 'street_3':
                        address['street'] += child.text.strip()
                    elif child.tag == 'CITY':
                        address['city'] = child.text.strip()
                    elif child.tag == 'COUNTRY':
                        address['county'] = child.text.strip()
                    elif child.tag == 'STATE':
                        address['state'] = child.text.strip()
                    elif child.tag == 'POSTAL_CODE':
                        postal_code = child.text.strip()

                        if postal_code.endswith('-'):
                            postal_code = postal_code[:-1]

                        address['zip'] = postal_code.strip()
                addresses.append(address)
        except ET.ParseError as e:
            sys.stderr.write(f"Error parsing XML file {file_path}: {str(e)}\n")
            sys.exit(1)
        return addresses
