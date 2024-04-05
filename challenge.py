import argparse
import sys
import os
from script.xml_parser import parse_xml  # Importing parse_xml function from xml_parser module
from script.tsv_parser import parse_tsv  # Importing parse_tsv function from tsv_parser module
from script.txt_parser import parse_txtfile  # Importing parse_txtfile function from txt_parser module


def main():
    """
    Main function to parse files based on their extensions.
    """

    parser = argparse.ArgumentParser(
        description="Parse files based on their extensions and extract address information.",
        epilog="Examples:\n"
        "python challenge.py input1.xml                              # Parse one XML file\n"
        "python challenge.py input1.xml input2.xml                   # Parse more than one XML file\n"
        "python challenge.py input1.xml input2.tsv input3.txt        # Parse XML, TSV, and TXT files simultaneously",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "file_path", 
        nargs="+", 
        help="Path to the files."
        )

    args = parser.parse_args()
    file_paths = args.file_path  # Renamed variable to better reflect its content

    valid_extensions = [".tsv", ".txt", ".xml"]
    invalid_files = []
 
    for file_name in file_paths:
        _,file_extension = os.path.splitext(file_name)
        if file_extension.lower() not in valid_extensions:
            invalid_files.append(file_name)
 
    if invalid_files:
        print(f"Unsupported file format: {file_name}", file=sys.stderr)
        sys.exit(1)

    def parse_file(file_path):
        """
        Function to parse file based on its extension.

        Args:
            file_path (str): Path to the file.

        Returns:
            list: List of dictionaries containing parsed data.
        """

        if file_path.endswith('.xml'):
            return parse_xml(file_path)
        elif file_path.endswith('.tsv'):
            return parse_tsv(file_path)
        elif file_path.endswith('.txt'):
            return parse_txtfile(file_path)
        else:
            print(f"Unsupported file format: {file_path}", file=sys.stderr)
            sys.exit(1)

    for file_path in file_paths:
        print("*"*25+"File Name:", file_path+"*"*25)
        # Renamed variable for clarity
        parsed_data = parse_file(file_path)
        print("Parsed Data: ", parsed_data)
    sys.exit(0)

if __name__ == "__main__":
    main()
