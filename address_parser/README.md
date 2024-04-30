# **Address Parser**
This Python script parses address data from XML, TSV, and TXT files and outputs a JSON-encoded list of addresses sorted by ZIP code in ascending order.

## Requirements
Python 3.11  
Standard Python libraries  
No external libraries are required, as the script uses only the standard library available in Python 3.11.  

## Features
The script parses files with the following extensions:  
.xml - Parsed by xml_parser.parse_xml  
.tsv - Parsed by tsv_parser.parse_tsv  
.txt - Parsed by txt_parser.parse_txt  
  
If the script encounters a file with an unsupported extension, it will write an error message to standard error (stderr) and exit with status code 1. 
   
Addresses are sorted by ZIP code in ascending order. The output is pretty-printed JSON.  

## Usage
To use the script, run it from the command line, passing the file paths as arguments. The script accepts multiple file paths.

```console
python challenge.py input/input1.xml input/input2.tsv input/input3.txt
```
### Options
--help - Display a help message and exit.

### Output
The script outputs to standard output (stdout). To save the output to a file, redirect the output as follows:

```console
python challenge.py input/input1.xml input/input2.tsv input/input3.txt > <filepath>/output.json
```
### Error Handling
The script checks for errors in the argument list. If no files are provided, or an invalid option is used, the script will print a usage message to stderr.  
  
Each parser function checks the input file format. If an input file does not conform to the expected format, the script will write an error message to stderr.  
  
If any errors are encountered, the script will exit with status code 1. Otherwise, it will exit with status code 0.