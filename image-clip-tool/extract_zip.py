import argparse
import os
from zipfile import ZipFile

def extract_zip(input_zip):
    input_zip = ZipFile(input_zip)
    return {name: input_zip.read(name) for name in input_zip.namelist()}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract contents of a zip file.")
    parser.add_argument("zipfile", help="Path to the zip file to extract.")
    args = parser.parse_args()

    if not os.path.exists(args.zipfile):
        print(f"Error: Zip file not found at {args.zipfile}")
        exit()

    extracted_data = extract_zip(args.zipfile)
    print(extracted_data)
