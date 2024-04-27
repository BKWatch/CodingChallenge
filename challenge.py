import json
import os
import sys
import xml.etree.ElementTree as ET


#   reads a line and returns the most likely category
def getlinetype(line):
    if line == "\n":
        return "newline"

    if len(line) > 2 and line[2].isnumeric() or line.startswith("  P.O."):
        return "street"

    if line.strip().split(' ')[len(line.strip().split(' ')) - 1].replace('-', '').isnumeric():
        return "zip"

    if line.find("COUNTY") != -1:
        return "county"


def parsetxt(f):
    clientdata = []
    with open(f, "r") as f:
        lines = f.readlines()
        client = ["None", "None", "None", "None", "None", "None", "None", "None"]
        for index, line in enumerate(lines[1:]):
            match (getlinetype(line)):
                #   if new line post current client, start a new list, and assume the next line is a name
                case "newline":
                    if index <= len(lines) - 3:
                        if index >= 4:
                            clientdata.append(client)
                            client = ["None", "None", "None", "None", "None", "None", "None", "None"]
                        client[0] = lines[index + 2].strip()

                #   checks if the line starts with numbers and assumes it's a street
                case "street":
                    client[2] = line.strip()

                #   Checks if the last part of the line is numeric and assumes thats the zipcode
                case "zip":
                    citystatezip = line.strip().split(' ')
                    if len(citystatezip) <= 3:
                        client[3] = citystatezip[0].replace(",", "")
                    else:
                        client[3] = citystatezip[0] + " " + citystatezip[1].replace(",", "")
                    client[5] = citystatezip[len(citystatezip) - 2]
                    client[6] = citystatezip[len(citystatezip) - 1]
                case "county":
                    client[4] = line.strip().replace("\n", "")
    clientdata.append(client)

    return clientdata


def parsetsv(f):
    clientdata = []
    with open(f, "r") as f:
        lines = f.readlines()
        for line in lines[1:]:
            #   replace blank inputs with a value
            parsed = line.replace(" 	", "None").split("	")
            client = [str(parsed[0] + " "
                          + parsed[1] + " "
                          + parsed[2])
                      .replace("N/M/N ", "").replace(",", ""),
                      parsed[3],
                      parsed[4],
                      parsed[5],
                      parsed[6],
                      parsed[7],
                      parsed[8]]
            if client[0].startswith("None None ") and client[0] != "None None None":
                client[1] = client[0].replace("None None ", "")
                client[0] = "None"
            for x in range(len(client)):
                if client[x].count("None") == 3:
                    client[x] = "None"
            for string in client:
                for x in range(len(string)):
                    string[x].replace(",", "")

            clientdata.append(client)

    return clientdata


def parsexml(f):
    tree = ET.parse(f)
    root = tree.getroot()
    clientdata = []
    for child in root[1]:
        for x in range(0, len(child), 9):
            if child[x].text == " ":
                child[x].text = "None"
            client = [str(child[x].text),
                      str(child[x + 1].text).strip(),
                      str(child[x + 2].text) + str(child[x + 3].text) + str(child[x + 4].text).strip(),
                      str(child[x + 5].text),
                      "None",
                      str(child[x + 6].text),
                      str(child[x + 8].text)]
            clientdata.append(client)
    return clientdata


def writetofile(clientdata, filename):
    with open(filename, "w") as f:
        f.write("[\n")
        clientdata = sortbyzipcode(clientdata)
        for clients in clientdata:
            for row in clients:
                clientobj = {'name': row[0],
                             'organization': row[1],
                             'street': row[2],
                             'city': row[3],
                             'county': row[4],
                             'state': row[5],
                             'zip': row[6]}
                for key, value in dict(clientobj).items():
                    if value == "None" or value == "N/A" or value == "":
                        del clientobj[key]
                json.dump(clientobj, f, indent=2)
                f.write(",\n")
        f.write("]")


def sortbyzipcode(clientdata):
    for client in clientdata:
        clientdata.clear()
        clientdata.append(sorted(client, key=lambda client: client[6]))
    return clientdata


def helpscreen():
    print("This script takes contact information in the formats .tsv .txt and .xml\n"
          "and creates a json document sorted by zipcode\n"
          "Syntax: python3 Challenge.py file1.txt etc.")

filenames = []

#   converts arguments to filepaths
for x in range(len(sys.argv) - 1):
    if(sys.argv[x + 1] == "--help"):
        helpscreen()
        exit(1)
    filenames.append(sys.argv[x + 1])

clientdata = []

for file in filenames:
    #   verify files existence
    if not os.path.isfile(file):
        print("File " + file + " does not exist\n Type --help for help", file=sys.stderr)
        exit(0)
        #   checks file type and calls parser
    else:
        if file.endswith(".txt"):
            clientdata.append(parsetxt(file))
        elif file.endswith(".tsv"):
            clientdata.append(parsetsv(file))
        elif file.endswith(".xml"):
            clientdata.append(parsexml(file))
        else:
            print(file + " is not a recognized type", file=sys.stderr)
            exit(0)

writetofile(clientdata, "output.txt")
exit(1)
