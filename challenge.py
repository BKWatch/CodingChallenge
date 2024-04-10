import json
import sys
import argparse
import csv
import xml.etree.ElementTree as ET

def process_xml(filepath):
	try:
		with open(filepath, 'r') as f:
			data = f.read()
	except Exception as e:
		sys.stderr.write(f"error reading xml file: {e}\n")
		sys.exit(1)

	try:
		root = ET.fromstring(data)
	except ET.ParseError as e:
		sys.stderr.write(f"error parsing xml: {e}\n")
		sys.exit(1)

	results = []
	for entity in root.findall('ENTITY/ENT'):
		entry = {}
		name = entity.find('NAME').text.strip()
		company = entity.find('COMPANY').text.strip()
		street = entity.find('STREET').text.strip()
		city = entity.find('CITY').text.strip()
		state = entity.find('STATE').text.strip()

		postal_code_parts = entity.find('POSTAL_CODE').text.strip().split(' ')
		postal_code = postal_code_parts[0]
		if len(postal_code_parts) == 3:
			postal_code = f"{postal_code_parts[0]}-{postal_code_parts[2]}"

		if name:
			entry['name'] = name
		elif company:
			entry['company'] = company

		entry['street'] = street
		entry['city'] = city
		entry['state'] = state
		entry['zip'] = postal_code
		results.append(entry)

	return results

def process_tsv(filepath):
	try:
		with open(filepath, 'r', newline='') as file:
			reader = csv.DictReader(file, delimiter='\t')
	except Exception as e:
		sys.stderr.write(f"Error reading TSV file: {e}\n")
		sys.exit(1)

	results = []
	with open(filepath, 'r', newline='') as file:
		reader = csv.DictReader(file, delimiter='\t')
		for row in reader:
			entry = {}

			if row['organization'] != 'N/A':
				entry['organization'] = row['organization']
			else:
				entry['name'] = ' '.join(filter(lambda x: x not in [None, 'N/A', 'N/M/N'], [row['first'], row['middle'], row['last']]))

			entry['street'] = row['address']
			entry['city'] = row['city']
			entry['state'] = row['state']

			if row['county']:
				entry['county'] = row['county']

			entry['zip'] = f"{row['zip'].strip()}-{row['zip4'].strip()}" if row['zip4'] else row['zip'].strip()

			entry = {k: v.strip() for k, v in entry.items() if v}
			results.append(entry)

	return results

def process_txt(file_path):
	try:
		with open(file_path, 'r') as file:
			content = file.read().strip()
	except Exception as e:
		sys.stderr.write(f"error reading txt file: {e}\n")
		sys.exit(1)

	results = []
	address_blocks = content.split('\n\n')
	for block in address_blocks:
		lines = block.split('\n')
		entry = {}

		entry['name'] = lines[0].strip()
		entry['street'] = lines[1].strip()

		if 'COUNTY' in lines[2].upper():
			entry['county'] = lines[2].strip()
			city_state_zip = lines[3]
		else:
			city_state_zip = lines[2]

		parts = city_state_zip.strip().split(' ')
		entry['state'] = parts[-2].replace(',', '')
		entry['city'] = ' '.join(parts[:-2]).replace(',', '')

		entry['zip'] = parts[-1]
		if entry['zip'].endswith('-'):
			entry['zip'] = entry['zip'][:-1]
		if '-' in entry['zip'] and len(entry['zip'].split('-')[1]) != 4:
			entry['zip'] = entry['zip'].split('-')[0]
		results.append(entry)

	return results

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='process an address file.')
	parser.add_argument('filepath', type=str, help='path to the input file.')
	args = parser.parse_args()

	filepath = args.filepath
	ext = filepath.split('.')[-1]

	processing_map = {
		'xml': process_xml,
		'tsv': process_tsv,
		'txt': process_txt
	}

	if ext not in processing_map:
		sys.stderr.write(f"unsupported file extension: {ext}\n")
		sys.exit(1)

	try:
		processing_func = processing_map[ext]
		results = processing_func(filepath)
		print(json.dumps(results, indent=4))
		sys.exit(0)
	except Exception as e:
		sys.stderr.write(f"error processing file: {e}\n")
		sys.exit(1)