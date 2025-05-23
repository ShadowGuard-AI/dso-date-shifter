import argparse
import os
import re
import random
import logging
import datetime
import chardet
from faker import Faker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the dso-date-shifter tool.
    """
    parser = argparse.ArgumentParser(
        description="Shifts all dates in a file (or directory of files) by a random or specified number of days."
    )

    parser.add_argument(
        "input_path",
        help="Path to the file or directory containing files to be processed."
    )

    parser.add_argument(
        "-s",
        "--shift_days",
        type=int,
        default=None,
        help="Number of days to shift dates by. If not specified, a random shift between -365 and 365 days will be used."
    )

    parser.add_argument(
        "-o",
        "--output_path",
        default=None,
        help="Path to the output directory. If not specified, the input files will be overwritten (use with caution!)."
    )
    
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Process files in the input directory recursively."
    )

    parser.add_argument(
        "-d",
        "--date_format",
        default="%Y-%m-%d",
        help="The format of the dates in the files. Defaults to %%Y-%%m-%%d"
    )
    
    return parser.parse_args()


def shift_date(date_str, shift_days, date_format):
    """
    Shifts a date by a specified number of days.

    Args:
        date_str (str): The date string to shift.
        shift_days (int): The number of days to shift the date by.
        date_format (str): The format of the input date string

    Returns:
        str: The shifted date string.
    """
    try:
        date_obj = datetime.datetime.strptime(date_str, date_format)
        shifted_date = date_obj + datetime.timedelta(days=shift_days)
        return shifted_date.strftime(date_format)
    except ValueError as e:
        logging.warning(f"Invalid date format or unparsable date: {date_str}. Error: {e}")
        return date_str  # Return original string if parsing fails


def process_file(file_path, shift_days, output_path, date_format):
    """
    Processes a single file, shifting all dates within it.

    Args:
        file_path (str): The path to the file to process.
        shift_days (int): The number of days to shift dates by.
        output_path (str): The path to write the processed file to.
        date_format (str): The format of the dates in the file.
    """
    try:
        # Detect the file encoding
        with open(file_path, 'rb') as f:
            rawdata = f.read()
        encoding = chardet.detect(rawdata)['encoding']

        if encoding is None:
            logging.error(f"Could not detect encoding for {file_path}. Skipping.")
            return

        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()

        # Find all dates matching the specified format
        date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}|\d{2}[/-]\d{2}[/-]\d{4}|\d{2}[/-]\d{2}[/-]\d{2}') # Matches YYYY-MM-DD, DD/MM/YYYY, DD/MM/YY and similar
        dates = re.findall(date_pattern, content)


        # Shift the dates and replace them in the content
        shifted_content = content
        for date_str in dates:
            shifted_date = shift_date(date_str, shift_days, date_format)
            shifted_content = shifted_content.replace(date_str, shifted_date)

        # Write the processed content to the output file
        if output_path:
            output_file_path = os.path.join(output_path, os.path.basename(file_path))
        else:
            output_file_path = file_path # Overwrite input file

        with open(output_file_path, 'w', encoding=encoding) as f:
            f.write(shifted_content)

        logging.info(f"Processed file: {file_path} -> {output_file_path}")

    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")



def process_directory(input_path, shift_days, output_path, recursive, date_format):
    """
    Processes all files in a directory, optionally recursively.

    Args:
        input_path (str): The path to the directory to process.
        shift_days (int): The number of days to shift dates by.
        output_path (str): The path to write the processed files to.
        recursive (bool): Whether to process files recursively.
        date_format (str): The format of the dates in the files.
    """
    if output_path and not os.path.exists(output_path):
        os.makedirs(output_path)

    for root, _, files in os.walk(input_path):
        for file in files:
            file_path = os.path.join(root, file)
            if not recursive and root != input_path:
                continue # Skip files in subdirectories if not recursive
            process_file(file_path, shift_days, output_path, date_format)
        if not recursive:
            break  # Only process the top-level directory


def main():
    """
    Main function of the dso-date-shifter tool.
    """
    args = setup_argparse()

    input_path = args.input_path
    shift_days = args.shift_days
    output_path = args.output_path
    recursive = args.recursive
    date_format = args.date_format

    # Input validation
    if not os.path.exists(input_path):
        logging.error(f"Input path does not exist: {input_path}")
        return

    if shift_days is None:
        shift_days = random.randint(-365, 365) # Random shift if not specified
        logging.info(f"Using random shift of {shift_days} days.")
    else:
        logging.info(f"Using shift of {shift_days} days.")
    
    if os.path.isfile(input_path):
        process_file(input_path, shift_days, output_path, date_format)
    elif os.path.isdir(input_path):
        process_directory(input_path, shift_days, output_path, recursive, date_format)
    else:
        logging.error(f"Invalid input path: {input_path}. Must be a file or directory.")


if __name__ == "__main__":
    main()