import argparse
import csv
import xml.etree.ElementTree as ET

def parse_xml(file_path):
  try:
    tree = ET.parse(file_path)
    root = tree.getroot()
    addresses = []

    for ent in root.findall('.//ENT'):
        address = {}
        name = ent.find('NAME').text.strip()
        company = ent.find('COMPANY').text.strip()
        street = ent.find('STREET').text.strip()
        city = ent.find('CITY').text.strip()
        state = ent.find('STATE').text.strip()
        zip = ent.find('POSTAL_CODE').text.split("-")
        if zip[1]==" ":
            zip_code = zip[0].strip()
        else:
            zip_code = zip[0].strip()+"-"+zip[1].strip()        

        if name:
            address['name'] = name
        else:
            address['organization'] = company

        address['street'] = street
        address['city'] = city
        address['state'] = state
        address['zip'] = zip_code
        addresses.append(address)

    return addresses
  except Exception as e:
        print(f"Error parsing TXT file '{file_path}': {str(e)}", file=sys.stderr)
        sys.exit(1)

def parse_tsv(file_path):
  try:
    addresses = []

    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            address = {}
            name = ' '.join([row['first'], row['middle'], row['last']]).strip()
            organization = row['organization'].strip()
            street = row['address'].strip()
            city = row['city'].strip()
            state = row['state'].strip()
            zip_code = row['zip'].strip()

            if name:
                address['name'] = name
            else:
                address['organization'] = organization

            address['street'] = street
            address['city'] = city
            address['state'] = state
            address['zip'] = zip_code
            addresses.append(address)

    return addresses
  except Exception as e:
        print(f"Error parsing TXT file '{file_path}': {str(e)}", file=sys.stderr)
        sys.exit(1)

def parse_txt(file_path):
  try:
    addresses = []
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = [line for line in file.readlines()]
        i=0
        l=[]
        while(i!=(len(lines))):
            address = {}
            if lines[i]!='\n':
               l.append(lines[i])
               i=i+1
            else:
               i=i+1
               if len(l)==3:
                name_org = l[0]
                street = l[1]
                city_state_zip = l[2]
                l=[]
                address['name'] = name_org.strip()
                address['street'] = street.strip()
                address['city'] = city_state_zip.split(",")[-2].strip()
                address['state'] = city_state_zip.split(",")[-1].split(" ")[-2].strip()
                zip = city_state_zip.split(",")[-1].split(" ")[-1].strip().split("-")
                if len(zip)==2:
                   if zip[1]=="":
                      address['zip'] = zip[0].strip()
                   else:
                      address['zip'] = zip[0].strip()+"-"+zip[1].strip() 
                else:
                   address['zip'] = zip[0].strip("-")       
                addresses.append(address)
               if len(l)==4:
                name_org = l[0]
                street = l[1]
                city_state_zip = l[3]
                address['name'] = name_org.strip()
                address['street'] = street.strip()
                address['city'] = city_state_zip.split(",")[-2].strip()
                address['county'] = l[2].strip()
                address['state'] = city_state_zip.split(",")[-1].split(" ")[-2].strip()
                zip = city_state_zip.split(",")[-1].split(" ")[-1].strip().split("-")
                if len(zip)==2:
                   if zip[1]=="":
                      address['zip'] = zip[0].strip()
                   else:
                      address['zip'] = zip[0].strip()+"-"+zip[1].strip()   
                else:
                   address['zip'] = zip[0].strip("-")
                l=[]
                addresses.append(address)

    return addresses
  except Exception as e:
        print(f"Error parsing TXT file '{file_path}': {str(e)}", file=sys.stderr)
        sys.exit(1)

def merge_addresses(files):
    addresses = []
    for file_path in files:
        if file_path.endswith('.xml'):
            addresses.extend(parse_xml(file_path))
        elif file_path.endswith('.tsv'):
            addresses.extend(parse_tsv(file_path))
        elif file_path.endswith('.txt'):
            addresses.extend(parse_txt(file_path))
    return addresses

def sort_by_zip(addresses):
    return sorted(addresses, key=lambda x: x['zip'])

def main():
    parser = argparse.ArgumentParser(description='Parse and merge address files')
    parser.add_argument('files', metavar='file', type=str, nargs='+',
                        help='list of file paths to parse and merge')
    args = parser.parse_args()

    merged_addresses = merge_addresses(args.files)
    sorted_addresses = sort_by_zip(merged_addresses)

    import json
    print(json.dumps(sorted_addresses, indent=2))

if __name__ == "__main__":
    main()
