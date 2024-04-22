import argparse
import os


class FileTypeChecker(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        valid_extensions = (".txt", ".xml", ".tsv")
        for value in values:
            ext = os.path.splitext(value)[1]
            if ext not in valid_extensions:
                parser.error(f"file '{value}' does not end with {valid_extensions}")
        setattr(namespace, self.dest, values)


def main():
    parser = argparse.ArgumentParser(description="BW Challenge")
    parser.add_argument(
        "files",
        nargs="+",
        action=FileTypeChecker,
        help="List of file paths (txt, xml, tsv)",
    )
    args = parser.parse_args()

    for file in args.files:
        print(file)

    # Use the validated file paths
    print("Validated file paths:", args.files)


if __name__ == "__main__":
    main()
