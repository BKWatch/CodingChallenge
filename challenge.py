import argparse
import os
import csv
import json
import xml.etree.ElementTree as ET
from sys import stderr, stdout

class AddressParser:
    def __init__(self):
        self.entries = []

    def configureParser(self):
        parser = argparse.ArgumentParser(description="Utility to parse address data from files in XML, TSV, or TXT formats.")
        parser.add_argument('files', nargs='+', help='List of file paths. Each file should be in XML, TSV, or TXT format.')
        return parser.parse_args()

    def run(self, filePaths):
        for filePath in filePaths:
            try:
                self.checkFileValidity(filePath)
                fileType = self.determineFileType(filePath)
                self.entries.extend(self.parseFile(filePath, fileType))
            except Exception as e:
                print(f"Error processing {filePath}: {e}", file=stderr)
                exit(1)
        self.outputSortedEntries(self.entries)

    def checkFileValidity(self, filePath):
        if not os.path.exists(filePath):
            raise FileNotFoundError(f"File not found: {filePath}")
        if not os.path.isfile(filePath):
            raise IsADirectoryError(f"Expected a file, but it's a directory: {filePath}")
        if not filePath.endswith(('.xml', '.tsv', '.txt')):
            raise ValueError(f"Unsupported file type: {filePath}")
        return True

    def determineFileType(self, filePath):
        if filePath.endswith('.xml'):
            return 'xml'
        elif filePath.endswith('.tsv'):
            return 'tsv'
        elif filePath.endswith('.txt'):
            return 'txt'

    def parseFile(self, filePath, fileType):
        if fileType == 'xml':
            return self.parseXml(filePath)
        elif fileType == 'tsv':
            return self.parseTsv(filePath)
        elif fileType == 'txt':
            return self.parseTxt(filePath)

    def parseXml(self, filePath):
        tree = ET.parse(filePath)
        root = tree.getroot()

        entries = []
        for ent in root.findall('./ENTITY/ENT'):
            entries.append(self.extractXmlEntry(ent))
        return entries

    def extractXmlEntry(self, ent):
        entry = {}
        name = ent.find('NAME').text.strip()
        company = ent.find('COMPANY').text.strip()
        street = ent.find('STREET').text.strip()
        city = ent.find('CITY').text.strip()
        state = ent.find('STATE').text.strip()
        zipCode = ent.find('POSTAL_CODE').text.strip(' -').replace(" ", "")
        entry['name' if name else 'organization'] = name or company
        entry['street'] = street
        entry['city'] = city
        entry['state'] = state
        entry['zip'] = zipCode
        return entry

    def parseTsv(self, filePath):
        entries = []
        with open(filePath, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                entries.append(self.extractTsvEntry(row))
        return entries

    def extractTsvEntry(self, row):
        entry = {}
        nameParts = [row['first'], row['middle'], row['last']]
        name = ' '.join(part for part in nameParts if part and part != 'N/M/N').strip()
        company = row['organization'].strip()
        entry['name' if name else 'organization'] = name or company
        entry['street'] = row['address'].strip()
        entry['city'] = row['city'].strip()
        entry['state'] = row['state'].strip()
        entry['zip'] = row['zip'].strip() + ('-' + row['zip4'].strip() if row['zip4'] else '')
        return entry

    def parseTxt(self, filePath):
        entries = []
        with open(filePath, 'r') as file:
            entry = {}
            for line in file:
                self.extractTxtEntry(line.strip(), entry, entries)
            if entry:
                self.finalizeEntry(entry, entries)
        return entries

    def extractTxtEntry(self, line, entry, entries):
        if 'COUNTY' in line:
            return
        if not line:
            if entry:
                self.finalizeEntry(entry, entries)
                entry.clear()
        elif any(char.isdigit() for char in line):
            if ',' in line:
                self.parseAddressLine(line, entry)
            else:
                entry['street'] = line
        else:
            entry['name'] = line

    def parseAddressLine(self, line, entry):
        if ',' in line:
            parts = line.split(', ')
            entry['city'] = parts[0].strip()
            if len(parts) > 1:
                stateZipParts = parts[1].split(' ')
                entry['state'] = ' '.join(stateZipParts[:-1]).strip()
                entry['zip'] = stateZipParts[-1].strip().rstrip('-')
        else:
            entry['street'] = line

    def finalizeEntry(self, entry, entries):
        entry.setdefault('name', '')
        entry.setdefault('street', '')
        entry.setdefault('city', '')
        entry.setdefault('state', '')
        entry.setdefault('zip', '')
        entries.append(entry.copy())


    def outputSortedEntries(self, entries):
        sortedEntries = sorted(entries, key=lambda x: x['zip'])
        json.dump(sortedEntries, stdout, indent=4)
        exit(0)

if __name__ == "__main__":
    addressBookParser = AddressParser()
    args = addressBookParser.configureParser()
    addressBookParser.run(args.files)
