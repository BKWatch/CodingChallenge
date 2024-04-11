# Furkhan Mehdi Syed 
# Testing all the defined function from challenge.py with expected output

import unittest
from unittest.mock import patch, mock_open
from challenge import parse_xml_file, parse_tsv_file, parse_txt_file, validate_addresses, sort_addresses_by_zip, parse_files
import xml.etree.ElementTree as ET

class Testchallenge(unittest.TestCase):

    def test_parse_xml_file(self):
        xml_content = '''<root>
            <person>
                <name>John Doe</name>
                <street>123 Elm Street</street>
                <city>Springfield</city>
                <county>Hampden</county>
                <state>MA</state>
                <zip>01103</zip>
            </person>
        </root>'''
        with patch("xml.etree.ElementTree.parse") as mocked_parse:
            mocked_parse.return_value = ET.ElementTree(ET.fromstring(xml_content))
            result = parse_xml_file("dummy_path")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['name'], 'John Doe')

    def test_parse_tsv_file(self):
        tsv_content = "name\torganization\tstreet\tcity\tstate\tzip\nJohn Doe\t-\t123 Elm Street\tSpringfield\tMA\t01103"
        with patch("builtins.open", mock_open(read_data=tsv_content)):
            result = parse_tsv_file("dummy_path.tsv")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['name'], 'John Doe')

    def test_parse_txt_file(self):
        txt_content = "John Doe,123 Elm Street,Springfield,Hampden,MA,01103\n"
        with patch("builtins.open", mock_open(read_data=txt_content)):
            result = parse_txt_file("dummy_path.txt")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['name'], 'John Doe')

    def test_validate_addresses(self):
        addresses = [{'name': 'John Doe', 'street': '123 Elm Street', 'city': 'Springfield', 'state': 'MA', 'zip': '01103'}]
        self.assertTrue(validate_addresses(addresses))

    def test_sort_addresses_by_zip(self):
        addresses = [{'name': 'John Doe', 'zip': '01104'}, {'name': 'Jane Doe', 'zip': '01103'}]
        sorted_addresses = sort_addresses_by_zip(addresses)
        self.assertEqual(sorted_addresses[0]['name'], 'Jane Doe')

    def test_parse_files_unsupported_format(self):
        with self.assertRaises(ValueError) as context:
            parse_files(['dummy_path.unsupported'])
        self.assertTrue('Unsupported file format' in str(context.exception))

if __name__ == '__main__':
    unittest.main()
