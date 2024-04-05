import sys
import json
import os

def parse_txtfile(file_path):
    """
    Parse TXT file and extract address information.

    Args:
        file_path (str): Path to the TXT file.

    Returns:
        list: List of dictionaries containing address information.
    """
    
    try:
        addresses = []

        with open(file_path) as f:
            data = f.read()
        
        text_list = data.split('\n\n')[1:-1]
        
        for i in text_list:
            sub = i.split("\n")
            no_elements = len(sub)
            
            for j in sub:
                if no_elements == 4:
                    # Extracting data for entries with 4 elements
                    name = sub[0].strip()
                    street = sub[1].strip()
                    county = sub[2].strip()
                    info = sub[3].split(",")
                    city = info[0].strip()
                    info2 = info[1].split(" ")
                    state = ""
                    zip_ = ""
                    
                    for k in info2:
                        if k and k.isalpha():
                            state += k + " "
                        elif k and k[0].isdigit():
                            zip_ += k
                        else:
                            continue
                    state = state.strip()
                    zip_ = zip_.strip()
                    
                    temp_dict = {
                        'name': name,
                        'street': street,
                        'city': city,
                        'county': county,
                        'state': state,
                        'zip': zip_
                    }
        
                else:
                    # Extracting data for entries with less than 4 elements
                    name2 = sub[0].strip()
                    street2 = sub[1].strip()
                    info2 = sub[2].split(",")
                    city2 = info2[0].strip()
                    info3 = info2[1].split(" ")
                    state2 = ""
                    zip_2 = ""
                    
                    for k in info3:
                        if k and k.isalpha():
                            state2 += k + " "
                        elif k and k[0].isdigit():
                            zip_2 += k
                        else:
                            continue
                    state2 = state2.strip()
                    zip_2 = zip_2.strip()
                    
                    temp_dict = {
                        'name': name2,
                        'street': street2,
                        'city': city2,
                        'state': state2,
                        'zip': zip_2
                    }
            addresses.append(temp_dict)
        
        # Sorting by zip code
        sorted_data = sorted(addresses, key=lambda item: item['zip'].rstrip('-'))
        
        # Convert addresses to JSON string
        json_data = json.dumps(sorted_data, indent=2)
        return json_data
    
    except Exception as e:
        print(f"Error parsing TXT file: {file_path}. {e}", file=sys.stderr)
        sys.exit(1)