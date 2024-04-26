import json

# Function to parse the source text file and convert it to JSON
def text_to_json(file_path):
    # Initialize variables to store data
    data = []
    current_entry = {}

    # Read the source text file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Function to reset current entry
    def reset_entry():
        nonlocal current_entry
        current_entry = {}

    # Iterate through lines to parse data
    for line in lines:
        line = line.strip()
        if line:  # If line is not empty
            if len(current_entry) == 0:
                current_entry['name'] = line
            else:
                if 'street' not in current_entry:
                    current_entry['street'] = line
                elif 'city' not in current_entry:
                    current_entry['city'] = line
                elif 'state' not in current_entry:
                    current_entry['state'] = line
                elif 'zip' not in current_entry:
                    current_entry['zip'] = line
        else:  # If line is empty, it indicates end of entry
            data.append(current_entry)
            reset_entry()

    # Append last entry
    if current_entry:
        data.append(current_entry)

    # Convert data to JSON
    json_data = json.dumps(data, indent=2)
    return json_data

# Main function
def main():
    file_path = 'input/input3.txt'
    json_data = text_to_json(file_path)
    print(json_data)

if __name__ == "__main__":
    main()