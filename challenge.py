import json as j
import xml.dom.minidom as x 
import itertools
import threading
import time
import sys

done = False
#here is the animation

def animate():
    print('\nPlease press enter to continue\n')
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if done:
            break
        sys.stdout.write('\rwaiting ' + str(c))
        sys.stdout.flush()
        time.sleep(0.1)

def shellSort(input_list):
    gap = len(input_list) // 2
    while gap > 0:
        for i in range(gap, len(input_list)):
            temp = input_list[i]
            j = i
            # Sort the sub list for this gap
            while j >= gap and input_list[j - gap]['POSTAL_CODE'] > temp['POSTAL_CODE']:
                input_list[j] = input_list[j - gap]
                j = j-gap
                input_list[j] = temp
# Reduce the gap for the next element
        gap = gap//2
    return input_list


def bubble(s):
    for i in range(0, len(s)-1):
        for k in range(i+1, len(s)):
            if s[i]['POSTAL_CODE'] > s[k]['POSTAL_CODE']:
                temp = s[i]
                s[i] = s[k]
                s[k] = temp
    return s

def insertion(InputList):
    for i in range(1, len(InputList)):
        j = i-1
        nxt_element = InputList[i]
# Compare the current element with next one
        while (InputList[j]['POSTAL_CODE'] > nxt_element['POSTAL_CODE']) and (j >= 0):
            InputList[j+1] = InputList[j]
            j=j-1
            InputList[j+1] = nxt_element

    return InputList

def selection(input_list):

    for idx in range(len(input_list)):
        min_idx = idx
        for j in range( idx +1, len(input_list)):
            if input_list[min_idx]['POSTAL_CODE']> input_list[j]['POSTAL_CODE']:
                min_idx = j
        # Swap the minimum value with the compared value
        input_list[idx], input_list[min_idx] = input_list[min_idx], input_list[idx]
    
    return input_list

def merge(unsorted_list):

    if len(unsorted_list) <= 1:
        return unsorted_list
    # Find the middle point and devide it
    middle = len(unsorted_list) // 2
    left_list = unsorted_list[:middle]
    right_list = unsorted_list[middle:]

    left_list = merge(left_list)
    right_list = merge(right_list)

    return list(merge_sort(left_list, right_list))

# Merge the sorted halves
def merge_sort(left_half,right_half):
    res = []

    while len(left_half) != 0 and len(right_half) != 0:
        if left_half[0]['POSTAL_CODE'] < right_half[0]['POSTAL_CODE']:
            res.append(left_half[0])
            left_half.remove(left_half[0])
        else:
            res.append(right_half[0])
            right_half.remove(right_half[0])

    if len(left_half) == 0:
        res = res + right_half
    else:
        res = res + left_half
    return res

def read(n, s):

    name={"NAME": "",
          "COMPANY": " ",
          "STREET": "",
          "STREET_2": " ",
          "STREET_3": " ",
          "CITY": "",
          "STATE": "",
          "COUNTRY": " ",
          "POSTAL_CODE": ""}
    list_for_entire_file=[]
    w=open(n, 'r')

    a=w.read()
    list_for_entire_file.append(a)
    w.close()

    g=[]
    e=[]
    i=0

    for x in list_for_entire_file:
        p=x.split("\n\n")
        for x in p:
            g.append(x)
        for p in g:
            p=p.split("\n")
            n=0
            for x in p:
                if x !="":
                    n+=1

            # I'm checking if n = 3 because each name and address can have more than one line. If I don't check for this, the concatenation of information for the dictionary will mess up
            if n == 3:
                name["NAME"]=p[0][2:]
                name["STREET"]=p[1][2:]
                a=p[2].split()
                name["CONTRY"]="US"
                if len(a) == 4:
                    name["CITY"]=a[0]+" "+a[1]
                    name["STATE"]=a[2]
                    name["POSTAL_CODE"]=a[3]
                else:
                    name["CITY"]=a[0]
                    name["STATE"]=a[1]
                    name["POSTAL_CODE"]=a[2]

            elif n == 4:
                name["NAME"]=p[0][2:]
                name["STREET"]=p[1][2:]
                name["STREET_2"]=p[2][2:]
                a=p[3].split()
                name["COUNTRY"]="US"
                if len(a) == 4:
                    name["CITY"]=a[0]+" "+a[1]
                    name["STATE"]=a[2]
                    name["POSTAL_CODE"]=a[3]
                else:
                    name["CITY"]=a[0]
                    name["STATE"]=a[1]
                    name["POSTAL_CODE"]=a[2]
               
            r=j.dumps(name)
            e.append(r)

        for a in e:
            x=j.loads(a)
            s.append(x)  
    return s

