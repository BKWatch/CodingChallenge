import re
import sys

def parse_txt(filepath):
    address_book = []
    organizations = set(["llc", "inc.", "pvt.", "ltd."])
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            lines = [line.strip() for line in file if line.strip()]
        
        index = 0
        while index < len(lines):
            address_entry = {}
            current_line = lines[index]

            if any(keyword in current_line.lower() for keyword in organizations):
                address_entry["organization"] = current_line
            else:
                address_entry["name"] = current_line

            address_entry["street"] = lines[index + 1]

            # Check if the next line is the county or city/state
            if "," in lines[index + 2]:  # It's city and state
                city_state = lines[index + 2].split(", ")
                index += 3
            else:  # It's county
                address_entry["county"] = lines[index + 2]
                city_state = lines[index + 3].split(", ")
                index += 4

            address_entry["city"] = city_state[0]

            # Regex to extract state and ZIP code
            state_zip_pattern = r"([A-Za-z\s]+),?\s*(\d{5}(?:-\d{4})?)"
            state_zip_match = re.search(state_zip_pattern, city_state[1])
            if state_zip_match:
                address_entry["state"] = state_zip_match.group(1).strip()
                address_entry["zip"] = state_zip_match.group(2).strip()

            address_book.append(address_entry)

    except Exception as error:
        sys.stderr.write(f"Error while parsing text file {filepath}: {error}\n")
        sys.exit(1)

    return address_book
