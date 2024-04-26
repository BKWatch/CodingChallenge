import argparse
from typing import List
import string
import json
import csv 
import sys
from xml.dom import pulldom

parser = argparse.ArgumentParser(
    prog="CodingChallenge.",
    description="Parse data into JSON.",
    epilog="Try searching StackOverflow idk.",
    add_help=True
    
)

parser.add_argument(
    "--paths",
    required=True,
    nargs='+',
    metavar="P",
    help="Pass list of valid paths. Supported formats are .csv .tsv .xml.",
    type=str,
    action="extend"
)

args = parser.parse_args()

def validate_data(data: List[str]):
    """
    Function to check if provided paths
    are in desirable format.
    """
    return False in [
        i.endswith(".txt") \
        or i.endswith(".tsv") \
        or i.endswith(".xml") \
        for i in data
    ]
    
    
def health_check(is_not_valid: bool):
    if is_not_valid:
        return"""
        Please, provide valid data paths. \n
        Supported formats: .txt .tsv .xml 
        """
    else:
        return "KOKO"

def open_data(i):
    with open(i, encoding="utf-8") as f:
        lines = f.read()
    return lines

def process_data(data: List[str]):
    check = health_check(validate_data(data))
    if "KOKO" != health_check(validate_data(data)):
        print(check)
        sys.exit(0)
    else:
        dictions = []
        for i in data:
            if i.endswith(".txt"):
                lines = open_data(i).split('\n\n')
                partially_parsed = []
                for e in lines:
                    if len(e.split("\n ")) > 1:
                        partially_parsed.append(e.split("\n "))
                for li in partially_parsed:
                    processed_data = {}
                    for n, ie in enumerate(li):
                        if n == 0:
                            processed_data['name'] = ie
                        elif ie.isupper():
                            processed_data['county'] = ie
                        elif ',' in ie and n != 0:
                            processed_data['city'] = ie.split(',')[0]
                            processed_data['state'] = ie.split(',')[1].split()[0]
                            processed_data['zip'] = ie.split(',')[1].split()[-1]
                        else:
                            processed_data['street'] = ie
                    dictions.append(processed_data)

            elif i.endswith(".tsv"):
                with open(i, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
                    for row in reader:
                        processed_data = {}
                        name = ""
                        for n, ie in enumerate(row):
                            if n <3 and ie != "":
                                name += ie + " "
                                if ("llc" in name.lower()) or ("ltd" in name.lower()):
                                    processed_data['organization_name'] = name
                                else:
                                    processed_data['name'] = name
                            else:
                                if row[3] != 'N/A':
                                    processed_data['organization_name'] = row[3]
                                processed_data['street'] = row[4]
                                processed_data['city'] = row[5]
                                processed_data['state'] = row[6]
                                if len(row[7]) > 1:
                                    processed_data['county'] = row[7]
                                if len(row[9]) > 2:
                                    processed_data['zip'] = row[8] + "-" + row[9]
                                else:
                                    processed_data['zip'] = row[8]
                        if processed_data['city'] != 'city':            
                            dictions.append(processed_data)        
            else:            
                doc = pulldom.parse(i)
                for event, node in doc:
                    if event == pulldom.START_ELEMENT and node.tagName == 'NAME':
                        doc.expandNode(node)
                        if len(node.toxml()) > len('NAME//NAME'):
                            processed_data = {}
                            if len(node.toxml().split(">")[1].split('</')[0]) > len('NAME//NAME'):
                                processed_data['name'] = node.toxml().split(">")[1].split('</')[0]
                    elif event == pulldom.START_ELEMENT and node.tagName == 'COMPANY':
                        doc.expandNode(node)
                        if len(node.toxml())> len('COMPANY//COMPANY'):
                            if len(node.toxml().split(">")[1].split('</')[0]) > len('COMPANY//COMPANY'):
                                processed_data['organisation_name'] = node.toxml().split(">")[1].split('</')[0]
                    elif event == pulldom.START_ELEMENT and node.tagName == 'STREET':
                        doc.expandNode(node)
                        if len(node.toxml()) > len('STREET//STREET'):
                            processed_data['street'] = node.toxml().split(">")[1].split('</')[0]
                    elif event == pulldom.START_ELEMENT and node.tagName == 'CITY':
                        doc.expandNode(node)
                        if len(node.toxml()) > len('CITY//CITY'):
                            processed_data['city'] = node.toxml().split(">")[1].split('</')[0]   
                    elif event == pulldom.START_ELEMENT and node.tagName == 'STATE':
                        doc.expandNode(node)
                        if len(node.toxml()) > len('STATE//STATE'):
                            processed_data['state'] = node.toxml().split(">")[1].split('</')[0] 
                    elif event == pulldom.START_ELEMENT and node.tagName == 'COUNTY':
                        doc.expandNode(node)
                        if len(node.toxml()) > len('COUNTY//COUNTY'):
                            processed_data['county'] = node.toxml().split(">")[1].split('</')[0]
                    elif event == pulldom.START_ELEMENT and node.tagName == 'POSTAL_CODE':
                        doc.expandNode(node)
                        if len(node.toxml()) > len('POSTAL_CODE//POSTAL_CODE'):
                            processed_data['zip'] = node.toxml().split(">")[1].split('</')[0]   
                            dictions.append(processed_data)    


    print(json.dumps(dictions, indent=4))
    sys.exit(1)
    
process_data(args.paths)
