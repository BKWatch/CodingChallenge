import sys

class TextParser:
    @staticmethod
    def parse(file_path):
        with open(file_path, 'r') as file:
            addresses = file.readlines()
        parsed_addresses = []
        address_lines = []
        for line in addresses:
            if line.strip():
                address_lines.append(line.strip())
            else:
                if address_lines:
                    parsed_address = TextParser.parse_address(address_lines)
                    parsed_addresses.append(parsed_address)
                    address_lines = []
        if address_lines:
            parsed_address = TextParser.parse_address(address_lines)
            parsed_addresses.append(parsed_address)
        return parsed_addresses

    @staticmethod
    def parse_address(address_lines):
        first_line = address_lines[0].lower()
        keywords = ['llc', 'ltd', 'inc']
        if any(keyword in first_line for keyword in keywords):
            organization = address_lines[0]
            name = ''
        else:
            organization = ''
            name = address_lines[0]

        street = address_lines[1]
        second_last_line = address_lines[-2]
        county = second_last_line.strip() if 'COUNTY' in second_last_line else ''

        last_line_parts = address_lines[-1].split(', ')
        city_state_zip_parts = last_line_parts[-1].split(' ')
        city = last_line_parts[0]
        state = city_state_zip_parts[-2]
        zip_code = city_state_zip_parts[-1]

        return {
            'name': name.strip(),
            'organization': organization.strip(),
            'street': street.strip(),
            'city': city.strip(),
            'county': county.strip(),
            'state': state.strip(),
            'zip': zip_code.strip()
        }
