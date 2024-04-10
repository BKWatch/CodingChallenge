"""
---------------------------------------
UNFINISHED CODE WARNING
---------------------------------------
It's basically functional in terms in being able to parse the three types of files, but I am not 100% done. There's still a lot of polish before I consider it satisfactory for a submission, but should do as needed if it must be submitted in the current state as it is.

I mostly just need to clean up the code with PEP 8 and comments, more in depth checking for input errors (there is some, but not exhaustive enough to account for every possible user inputted error), and proper output. This is more or less a prototype.
"""
import argparse
import xml.etree.ElementTree as ET
import json

mp = argparse.ArgumentParser(add_help=True)
mp.add_argument('path')
args = mp.parse_args()

def check_tsv(f):
    f.seek(0)
    rows=len(f.readline().split("\t"))
    if not rows>1:
        return False
    for i in f.readlines():
        rows2=len(i.split("\t"))
        if (rows2 != rows):
            return False
    return True

def xml_read(xml):
    users=[]
    ent=xml.find("ENTITY")
    if ent!=None:
        for i in ent:
            if i.tag=="ENT":
                usr={}
                
                item=i.find("NAME")
                if item!=None:
                    if not item.text.isspace():
                        usr['name']=item.text
                
                if 'name' not in usr:
                    item=i.find("COMPANY")
                    if item!=None:
                        if not item.text.isspace():
                            usr['company']=item.text
                
                item=i.find("STREET")
                if item!=None:
                    if not item.text.isspace():
                        usr['street']=item.text
                if 'street' in usr:
                    item=i.find("STREET_2")
                    if item!=None:
                        if not item.text.isspace():
                            usr['street']+=f", {item.text}"
                            item=i.find("STREET_3")
                            if item!=None:
                                if not item.text.isspace():
                                    usr['street']+=f", {item.text}"
                
                item=i.find("CITY")
                if item!=None:
                    if not item.text.isspace():
                        usr['city']=item.text
                
                item=i.find("COUNTY")
                if item!=None:
                    if not item.text.isspace():
                        usr['county']=item.text
                
                item=i.find("STATE")
                if item!=None:
                    if not item.text.isspace():
                        usr['state']=item.text
                
                item=i.find("POSTAL_CODE")
                if item!=None:
                    if not item.text.isspace():
                        z=item.text.split(" - ")
                        if len(z)>=2:
                            if len(z[1])>0:
                                clean_up=str(int(z[0])).zfill(5)[:5]
                                usr['zip']=clean_up
                                
                                clean_up=str(int(z[1])).zfill(4)[:4]
                                usr['zip']+="-"+clean_up
                            else:
                                clean_up=str(int(z[0])).zfill(5)[:5]
                                usr['zip']=clean_up
                
                users.append(usr)
    return users

def tsv_read(f):
    users=[]
    usr={}
    f.seek(0)
    headers=f.readline().split("\t")
    for i in range(len(headers)):
        headers[i]=headers[i].replace("\n","")
    try:
        c_fname=headers.index("first")
        c_mname=headers.index("middle")
        c_lname=headers.index("last")
        c_organization=headers.index("organization")
        c_address=headers.index("address")
        c_city=headers.index("city")
        c_state=headers.index("state")
        c_county=headers.index("county")
        c_zip=headers.index("zip")
        c_zip4=headers.index("zip4")
        for i in f.readlines():
            usr={}
            user_data=i.split("\t")
            for j in range(len(user_data)):
                user_data[j]=user_data[j].replace("\n","")
            
            if not len(user_data[c_fname]) > 0:
                if not user_data[c_lname].isspace():
                    usr['company']=user_data[c_lname]
            else:
                usr['name']=user_data[c_fname]
                if user_data[c_mname] != "N/M/N":
                    usr['name']+=f" {user_data[c_mname]}"
                usr['name']+=f" {user_data[c_lname]}"
                
            if len(user_data[c_address]) > 0:
                usr['street']=user_data[c_address]
            
            if len(user_data[c_address]) > 0:
                usr['city']=user_data[c_city]
            
            if len(user_data[c_county]) > 0:
                usr['county']=user_data[c_county]
            
            if len(user_data[c_state]) > 0:
                usr['state']=user_data[c_state]
            
            if len(user_data[c_zip]) > 0:
                clean_up=str(int(user_data[c_zip])).zfill(5)[:5]
                usr['zip']=clean_up
                if len(user_data[c_zip4]) > 0:
                    clean_up=str(int(user_data[c_zip4])).zfill(4)[:4]
                    usr['zip']+=f"-{clean_up}"
            
            users.append(usr)
    except ValueError as er:
        print(er.args)
    return users

def txt_read(f):
    users=[]
    usr={}
    temp_inputs=[]
    f.seek(0)
    for i in f.readlines():
        temp_str=i.replace("\n","")
        if len(temp_str)>0:
            temp_inputs.append(temp_str)
        else:
            usr={}
            if len(temp_inputs)>=3:
                usr['name']=(temp_inputs[0][:1] + temp_inputs[0][2:]).title()
                usr['address']=temp_inputs[1][:1] + temp_inputs[1][2:]
                if len(temp_inputs)>=4:
                    if temp_inputs[2].find("COUNTY") != -1:
                        temp_str=(temp_inputs[2][:1] + temp_inputs[2][2:]).split()
                        usr['county']=temp_str[0].title()
                j=len(temp_inputs)-1
                temp_split=temp_inputs[j].split(",")
                usr['city']=temp_split[0][:1] + temp_split[0][2:]
                
                temp_split=temp_split[1].split()
                usr['state']=temp_split[0]
                
                if len(temp_split)==3:
                    temp_state=f"{temp_split[0]} {temp_split[1]}"
                    temp_zip=temp_split[2]
                    temp_split[0]=temp_state
                    temp_split[1]=temp_zip
                    temp_split.pop(2)
                
                z=temp_split[1].split("-")
                if len(z)>=2:
                    if len(z[1])>0:
                        clean_up=str(int(z[0])).zfill(5)[:5]
                        usr['zip']=clean_up
                        
                        clean_up=str(int(z[1])).zfill(4)[:4]
                        usr['zip']+="-"+clean_up
                    else:
                        clean_up=str(int(z[0])).zfill(5)[:5]
                        usr['zip']=clean_up
                else:
                    clean_up=str(int(temp_split[1])).zfill(5)[:5]
                    usr['zip']=clean_up
                users.append(usr)
            temp_inputs=[]
    return users

def main():
    xml_data=None
    tsv_data=None
    txt_data=None
    output=None
    try:
        f=open(args.path,"rt")
        txt_data=f.read()
        data_type=0
        # Determines the type of data just based on parsing it as a valid, rather than just reading from the filename.
        if data_type==0:
            try: #Checking if XML here.
                xml_data = ET.fromstring(txt_data)
                data_type=1
                print("XML detected.")
                output=xml_read(xml_data)
            except ET.ParseError:
                pass
        if data_type==0:
            if check_tsv(f):
                print("TSV detected.")
                data_type=2
                output=tsv_read(f)
        if data_type==0:
            print("TXT or other file detected.")
            output=txt_read(f)
        f.close()
        if output != None:
            print(json.dumps(output, indent=4))
        else:
            return 1
    except Exception as er:
        print(type(er), er.args)
    return 0
    
if __name__ == '__main__':
    print(f"Output: {main()}")