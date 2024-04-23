"""
A python script which reads a list of files in different formats (i.e. XML, TSV, and TXT), then transforms and
concatenates them into a single JSON array.
"""

import os
import sys
import argparse
from typing import List, Dict, Tuple, Union

import xml.etree.ElementTree as ET
import csv
import json


def is_valid_file(file_path: str) -> bool:
    """
    Check if the given file path is a valid file.

    :param file_path: The path to the file.
    :return: True if the file is valid, False otherwise.
    """
    if not os.path.isfile(file_path):
        sys.stderr.write(f'Error: {file_path} is not a valid file.\n')
        return False
    return True


def format_zip_code(zip_code: str, zip_4: str) -> str:
    """
    Format the ZIP code based on the presence of ZIP+4.

    :param zip_code: The 5-digit ZIP code.
    :param zip_4: The 4-digit ZIP+4 extension.
    :return: The formatted ZIP code.
    """
    return f'{zip_code}-{zip_4}' if zip_4 else zip_code


def check_xml_root(context: ET.iterparse, file_path: str) -> None:
    """
    Check if the XML file has the expected root element.

    :param context: The iterparse context for XML parsing.
    :param file_path: The path to the XML file.
    :raises ValueError: If the root element is not 'EXPORT'.
    """
    _, root = next(context)
    if root.tag != 'EXPORT':
        raise ValueError(f'Error: {file_path} does not have the expected root element')


def check_xml_meta_and_entity(event: str, elem: ET.Element, file_path: str) -> None:
    """
    Check if the XML elements 'META' and 'ENTITY' have the expected events.

    :param event: The event type ('start' or 'end').
    :param elem: The XML element.
    :param file_path: The path to the XML file.
    :raises ValueError: If the event for 'META' or 'ENTITY' is not as expected.
    """
    expected_events = {
        'META': 'start',
        '/META': 'end',
        'ENTITY': 'start',
        '/ENTITY': 'end'
    }
    if elem.tag in expected_events:
        if event != expected_events[elem.tag]:
            if event == 'end' and elem.tag in {'META', 'ENTITY'} and elem.text is None:
                return
            if event != expected_events[elem.tag]:
                raise ValueError(
                    f'Error: {file_path} - Expected {expected_events[elem.tag]} event for {elem.tag} element,'
                    f'but got {event}.')


def handle_xml_ent_zip(ent_dict: Dict[str, str], key: str, value: str) -> None:
    """
    Handle the ZIP code element within the 'ENT' element.

    :param ent_dict: The dictionary to store the parsed 'ENT' data.
    :param key: The key of the element.
    :param value: The value of the element.
    :raises ValueError: If the postal code format is invalid.
    """
    try:
        zip_code, zip_4 = value.replace(' ', '').split('-', maxsplit=1)
        ent_dict['zip'] = format_zip_code(zip_code, zip_4)
    except ValueError as e:
        raise ValueError(f'Invalid postal code format: {value}') from e


def handle_xml_ent_streets(ent_dict: Dict[str, str], key: str, value: str) -> None:
    """
    Handle the street elements within the 'ENT' element.

    :param ent_dict: The dictionary to store the parsed 'ENT' data.
    :param key: The key of the element.
    :param value: The value of the element.
    """
    if value != '':
        if 'street' in ent_dict:
            ent_dict['street'] += f', {value}'
        else:
            ent_dict['street'] = value


def handle_xml_ent_elem(ent_dict: Dict[str, str], elem: ET.Element) -> None:
    """
    Handle the 'ENT' element within the XML file.

    :param ent_dict: The dictionary to store the parsed 'ENT' data.
    :param elem: The 'ENT' element.
    :raises ValueError: If an unexpected element is found or a required element is missing or empty.
    """
    required_elements = ['NAME', 'COMPANY', 'STREET', 'STREET_2', 'STREET_3', 'CITY', 'STATE', 'COUNTRY', 'POSTAL_CODE']

    key = elem.tag.lower()
    value = elem.text.strip().title() if elem.text else ''
    if value.strip():
        if key == 'postal_code':
            handle_xml_ent_zip(ent_dict=ent_dict, key=key, value=value)
        elif key == 'street_2' or key == 'street_3':
            handle_xml_ent_streets(ent_dict=ent_dict, key=key, value=value)
        elif key == 'state':
            if len(value) == 2:
                ent_dict[key] = value.upper()
            else:
                ent_dict[key] = value.strip()
        elif key == 'company':
            ent_dict['organization'] = value
        elif key != 'country' and value:
            ent_dict[key] = value


def handle_xml(file_path: str, data: List[Dict[str, str]]) -> bool:
    """
    Handle the XML file and extract the required data.

    :param file_path: The path to the XML file.
    :param data: The list to store the extracted data.
    :return: True if the XML file is processed successfully, False otherwise.
    """
    try:
        context = ET.iterparse(file_path, events=('start', 'end'))
        check_xml_root(context=context, file_path=file_path)

        ent_dict = None
        for event, elem in context:
            check_xml_meta_and_entity(event, elem, file_path)

            if elem.tag == 'ENT':
                if event == 'start':
                    ent_dict = {}
                else:
                    data.append(ent_dict)
                    ent_dict = None

            if ent_dict is not None:
                handle_xml_ent_elem(ent_dict, elem)

            elem.clear()
    except (ET.ParseError, ValueError) as e:
        if isinstance(e, ET.ParseError):
            line_number, column_number = e.position
            error_message = f'Error: {file_path} is not a well-formed XML file.' \
                            f'\nParsing error at line {line_number},column {column_number}: {str(e)}\n'
        else:
            error_message = str(e)

        sys.stderr.write(error_message)
        sys.exit(0)


