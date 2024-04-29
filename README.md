# BankruptcyWatch Coding Challenge

## Goal

The BankruptcyWatch Coding Challenge is designed to help us locate experienced
developers who are proficient in the Python language and in developing at Github
and who are able to write clean, correct, and reliable code.

## The Challenge

The directory [`input`](input) contains three files each containing a list of US
names and addresses:

* [`input1.xml`](input/input1.xml)
* [`input2.tsv`](input/input2.tsv)
* [`input3.txt`](input/input3.txt)

The file formats are not documented, but you can deduce the formats by examing
their contents. The challenge is to write a python script `challenge.py`,
desgined to be run from the command line, that accepts a list of pathnames of
files in any of the above formats, parses them, and writes a JSON-encoded list
of the combined addresses to standard output, sorted by ZIP code in ascending order. You can assume
that the the format of each file corresponds to its extension, as illustrated by
the above examples. Your submission should consist of a single file, without any 
supporting documents. The output should be a pretty-printed JSON array of JSON
objects, each having 5 or 6 properties, serialized in the given order:

* `name`: The person's full name, if present, consisting of a list of one or more given names followed by the family name
* `organization`: The company or organization name, if present
* `street`: The street address, often just a house number followed by a direction indicator and a street name
* `city`: The city name
* `county:` The county name, if present
* `state`: The US state name or abbreviation
* `zip`: The ZIP code or ZIP+4, in the format 00000 or 00000-0000

A personal name or organization name will always be present, but not both.

Here is a sample output:

```
[
  {
    "name": "Hilda Flores",
    "street": "1509 Alberbrook Pl",
    "city": "Garland",
    "county": "DALLAS",
    "state": "TX",
    "zip": "75040"
  },
  {
    "organization": "Central Trading Company Ltd.",
    "street": "1501 North Division Street",
    "city": "Plainfield",
    "state": "Illinois",
    "zip": "60544-3890"
  }
]
```

The script should

* Be well-organized and easy to understand
* Use only standard Python libraries
* Be compatible with Python 3.11
* Conform to [PEP 8](https://peps.python.org/pep-0008/)
* Provide a `--help` option
* Check for errors in the argument list
* Check the input files to make sure they conform to the formats expemplified by the sample files 
* Output a list of addresses only if no errors were discovered in the above two steps
* Write any error messages to stderr
* Exit with status `0` or `1` to indicate success or failure

> [!WARNING]
> Study the data carefully: it's not as easy as it looks.

## Timing

You should submit your solution within 24 hours of beginning to work on the
challenge.

## Submitting Your Solution

To Submit your solution, fork this repository and submit a pull request. It
should consist of a single commit with a concise commit message.

## Run Code

To run the program, type:
```
python challenge.py input/input1.xml input/input2.tsv input/input3.txt
```

---

Copyright &copy; 2024 BankruptcyWatch, LLC
