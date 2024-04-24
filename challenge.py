import xml.etree.ElementTree as ET
import json
import csv

def JSON(path):
    output = []
    if(path[-4:] == ".xml"):
      tree = ET.parse(path)
      root = tree.getroot()

# Step 2 & 3: Traverse the XML tree and extract relevant information
      output = []
      for parent in root:
        for child in parent:
           if child.tag == "ENT":
              data = {}
              for inner in child:
                data[inner.tag.lower()] = inner.text
              output.append(data)
      output = sorted(output, key=lambda x: (x['postal_code'].split("-"))[0].strip(), reverse=True)
               
                  
    elif(path[-4:] == ".tsv"):

    # Open the TSV file for reading
       with open(path, 'r', encoding='utf-8') as tsvfile:
        # Create a TSV reader
         tsvreader = csv.DictReader(tsvfile, delimiter='\t')
        
        # Iterate over each row in the TSV file
         for row in tsvreader:
            # Append each row as a dictionary to the list
            output.append(row)

       output = sorted(output, key=lambda x: x['zip'].strip(), reverse=True)
    
   
    else:
      
      who = []
      file = open(path,"r")
      people = file.readlines()
      person = []
      for line in people:
        if line != '\n':
            who.append(line[:(len(line)-1)].strip())
            person.append(line[:(len(line)-1)].strip())
        else:
            if len(person) > 0:
              print(person)
              div = {}
              div["name"] = person[0]
              div["address"] = person[1]
              if(len(person) == 3):
                location = person[2].split(" ")
              else:
                div["county"] = person[2]
                location = person[3].split(" ")
              div["city"] = location[0].replace(",","")
              div["state"] = location[1]
              div["zip"] = location[2]
              output.append(div)
              person = []
      file.close()
      output = sorted(output, key=lambda x: x['zip'].strip(), reverse=True)
    return output

output = []
path = input("Enter filepaths for JSON conversion:").split(",")
for check in path: 
  while(check[-4:] != ".xml" and check[-4:] != ".tsv" and check[-4:] != ".txt"):
    print("File has incorrect format, it must be a .xml,.tsv, or .txt file and it's " + check[-4:])
    path = input("Enter filepaths for JSON conversion:")
for file in path:
   found = JSON(file)
   output += found



    


#Convert to JSON
json_data = json.dumps(output, indent=4)
print(json_data)
