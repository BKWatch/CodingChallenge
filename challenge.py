"""
Written by Zachary Tabikh (04/10/2024)

---------------------------------------
REMARKS
---------------------------------------
* This is more of code for demonstration, rather than for production. There's a handful of mistakes and messy bits I believe I had written in the code, but it should basically be functional enough to do as needed.

* This should be able to read for valid data. I can verify XML and TSV parsing should work securely enough for the general purposes, and not for production purposes.

* I misread the submission instructions, as this is actually 2nd commit and not the only commit. The 1st was actually a functional program, but it lacked a sufficient amount of error output and had little to no commentary on what was intended. But it was effectively a fail-safe in the case of running out of time.

"""

import sys
import argparse
import json
import xml.etree.ElementTree as ET # It's only for XML reading in which it uses a Python library.


# Error Checking
def error(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# This basically checks if it's a valid TSV file.
def check_tsv(f):
    f.seek(0)
    rows=len(f.readline().split("\t")) # Since TSV files only uses the tab character for separation and tabs within the data are represented as \t, all that is needed to make sure if the table is consistently using the same number of tabs in all lines. So determines the amount from the first line.
    if not rows>1: # And of course, if there is nothing to split, just consider it not as valid data.
        return False
    for i in f.readlines():
        rows2=len(i.split("\t"))
        if (rows2 != rows): # So... If there's not an even number of tabs, that would be enough to consider it not as one.
            return False
    return True

# This checks the dictionary input after parsing it through xml_read(), tsv_read(), or txt_read(), mostly if it's blank.
def check_valid(usr):
    if (('name' in usr) and ('company' not in usr)) or (('name' not in usr) and ('company' in usr)): # It has to be a person or company, not both.
        if 'street' in usr and 'city' in usr and 'state' in usr and 'zip' in usr:
            if not len(usr['street'])>0: #Street, City, State, and Zip are mandatory data requirements. 
                error("Input: Missing street data.")
                return False
            if not len(usr['city'])>0:
                error("Input: Missing city data.")
                return False
            if not len(usr['state'])>0:
                error("Input: Missing state data.")
                return False
            if not len(usr['zip'])>0:
                error("Input: Missing zip data.")
                return False
            return True
        else:
            error("Input: Missing data for Street, City, State, and/or Zip.")
            return False
    else:
        error("Input: Must be a name or company, it cannot be both.")
        return False
    error("Input: I have no clue. This must be an error regardless.") # This shouldn't be executed, even with errors. But is thrown in anyways.
    return False

# Reads the data through the XML library!
def xml_read(xml):
    users=[]
    ent=xml.find("ENTITY") # All of the important data is within ENTITY.
    if ent!=None:
        count=0 # Count is used to check if there's ENT data inside. It doesn't actually count, and probably should be a Boolean, but it used to.
        for i in ent:
            if i.tag=="ENT": # And let's make sure it's all within ENT tags.
                count=1
                usr={}
                
                item=i.find("NAME")
                if item!=None:
                    if not item.text.isspace():
                        usr['name']=item.text
                
                if 'name' not in usr: # So, if there isn't a name, there should be a company name.
                    item=i.find("COMPANY")
                    if item!=None:
                        if not item.text.isspace():
                            usr['company']=item.text
                
                item=i.find("STREET")
                if item!=None:
                    if not item.text.isspace():
                        usr['street']=item.text
                if 'street' in usr: # This appends for extended street address info, if inputted to STREET_2 and STREET_3.
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
                        z=item.text.split(" - ") # This probably isn't necessary, but I decided to make sure the ZIP data is in the proper format with zeros.
                        if len(z)>=2:
                            if len(z[1])>0:
                                clean_up=str(int(z[0])).zfill(5)[:5]
                                usr['zip']=clean_up
                                
                                clean_up=str(int(z[1])).zfill(4)[:4]
                                usr['zip']+="-"+clean_up
                            else:
                                clean_up=str(int(z[0])).zfill(5)[:5]
                                usr['zip']=clean_up
                
                if not check_valid(usr): # check_valid is effectively the final checking function for further validations in the input data, that don't require the specifics of the format reading. Perhaps that function was the only necessary thing for checking errors.
                    error("XML: Invalid input data.")
                    return []
                users.append(usr)
        if count==0:
            error("XML: There is no data within ENTITY.")
    else:
        error("XML: ENTITY is missing.")
    return users

# This reads from TSV data, which by this point the data should be effectively considered as a valid TSV table. But it may not necessarily be valid for the specific purpose of this program, which is what this function is for.
def tsv_read(f):
    users=[]
    usr={}
    f.seek(0) # It's still making use of the file, so reading back to the start of the file.
    headers=f.readline().split("\t")
    for i in range(len(headers)): #Removes the \n in the list. It's only really the last one that should have it, so the loop isn't actually necessary. Oh well.
        headers[i]=headers[i].replace("\n","")
    try: # This use of TRY should catch the errors if there is missing headers. I'm also using headers as a pseudo-constant, which means there's technically a feature if the TSV columns in the data were rearranged, it should still fetch the right data at the relocated column. It wasn't really a planned feature, but it's something that it could do.
        c_fname=headers.index("first")
        c_mname=headers.index("middle")
        c_lname=headers.index("last")
        c_organization=headers.index("organization")
        c_address=headers.index("address") # BTW, it's annoying with how inconsistent the specification + data is for using 'street' or 'address'.
        c_city=headers.index("city")
        c_state=headers.index("state")
        c_county=headers.index("county")
        c_zip=headers.index("zip")
        c_zip4=headers.index("zip4")
        for i in f.readlines(): # Loops through all of the lines past the first.
            usr={}
            user_data=i.split("\t")
            for j in range(len(user_data)): # That's right, doing this again.
                user_data[j]=user_data[j].replace("\n","")
            
            if not len(user_data[c_fname]) > 0: # Even though there's a column row for organization, it's actually under the last name columns.
                if not user_data[c_lname].isspace():
                    usr['company']=user_data[c_lname]
            else:
                usr['name']=user_data[c_fname]
                if user_data[c_mname] != "N/M/N": # Appends for middle and last name. N/M/N is a field for no middle, so skips that if that's there.
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
            
            if len(user_data[c_zip]) > 0: # Basically the same ZIP data corrections as used in xml_read(). Probably should've been a function.
                clean_up=str(int(user_data[c_zip])).zfill(5)[:5]
                usr['zip']=clean_up
                if len(user_data[c_zip4]) > 0:
                    clean_up=str(int(user_data[c_zip4])).zfill(4)[:4]
                    usr['zip']+=f"-{clean_up}"
            
            if not check_valid(usr): # And the finalized input data validations are here too. If it's not good, no show.
                error("TSV: Invalid input data.")
                return []
            users.append(usr)
    except ValueError as er:
        error(f"TSV: Missing Header, {er.args[0]}")
        return []
    return users

# This reads from TXT data, which is a weird mess because what considered as valid data is fairly loose. But there is a pattern to the format, and so it's still possible to check for validations. I don't imagine many people would like to use such an insecure format anyways, but here's my attempt. It also uses a lot of split, so it's pretty easy to break the parsing if the text wasn't put together right. Oh well, it at least parses input3.txt as it should and that was my main intention.
def txt_read(f):
    users=[]
    usr={}
    temp_inputs=[]
    f.seek(0) # Reads the file from the start, as it's still opened.
    for i in f.readlines():
        temp_str=i.replace("\n","")
        if len(temp_str)>0: # Basically how it checks for data is stupidly simple. Just collects lines of text in an array, and if it bumps into a blank line. That would be considered as a full input. There can be major issues if one were to read a text file that formatted differently, namely with memory, but I'm sure the person who wrote the challenge was aware of such security issues.
            temp_inputs.append(temp_str)
        else:
            usr={}
            if len(temp_inputs)>=3: # What seems like a valid input is that each segment is consisted of 3 lines or 4 lines.
                usr['name']=(temp_inputs[0][:1] + temp_inputs[0][2:]).title() # This removes the white space at the start, and corrects the casing. As some bits of the data makes use of caps.
                usr['street']=temp_inputs[1][:1] + temp_inputs[1][2:]
                if len(temp_inputs)>=4: # The 4 line inputs make use of counties, so let's parse that.
                    if temp_inputs[2].find("COUNTY") != -1: # And well, doesn't hurt to be sure if that block of text contains COUNTY.
                        temp_str=(temp_inputs[2][:1] + temp_inputs[2][2:]).split()
                        usr['county']=temp_str[0].title() # The data is in caps, so let's fix the casing anyways.
                j=len(temp_inputs)-1
                temp_split=temp_inputs[j].split(",") # Two layers of split here.
                usr['city']=temp_split[0][:1] + temp_split[0][2:]
                
                temp_split=temp_split[1].split()
                usr['state']=temp_split[0]
                
                if len(temp_split)==3: # Because of the fact some states may have two words (I mean especially YOU, New Jersey), I did this just for New Jersey. Thankfully there's no state in the US that is three words or more.
                    temp_state=f"{temp_split[0]} {temp_split[1]}"
                    temp_zip=temp_split[2]
                    temp_split[0]=temp_state
                    temp_split[1]=temp_zip
                    temp_split.pop(2)
                
                z=temp_split[1].split("-") # And this is the last time, of making use of that ZIP code formatting.
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
                if not check_valid(usr): # And checks for more validations, if there's anything wrong with the input but not the formatting.
                    print(usr)
                    error("TXT: Invalid input data.")
                    return []
                users.append(usr)
            else:
                if len(users)>0:
                    error("TXT: This may not be proper data.") # I say may not, because as I said how it checks for valid data is way too loose. Hopefully for the general purpose of the challenge it should work. But don't feel it's acceptable for production use.
                    return []
            temp_inputs=[] # Reset the temp input data.
    return users

# The main function, it basically checks if the data from the given path is a valid XML, and if it isn't checks if it's TSV, then checks as TXT data. It does not parse based on the file extension, which is somewhat more secure in that matter.
def main():
    # Argument parsing goes here.
    mp = argparse.ArgumentParser(add_help=True)
    mp.add_argument('path')
    args = mp.parse_args()
    
    # Placeholder variables for the data. There was a tsv_data and txt_data over here, but turned out to be not necessary.
    xml_data=None
    output=None
    
    try:
        f=open(args.path,"rt")
        txt_data=f.read()
        data_type=0 # Determines the type of data just based on parsing it as a valid, rather than just reading from the filename.
        if data_type==0:
            try: # So the first check if the data is XML, otherwise if it isn't. Just skip to the TSV check.
                xml_data = ET.fromstring(txt_data)
                data_type=1
                print("XML detected.")
                output=xml_read(xml_data)
            except ET.ParseError:
                pass
        if data_type==0:
            if check_tsv(f): # Checks if it's TSV data, which basically is a check if the number of tabs is consistent across all lines.
                print("TSV detected.")
                data_type=2
                output=tsv_read(f)
        if data_type==0: # And as a last resort, checks if it's TXT data. Which would be very loose in terms of what counts as valid data, but it does attempt to see if it's formatted correctly. Otherwise if that fails, it's simply an error for invalid data.
            output=txt_read(f)
            if output:
                print("TXT file detected.")
                data_type=3
        f.close()
        if len(output) >0: # So if the parsing was successful for any of the three methods, it should dump pretty JSON data.
            print(json.dumps(output, indent=4))
        else:
            error("Main: Cannot read the file format.")
            return 1
    except FileNotFoundError as er:
        error(f"Main: File not found! [{args.path}]")
        return 1
    except Exception as er: # Not sure what sort of error could come up, but it will go to stderr.
        error(f"Main: Misc. Error! [{type(er)}, {er.args}]")
        return 1
    return 0
    
if __name__ == '__main__':
    print(f"Output: {main()}")