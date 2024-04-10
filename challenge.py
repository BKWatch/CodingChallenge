import sys, pathlib, re, os.path, collections, json
from argparse import ArgumentParser
import xml.etree.ElementTree as ET

tags = ['name','organization','street','city','county','state','zip']
exceltags = {'name':'name','company':'organization','street':'street','street_2':'street','street_3':'street','city':'city','county':'county','state':'state','postal_code':'zip'}
tsvtags = {'first':'name','middle':'name','last':'name','organization':'organization','address':'street','city':'city','county':'county','state':'state','zip':'zip','zip4':'zip'}
files = sys
JSON_ab ={}

def insertIntoJSON(quip):
	JSON_ab[quip['zip']] = quip

def printErr(msg):
	print(msg, file=sys.stderr)
	sys.exit(1)

def checkZip(zipc):
	inf = re.search('([0-9]{5}\-?([0-9]{4})?)', zipc)
	if not inf:
		printErr("Error: No zip code found in .xml entry.")

def parseTXT(file):
	f = open(file, "r")
	lines = f.read()
	lines = lines.split('\n\n')
	for li in lines:
		if li:
			json_node = {}
			values = li.split('\n')
			if len(values) > 4 or len(values) < 3:
				printErr("Error in .txt file: Incorrect amount of items in entry. Should be 3 or 4.")
			json_node['name'] = values[0].strip()
			json_node['street'] = values[1].strip()
			csz = values[-1].strip().split(',')
			inf = re.search('([0-9]{5}\-?([0-9]{4})?)', csz[1]) # Regex that detects numbers in a zip code format
			if not inf:
				printErr("Error: No zip code found in .txt entry.")
			json_node['city'] = csz[0].strip()
			json_node['state'] = csz[1][:inf.start()].strip()
			json_node['zip'] = inf.group(1)
			if '-'==json_node['zip'].strip()[-1]:
				json_node['zip'] = json_node['zip'][:-1]
			if len(values) == 4:
				json_node['county'] = values[2].strip()
			insertIntoJSON(json_node)

def parseTSV(file):
	f = open(file, "r")
	lines = f.read()
	lines = lines.split('\n')
	tags = lines[0].split('\t')
	lines = lines[1:]
	for li in lines:
		if li:
			li = li.split('\t')
			if (len(li)!=len(tags)):
				printErr("Mismatch between tags and entry indexes in .TSV file.")
			json_node = {}
			for t in range(len(li)):
				if li[t] and li[t]!="N/A":
					if tags[t] == 'first' and li[t] != "":
						json_node['name'] = li[t]+(' ' if li[t+1]=="N/M/N" else " "+li[t+1]+" ")+li[t+2] #Get whole name at once
					elif tags[t] == 'zip':
						json_node['zip'] = li[t]
						if li[t+1]:
							json_node['zip']+='-'+li[t+1]
						checkZip(json_node['zip'])
					elif tsvtags[tags[t]]!='name':
						json_node[tsvtags[tags[t]]] = li[t]
			insertIntoJSON(json_node)

def parseExcel(file):
	tree = ''
	try:
		tree = ET.parse(file)
		root = tree.getroot()
		root = root[1] #Get main file data
		for child in root: #Each node
			json_node = {'street':''}
			companyname = False
			for tag in child:
				if (tag.tag.lower() in exceltags.keys()):
					if (tag.text and not tag.text==' '):
						if (tag.tag == 'COMPANY' or tag.tag == 'NAME'):
							if companyname:
								printErr("Can't have a company and a name.")
							json_node[exceltags[tag.tag.lower()]]=tag.text.strip()
							companyname = True
						elif (tag.tag == 'STREET' or tag.tag == 'STREET_2' or tag.tag == 'STREET_3'):
							json_node[exceltags[tag.tag.lower()]]=(json_node["street"]+tag.text).strip()
						elif (tag.tag == 'POSTAL_CODE'):
							json_node[exceltags[tag.tag.lower()]]=tag.text.replace(" ","")
							# if there's an extra dash, trim it to look pretty
							if '-'==json_node['zip'].strip()[-1]:
								json_node['zip'] = json_node['zip'][:-1]
							checkZip(json_node['zip'])
						else:
							json_node[exceltags[tag.tag.lower()]]=tag.text.strip()
			insertIntoJSON(json_node)
	except ET.ParseError:
		printErr("Unable to parse the XML file. Please check and try again.")

parser = ArgumentParser()
parser.add_argument('files',metavar='path', type=str, nargs='+', help='A list of files to parse.')
res = parser.parse_args()
for file in res.files:
	if not os.path.isfile(file):
		printErr("File "+file+" does not exist. Please check and try again.")
for file in res.files:
	ext = pathlib.Path(file).suffix
	if ext == '.xml':
		parseExcel(file)
	elif ext == '.tsv':
		parseTSV(file)
	elif ext == '.txt':
		parseTXT(file)
	else:
		printErr("File format"+pathlib.Path(file).suffix+" is not supported.")
	print(json.dumps(collections.OrderedDict(sorted(JSON_ab.items())), indent=1))
	sys.exit(0)