def get_tsv_name(first: str, middle: str, last: str) -> str:
    """
    Get the formatted name from the TSV file.

    :param first: The first name.
    :param middle: The middle name.
    :param last: The last name.
    :return: The formatted name.
    """
    return f'{first} {last}'.title() if middle == 'N/M/N' else f'{first} {middle} {last}'.title()


def check_tsv_column_length(line: List[str], file_path: str) -> None:
    """
    Check if the TSV line has the expected number of columns.

    :param line: The TSV line as a list of columns.
    :param file_path: The path to the TSV file.
    :raises ValueError: If the TSV line does not have the expected number of columns.
    """
    if len(line) != 10:
        raise ValueError(f'Error: {file_path} does not have the expected TSV format.')


def handle_tsv(file_path: str, data: List[Dict[str, str]]) -> None:
    """
    Handle the TSV file and extract the required data.

    :param file_path: The path to the TSV file.
    :param data: The list to store the extracted data.
    """
    try:
        with open(file_path, encoding='latin1') as file:
            tsv_file = csv.reader(file, delimiter='\t')
            header = next(tsv_file)
            check_tsv_column_length(header, file_path=file_path)

            for line in tsv_file:
                check_tsv_column_length(line, file_path=file_path)
                line_dict = {}
                first, middle, last, org, street, city, state, county, zip_code, zip_4 = map(str.strip, line)

                if first:
                    line_dict['name'] = get_tsv_name(first, middle, last)

                if (last and not first) or (org != 'N/A'):  # handles if organization name is in wrong column
                    line_dict['organization'] = last if last else org
                if 'name' not in line_dict and 'organization' not in line_dict:
                    raise ValueError(f'Error: {file_path} has entity with missing name and organization.')

                line_dict['street'] = street
                line_dict['city'] = city

                if county:
                    line_dict['county'] = county

                line_dict['state'] = state
                if not zip_code or not zip_code.isdigit() or len(zip_code) != 5:
                    raise ValueError(f'Error: {file_path} has an invalid ZIP code: {zip_code}')
                line_dict['zip'] = format_zip_code(zip_code, zip_4)

                data.append(line_dict)
    except (ValueError, IOError) as e:
        sys.stderr.write(str(e) + '\n')
        sys.exit(0)


def validate_txt_dict(txt_dict: Dict[str, str], required_fields: List[str], file_path: str) -> bool:
    """
    Validate the dictionary extracted from the TXT file.

    :param txt_dict: The dictionary to validate.
    :param required_fields: The list of required fields.
    :param file_path: The path to the TXT file.
    :return: True if the dictionary is valid, False otherwise.
    :raises ValueError: If the dictionary is missing required fields.
    """
    if 'name' not in txt_dict and 'organization' not in txt_dict:
        raise ValueError(f"Error: {file_path} has a record with missing name and organization.")
    for field in required_fields:
        if field not in txt_dict:
            raise ValueError(f"Error: {file_path} has a record with missing {field}.")
    return True


def handle_txt(file_path: str, data: List[Dict[str, str]]) -> None:
    """
    Handle the TXT file and extract the required data.

    :param file_path: The path to the TXT file.
    :param data: The list to store the extracted data.
    """
    required_fields = ['street', 'city', 'state', 'zip']

    try:
        with open(file_path, encoding='latin1') as file:
            txt_dict = {}
            for line in file:
                line = line.strip().lower()  # normalize line
                if not line:
                    if txt_dict:
                        validate_txt_dict(txt_dict, required_fields=required_fields, file_path=file_path)
                        data.append(txt_dict)
                        txt_dict = {}
                elif line[0].isdigit() or line.startswith('p.o.'):
                    txt_dict['street'] = line.title()
                elif 'county' in line:
                    txt_dict['county'] = line.title().rstrip(' county')
                elif line[-1].isdigit() or line[-1] == '-':
                    city, state_and_zip = line.split(',')
                    state, zip_code = state_and_zip.rsplit(maxsplit=1)
                    try:
                        zip_code, zip_4 = zip_code.split('-')
                    except ValueError:
                        zip_4 = None

                    txt_dict.update({
                        'city': city.title(),
                        'state': state.strip().upper() if len(state.strip()) == 2 else state.strip().title(),
                        'zip': format_zip_code(zip_code, zip_4)
                    })
                else:
                    txt_dict['name'] = line.title()

            if txt_dict:
                validate_txt_dict(txt_dict, required_fields=required_fields, file_path=file_path)
                data.append(txt_dict)
    except (ValueError, IOError) as e:
        sys.stderr.write(str(e) + '\n')
        sys.exit(0)


def get_zip(data_dict: Dict[str, str]) -> str:
    """
    Get the ZIP code from the data dictionary.

    :param data_dict: The data dictionary.
    :return: The ZIP code.
    """
    return data_dict['zip']


def main() -> None:
    """
    The main function that orchestrates the execution of the script.
    """
    parser = argparse.ArgumentParser(
        prog='BKWatch Coding Challenge',
        description='Reads files in XML, TSV, and TXT formats,'
                    'transforms and concatenates them into a single JSON array.'
    )
    input_dir = 'input'
    data = []

    for file_name in os.listdir(input_dir):
        file_path = os.path.join(input_dir, file_name)
        if file_name.endswith('.xml'):
            handle_xml(file_path, data)
        elif file_name.endswith('.tsv'):
            handle_tsv(file_path, data)
        elif file_name.endswith('.txt'):
            handle_txt(file_path, data)
        else:
            _, extension = os.path.splitext(file_name)
            sys.stderr.write(f'Error: {extension} files not supported.\n')
            sys.exit(0)

    data.sort(reverse=True, key=lambda data_dict: data_dict['zip'])
    json.dump(data, sys.stdout, indent=4)
    sys.exit(1)


if __name__ == '__main__':
    main()
