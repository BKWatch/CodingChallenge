import os
import sys
import json
import argparse
from xml.dom import minidom 


parser = argparse.ArgumentParser(description="This program can accept a list of inputs in the following formats: " + 
				".txt, .xml or .tsv", usage="challenge.py pathname.*** [pathname.*** ...]");
parser.add_argument('pathname.***',nargs='+')
args=parser.parse_args()

list_result = []


def analize(list_p):
	list_p.pop(0)
	for item in list_p:
		if(os.path.isfile(item)):
			split_name = os.path.splitext(item)
			if split_name[1] == '.txt':
				parse_txt(item)
			elif split_name[1] == '.tsv':
				parse_tsv(item)
			elif split_name[1] == '.xml':
				parse_xml(item)
			else:
				print(item + " does not end in .txt, .tsv or .xml, please try again" +
					" with the correct file", file=sys.stderr)
				exit(0)
		else:
			print(item + " does not exist, please try again with the correct address", file=sys.stderr)
			exit(0)
	printJson(list_result)
	exit(1)


def printJson(l):
	for i in l:
		for key, val in list(i.items()):
			if val.strip() == "":
				i.pop(key)
	json_str = json.dumps(l, indent=4)
	print(json_str)


def parse_txt(path):
	list_txt = []
	with open(path) as f:
		instance = []
		for line in f:
			if line.rstrip():
				instance.append(line.strip())
			else:
				if instance:
					list_txt.append(instance)
					instance = []
	getText(list_txt)


def getText(l):
	for ins in l:
		if len(ins) > 3:
			list_result.append({"name":ins[0],
					"organization":"",
					"street":ins[1],
					"city":ins[3].split(',')[0],
					"county":ins[2],
					"state":ins[3].split(',')[1].strip().rstrip('0123456789- '),
					"zip":ins[3].split(',')[1].strip().split(' ')[1]})
		else:
			list_result.append({"name":ins[0],
					"organization":"",
					"street":ins[1],
					"city":ins[2].split(',')[0],
					"county":"",
					"state":ins[2].split(',')[1].strip().rstrip('0123456789- '),
					"zip":ins[2].split(',')[1].strip().split(' ')[1]})



def parse_tsv(path):
	with open(path) as f:
		next(f)
		for line in f:
			l = line.split('\t')
			list_result.append({"name":getName(l[0],l[1],l[2]),
				"organization":getOrg(l[0],l[2],l[3]),
                                "street":l[4],
                                "city":l[5],
                                "county":l[7],
                                "state":l[6],
                                "zip":getZip(l[8],l[9])})



def parse_xml(path):
	file = minidom.parse(path)
	name = file.getElementsByTagName('NAME')
	company = file.getElementsByTagName('COMPANY')
	street = file.getElementsByTagName('STREET')
	street2 = file.getElementsByTagName('STREET_2')
	street3 = file.getElementsByTagName('STREET_3')
	city = file.getElementsByTagName('CITY')
	state = file.getElementsByTagName('STATE')
	country = file.getElementsByTagName('COUNTRY')
	zip = file.getElementsByTagName('POSTAL_CODE')
	for i in range(len(name)):
		list_result.append({"name":name[i].firstChild.data, 
				"organization":company[i].firstChild.data,
				"street":getStreet(street[i].firstChild.data,street2[i].firstChild.data,street3[i].firstChild.data),
				"city":city[i].firstChild.data,
				"county":"",
				"state":state[i].firstChild.data,
				"zip":zip[i].firstChild.data})


def getZip(eight, nine):
	if len(nine)>1:
		return (eight + "-" + nine).strip()
	else:
		return eight



def getName(one, two, three):
	if len(one)>1:
		if two != "N/M/N":
			return one + " " + two + " " + three
		else:
			return one + " " + three
	else:
		return ""			



def getOrg(one, three, four):
	if four == "N/A":
		if one == "":
			return three
		else:
			return ""
	else:
		return four



def getStreet(one, two, three):
	if two != " ":
		if three != " ":
			return one + " " + two + " " + three
		else:
			return one + " " + two
	else:
		return one



analize(sys.argv)
