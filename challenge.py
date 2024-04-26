import json
import sys
import argparse
import csv
import xml.etree.ElementTree as ET


def process_xml(filepath: str) -> list:
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
			entry['organization'] = company

		entry['street'] = street
		entry['city'] = city
		entry['state'] = state
		entry['zip'] = postal_code
		results.append(entry)

	return results


def process_tsv(filepath: str) -> list:
	try:
		results = []
		with open(filepath, 'r', newline='') as file:
			reader = csv.DictReader(file, delimiter='\t')
			for row in reader:
				entry = {}
				if row['organization'] != 'N/A':
					entry['organization'] = row['organization']
				else:
					name  = ' '.join(
						[x for x in [row['first'], row['middle'], row['last']] if x not in [None, 'N/A', 'N/M/N']]
					)
					if any(x in name.lower() for x in [' llc', ' inc', ' ltd']):
						entry['organization'] = name
					else:
						entry['name'] = name

				entry['street'] = row['address']
				entry['city'] = row['city']
				entry['state'] = row['state']

				if row['county']:
					entry['county'] = row['county']

				entry['zip'] = f"{row['zip'].strip()}-{row['zip4'].strip()}" if row['zip4'] else row['zip'].strip()

				entry = {k: v.strip() for k, v in entry.items() if v}
				results.append(entry)
		return results
	except Exception as e:
			sys.stderr.write(f"Error reading TSV file: {e}\n")
			sys.exit(1)


def process_txt(file_path: str) -> list:
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
	parser = argparse.ArgumentParser(description='process multiple address files.')
	parser.add_argument('filepaths', type=str, nargs='+', help='paths to the input files')
	args = parser.parse_args()

	processing_map = {
		'xml': process_xml,
		'tsv': process_tsv,
		'txt': process_txt
	}

	for filepath in args.filepaths:
		filepath_parts = filepath.split('/')
		data_dir = '/'.join(filepath_parts[:-1])
		filename = filepath_parts[-1]
		filename_parts = filename.split('.')
		ext = filename_parts[-1]

		if ext not in processing_map:
			sys.stderr.write(f"unsupported file extension: {ext}\n")
			continue

		try:
			processing_func = processing_map[ext]
			results = processing_func(filepath)
			output_path = f"{data_dir}/{''.join(filename_parts)}_processed.json"
			with open(output_path, 'w') as f:
				f.write(json.dumps(results, indent=4))
			print(json.dumps(results, indent=4))
		except Exception as e:
			sys.stderr.write(f"error processing file {filepath}: {e}\n")

	sys.exit(0)