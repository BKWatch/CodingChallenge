import xml.etree.ElementTree as ET
import pandas as pd

def parse_xml_to_dataframe(xml_file):
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Initialize empty lists to store data
    data = {'name': [], 'company': [], 'street': [], 'city': [], 'state': [], 'country': [], 'postal_code': []}

    # Iterate through the elements and extract data
    for entity in root.findall('.//ENTITY/ENT'):
        name = entity.find('NAME').text.strip()
        company = entity.find('COMPANY').text.strip() if entity.find('COMPANY') is not None else ''
        street = entity.find('STREET').text.strip()
        city = entity.find('CITY').text.strip()
        state = entity.find('STATE').text.strip()
        country = entity.find('COUNTRY').text.strip()
        postal_code = entity.find('POSTAL_CODE').text.strip()
        
        # Append data to the dictionary
        data['name'].append(name)
        data['company'].append(company)
        data['street'].append(street)
        data['city'].append(city)
        data['state'].append(state)
        data['country'].append(country)
        data['postal_code'].append(postal_code)

    # Create DataFrame
    df = pd.DataFrame(data)
    return df

def main():
    xml_file_path = 'input/input1.xml'
    df = parse_xml_to_dataframe(xml_file_path)
    
    # Convert DataFrame to JSON
    json_data = df.to_json(orient='records', indent=2)
    print(json_data)

if __name__ == "__main__":
    main()