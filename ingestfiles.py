import glob
import os
import pandas as pd
import numpy as np
import re
import bs4 as bs
import json
import sys
from typing import List
import argparse




class JSONAddressBook:

    """"Parses xml, txt, and tsv files with addresses in particular formats and saves the addresses in a json file. Requires text files in address format with county on the 3rd line, no organization line, and empty lines between addresses. Requires xml files with tags for NAME, COMPANY, STREET, CITY, STATE and POSTAL_CODE. Requires tsv files with 'first', 'middle' and 'last' name columns as well as columns for 'organization','address','city','county','state', 'zip', and 'zip4'", type = List[str])
   """
    
    def __init__(self, file_locs: List[str]):

        self.file_locs = file_locs
        self.empty_address = {'name':[],'organization' : [],'street' :[],'city': [],'county': [],'state': [],'zip': []}

        if self.file_locs==None:
            sys.stderr.write('Empty file locations')
            sys.exit(1)

        if len(self.file_locs)==0:
            sys.stderr.write('Empty file locations')
            sys.exit(1)

        if type(self.file_locs)!=list:
            sys.stderr.write('Invalid file locations')
            sys.exit(1)

        if type(self.file_locs[0])!=str:
            sys.stderr.write('Invalid file locations')
            sys.exit(1)
            

    def parse_xml(self)  -> pd.DataFrame :

        xmls=[]
        for file_loc in self.file_locs:
            xmls += glob.glob(f"{file_loc}/*.xml")

        if len(xmls)==0:
            return pd.DataFrame(None)

        addresses = self.empty_address


        for f in xmls:
            
            with open(f, 'r') as file:
                content = file.read() 

            if len(content.strip())==0:
                sys.stderr.write('Empty XML file')
                sys.exit(1)
            
            soup = bs.BeautifulSoup(content,'xml')
            
    
            if len(str(soup))==39:
                    sys.stderr.write('Invalid XML file')
                    sys.exit(1)


            addresses['name']+= [data.get_text() for data in soup.find_all('NAME')]
            addresses['organization']+= [data.get_text() for data in soup.find_all('COMPANY')]
            addresses['street'] += [data.get_text() for data in soup.find_all('STREET')]
            addresses['city'] += [data.get_text() for data in soup.find_all('CITY')]
            addresses['state'] += [data.get_text() for data in soup.find_all('STATE')]
            addresses['zip'] += [data.get_text() for data in soup.find_all('POSTAL_CODE')] 
        
        addresses['county']=len(addresses['state'])*[np.nan]   

        df = pd.DataFrame.from_dict(addresses)
        #print(df.head())

        return df

    def parse_tsv(self) -> object :

        tsvs=[]
        for file_loc in self.file_locs:
            tsvs += glob.glob(f"{file_loc}/*.tsv")

        if len(tsvs)==0:
            return pd.DataFrame(None)
            

        dfs = []
        for file in tsvs:
            
            df = pd.read_csv(file,sep ="\t")
            if len(df.columns)==1:
                sys.stderr.write('Invalid tsv file')
                sys.exit(1)
            if len(df)==0:
                sys.stderr.write('Empty tsv file')
                sys.exit(1)

            dfs.append(df)

        alldf = pd.concat(dfs)

        alldf = alldf.rename(columns ={'address':'street'})
        
        lasts=[]
        orgs=[]
        for last, org in zip(alldf['last'],alldf['organization']):


            if type(last)!=float:
                if last.find('LLC')>-1:
                    orgs.append(last)
                    lasts.append(np.nan)
                    continue
                else:
                    lasts.append(last)
            else:
                lasts.append(last)

            orgs.append(org)

        alldf['last'] =  lasts
        alldf['organization'] = orgs

        alldf['middle'] =alldf['middle'].str.replace('N/M/N', '')
        alldf['middle'] = alldf['middle'].apply(lambda x: x.strip()+' ' if x==x else np.nan)
        alldf['first'] = alldf['first'].apply(lambda x: x.strip()+' ' if x==x else np.nan)

        alldf['name'] = alldf['first'] + alldf['middle'] + alldf['last']

        alldf['zip4'] = alldf['zip4'].apply(lambda x: '-'+str(int(x)) if x==x else np.nan)
        alldf['zip'] = alldf['zip'].astype(str) + alldf['zip4']

        alldf = alldf[['name','organization','street','city','county','state','zip']]
        
        #print(alldf.head())

        return alldf


    def parse_txt(self)  -> pd.DataFrame :

        txts=[]
        for file_loc in self.file_locs:
            txts += glob.glob (f"{file_loc}/*.txt")

        if len(txts)==0:
            return pd.DataFrame(None)

        addresses = self.empty_address

        for f in txts:

            with open (f, 'r') as file:
                
                content = file.read()

            if len(content.strip())==0:
                sys.stderr.write('Empty text file')
                sys.exit(1)


            textlist = content.strip().split("\n\n")

            textmatrix = [i.split("\n") for i in textlist]
            textmatrix = [i for i in textmatrix if len(i) in [3,4]]

            if len(textmatrix)==0:
                sys.stderr.write('Improperly formatted text file')
                sys.exit(1)

            addresses['name'] += [i[0].strip() for i in textmatrix]
            addresses['street'] += [i[1].strip() for i in textmatrix]
            addresses['city']  += [i[-1].split(",")[0].strip() for i in textmatrix]
            addresses['state']  += [i[-1].split(",")[-1].split()[0].strip() for i in textmatrix]
            addresses['zip'] += [i[-1].split()[-1].strip() for i in textmatrix]
            addresses['county'] += [i[2].strip().upper() if len(i)==4 else np.nan for i in textmatrix]

        addresses['organization'] = len(addresses['state'])*[np.nan]
        
        df = pd.DataFrame.from_dict(addresses)
        #print(df.head())

        return df


    def combine_addresses(self)  -> pd.DataFrame :


        one = self.parse_xml()
        two = self.parse_tsv()
        three = self.parse_txt()

        finaldf = pd.concat([one,two, three])

        if len(finaldf)==0:               
            sys.stderr.write('No input data')
            sys.exit(1)                 
        
        finaldf = finaldf.reset_index(drop=True)
        finaldf = finaldf[['name','organization','street','city','county','state','zip']]

        #print(finaldf.head())

        return finaldf


    def save_json_addresses(self):


        finaldf = self.combine_addresses()

        jsons = finaldf.to_json('json_address.json',orient='index',indent=2)

        print('Yay!')

        sys.exit(0)

        
    
if __name__ == "__main__":


    #book = JSONAddressBook(['input','others'])
    #book.save_json_addresses()


    parser = argparse.ArgumentParser(description='Make JSON address book from text, xml, and tsv files')


    requiredNamed = parser.add_argument_group('arguments')
    requiredNamed.add_argument('--file_locs', nargs="*", help="The file_locs must be a list of strings. file_locs are file locations of input files. To add file locations at command line type --file_locs followed by paths to files with spaces between them.", type = str)
   
    args = parser.parse_args()
    

    book = JSONAddressBook(args.file_locs)
    book.save_json_addresses()