def process(n, listOf):
    info={"first":"",
          "middle":"",
          "last":"",
          "organization":"",
          "address":"",
          "city":"",
          "state":"",
          "county":"",
          "zip":"",
          "zip4":""}

    name={"NAME": "",                               "COMPANY": " ",
        "STREET": "",
        "STREET_2": " ",                            "STREET_3": " ",
        "CITY": "",
        "STATE": "",
        "COUNTRY": " ",
        "POSTAL_CODE": ""}
    list_for_entire_file=[]
    w=open(n, 'r')
    for l in w:
        a=w.read()
        list_for_entire_file.append(a)
    w.close()
    g=[]
    k=[]
    i=0
    for x in list_for_entire_file:
        p=x.split("\n")
        
        for o in p:
            o=o.split("\t")
            
            if len(o) == 10:    
                info["first"]=o[0]
                info["middle"]=o[1]
                info["last"]=o[2]
                info["organization"]=o[3]
                info["address"]=o[4]
                info["city"]=o[5]
                info["state"]=o[6]
                info["county"]=o[7]
                info["zip"]=o[8]
                info["zip4"]=o[9]

                name["NAME"]=info["first"]+" "+info["middle"]+" "+info["last"]
                name["COMPANY"]=info["organization"]
                name["STREET"]=info["address"]
                if info["county"] == "":
                    name["CITY"]=info["city"]
                else:
                    name["CITY"]=info["city"]+", "+info["county"]
                name["STATE"]=info["state"]
                name["COUNTRY"]="US"
                if info["zip4"] == "":
                    name["POSTAL_CODE"]=info["zip"]+" - "
                else:
                    name["POSTAL_CODE"]=info["zip"]+" - "+info["zip4"]

            #I'm turning the dictionary into a string temporarily because you can't add them to the list all immediately. 
            
                x=j.dumps(name)
                k.append(x)

    #After the set of string dictionaries are all loaded or appended into the list, then you can iterate over the list to turn it back into a json dictionary and append each to the larger list of all dictionaries

    for a in k:
        x=j.loads(a)
        listOf.append(x)

    #Returning the list of all json objects after processing
    return listOf
def xml(fileName, listofnames):
    # Read the file
    y=x.parse(fileName)

    # Look through each node having ENT node name
    for i in y.getElementsByTagName("ENT"):
        
        # Generate dictionary for node element
        brace={}

        # For each ENT, look for the children nodes for each address and name information
        for child in i.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                nodeName=child.nodeName
                if child.firstChild != None:
                    node=nodeName
                    nodeName=child.firstChild.nodeValue
                    brace[node]=nodeName
        listofnames.append(brace)
    return listofnames


if sys.argv[1] == '--help':
    print("usage: file.py <file.xml> <file.txt> <file.tsv>...")
else:
    list_for_file=[]
    file_list=[]
    sorted_result=[]

    print("Here are the files you selected:")
    print()
    for w in range(1, len(sys.argv)):
        print(sys.argv[w])
    print()

    t = threading.Thread(target=animate)
    t.start()
    
    p=input()
    done = True
    
    type=0
    for arg in range(1, len(sys.argv)):
        if sys.argv[arg][-3:] == "xml":
            try:
                file_list=xml(sys.argv[arg], list_for_file)
            except:
                print("Unable to read: " +sys.argv[arg], file=sys.stderr)
                raise
                sys.exit(1)


        elif sys.argv[arg][-3:] == "tsv":
            try:
                file_list=process(sys.argv[arg], list_for_file)
            except:
                print("Unable to read: " +sys.argv[arg], file=sys.stderr)
                raise
                sys.exit(1)
        elif sys.argv[arg][-3:] == "txt":
            try:
                file_list=read(sys.argv[arg], list_for_file)
            except:
                print("Unable to read: " +sys.argv[arg], file=sys.stderr)
                raise
                sys.exit(1)
        else:
            print("Something went wrong!", file=sys.stderr)
            raise
            sys.exit(1)
    print("number ", end="")
    print(type)
    

    print("Which sorting algorithm would you like to use:")
    print("1) Bubble")
    print("2) Selection")
    print("3) Insertion")
    print("4) Merge")
    print("5) Shell")
    algo=int(input())

    if algo == 1:
        sorted_result=bubble(file_list)
    elif algo == 2:
        sorted_result=selection(file_list)
    elif algo == 3:
        sorted_result=insertion(file_list)
    elif algo == 4:
        sorted_result=merge(file_list)
    elif algo == 5:
        sorted_result=shellSort(file_list)

    list_of_json=j.dumps(sorted_result, indent=4)
    print(list_of_json)
    print()
    sys.exit(0)

