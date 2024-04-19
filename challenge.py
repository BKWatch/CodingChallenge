
import sys
def zip_func(dict_):
    print(dict_)
    zip = dict_['zip']
    if "-" not in zip:
        return int(zip)
    else:
        return int(zip.split("-")[0])

def format_file(contents,type):
    
    keys = ['name', 'organization','street','street1','street2','city', 'state','country', 'zip']

        
    xml_tags = [
    "<NAME>",
    "</NAME>",
    "<COMPANY>",
    "</COMPANY>",
    "<STREET>",
    "</STREET>",
    "<STREET_2>",
    "</STREET_2>",
    "<STREET_3>",
    "</STREET_3>",
    "<CITY>",
    "</CITY>",
    "<STATE>",
    "</STATE>",
    "<COUNTRY>",
    "</COUNTRY>",
    "<POSTAL_CODE>",
    "</POSTAL_CODE>"
    ]

    json_list = []
    if type == "xml":
        
        contents = contents.split("<ENTITY>")[-1]
        contents = contents.split("</ENTITY>")[0]
        entities = contents.split("</ENT>")
        
        for ent in entities[1:]:
            
            ent = ent.replace("<ENT>\n","")
            ent = ent[1:]
            e = ent.split("\n")
            e.pop()
            
            cnt = 0
            dict_ = {}
            final_dict = {}
            for item in e:
                for tag in xml_tags:
                    item = item.replace(tag,"")
                
                if len(item.strip()) >0:
                    dict_[keys[cnt]] = item.strip()
                    
                    if keys[cnt] == "zip":
                        if dict_[keys[cnt]][-1] == "-":
                            dict_[keys[cnt]] = dict_[keys[cnt]][:-1]
                
                cnt+=1
            
            for k in dict_:
                if len(dict_[k].strip()) != 0 and dict_[k]!="N/A":
                    final_dict[k] = dict_[k].strip()
            json_list.append(final_dict)
            
        json_list.pop()
    
    elif type == "tsv":
        columns = ["first", "middle", "last", "organization", "address", "city", "state", "county", "zip", "zip4"]
        contents = contents.split("\n")
        contents = contents[1:]
        contents = contents[:-1]
        
        for line in contents:
            
            final_dict = {}
            dict_ = {}
            
            vals = line.split("\t")
            
            cnt = 0
            
            dict_["name"] = ""
            for v in vals:
                if cnt<=2:
                    
                    dict_["name"]+=" "+v
                
                    
                elif "zip" in dict_:
                    dict_["zip"]+="-"+v
                else:
                    dict_[columns[cnt]] = v
                    
                
                cnt+=1
            
            for k in dict_:
                if len(dict_[k].strip()) != 0 and dict_[k]!="N/A":
                    final_dict[k] = dict_[k].strip()
                
            json_list.append(final_dict)
        
            
    
    elif type == "txt":
        
        lines = contents.split("\n")
        lines = lines[2:]
        lines.pop()
        lines.pop()
        prep_content = []
        
        temp = []
        for l in lines:
            
            if len(l.strip())>0: 
                temp.append(l.strip())
            
            else:
                
                prep_content.append(temp)
                temp = []
                
        for content in prep_content:
            
            dict_ = {}
            final_dict = {}
            
            x = content.pop(0)
            y = content.pop()
            dict_["name"] = x
            
            address_list = y.split(",")
            
            if len(content)>1:
                dict_["street"] = content[0]
                dict_["county"] = content[1]
                
            else:
                dict_["street"] = content[0]
            
            dict_["city"] = address_list[0]
            
            z = address_list[1].split()
            
            if len(z)==2:
                dict_["state"] = z[0]
                dict_["zip"] = z[1]
            
            elif len(z)>2:
                dict_["state"] = ""
                for it in z[:-1]:
                    dict_["state"]+=it+" "
                
                dict_["zip"] = z[-1]
            
            for k in dict_:
                if len(dict_[k].strip()) != 0 and dict_[k]!="N/A":
                    final_dict[k] = dict_[k].strip()
            
            
            
            json_list.append(final_dict)
    
    json_list = sorted(json_list, key=lambda x: zip_func(x))
    c = 0
    for iter_dict in json_list:
        if iter_dict['zip'][-1] == "-":
            json_list[c]['zip'] = iter_dict['zip'][:-1]
        c+=1
    return json_list
                    
                
            
if __name__ == "__main__":
    
    for filename in sys.argv:
    
        file_type = filename.split(".")[-1]
        
        if file_type in ["xml","txt","tsv"]:

            f = open(filename,'r')

            contents = f.read()

            out_json = format_file(contents,file_type)
            
            print(f"JSON output for filename {filename}")
            print()
            print(out_json)
            print()
            print()
            
        else:
            print("Unsupported file type")
            print()
            print()







