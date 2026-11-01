import argparse
import os
import re
import random
import logging
import sys
import datetime
import chardet

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


def candidate_formats(date_str, date_format):
    """Formats to try for a matched date, in order.

    The configured format is tried first. If it cannot parse the
    shape that was matched, the format that shape itself implies
    is tried next, so every shape the search pattern advertises
    is actually shifted instead of being left in clear.
    """
    candidates = []

    def add(fmt):
        if fmt and fmt not in candidates:
            candidates.append(fmt)

    # Order in this list is a silent decision about ambiguous dates. For a
    # two part shape, day first is added before month first, and the
    # configured default (%Y-%m-%d) cannot parse such a shape at all, so a
    # plain run reads 01/02/2023 as 1 February. When both readings parse,
    # which is any day of 12 or under, the day first reading wins with no
    # warning anywhere.
    add(date_format)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
        add("%Y-%m-%d")
    elif re.fullmatch(r"\d{4}/\d{2}/\d{2}", date_str):
        add("%Y/%m/%d")
    elif re.fullmatch(r"\d{2}-\d{2}-\d{4}", date_str):
        add("%d-%m-%Y")
        add("%m-%d-%Y")
    elif re.fullmatch(r"\d{2}/\d{2}/\d{4}", date_str):
        add("%d/%m/%Y")
        add("%m/%d/%Y")
    elif re.fullmatch(r"\d{2}-\d{2}-\d{2}", date_str):
        add("%d-%m-%y")
        add("%m-%d-%y")
    elif re.fullmatch(r"\d{2}/\d{2}/\d{2}", date_str):
        add("%d/%m/%y")
        add("%m/%d/%y")
    return candidates


def shift_date(date_str, shift_days, date_format):
    """
    Shifts a date by a specified number of days.

    Args:
        date_str (str): The date string to shift.
        shift_days (int): The number of days to shift the date by.
        date_format (str): The format of the input date string

    Returns:
        str: The shifted date string in the same shape as the
        input, or None when no candidate format can parse it.
    """
    last_error = None
    for fmt in candidate_formats(date_str, date_format):
        try:
            date_obj = datetime.datetime.strptime(date_str, fmt)
            shifted_date = date_obj + datetime.timedelta(days=shift_days)
            return shifted_date.strftime(fmt)
        except ValueError as e:
            last_error = e
    logging.warning(f"Invalid date format or unparsable date: {date_str}. Error: {last_error}")
    return None


def process_file(file_path, shift_days, output_path, date_format):
    """
    Processes a single file, shifting all dates within it.

    Returns a dict with matched, shifted, and failed counts and a
    success flag. A file counts as successful only when at least
    one date was shifted and no matched date was left unshifted.
    """
    stats = {"matched": 0, "shifted": 0, "failed_dates": 0, "success": False}
    try:
        # Detect the file encoding
        with open(file_path, 'rb') as f:
            rawdata = f.read()
        encoding = chardet.detect(rawdata)['encoding']

        if encoding is None:
            logging.error(f"Could not detect encoding for {file_path}. Skipping.")
            return stats

        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()

        # Find all dates matching the advertised shapes and shift them
        # in one substitution pass, using one shared shift for the run.
        # The old loop replaced one date string at a time over the whole
        # text, so a shifted date that landed on another date present in
        # the file was shifted a second time when that date's turn came:
        # distinct dates collapsed onto one day.
        date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}|\d{4}/\d{2}/\d{2}|\d{2}[/-]\d{2}[/-]\d{4}|\d{2}[/-]\d{2}[/-]\d{2}') # Matches YYYY-MM-DD, YYYY/MM/DD, DD/MM/YYYY, DD/MM/YY and similar

        def _sub(match):
            stats["matched"] += 1
            shifted = shift_date(match.group(0), shift_days, date_format)
            if shifted is None:
                stats["failed_dates"] += 1
                return match.group(0)
            stats["shifted"] += 1
            return shifted

        shifted_content = date_pattern.sub(_sub, content)

        # The write happens before the success checks below, and I have
        # run the case: a file with one good date and one impossible date
        # is written to the output with the good date shifted and the bad
        # one left in the clear, and only then does the run fail. In the
        # no output mode that same order overwrites the original file on
        # a failed run. The pattern also has no boundaries, so a date
        # shape inside a longer digit run is matched and shifted in place.
        if output_path:
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            output_file_path = os.path.join(output_path, os.path.basename(file_path))
        else:
            output_file_path = file_path # Overwrite input file

        with open(output_file_path, 'w', encoding=encoding) as f:
            f.write(shifted_content)

        if stats["failed_dates"]:
            logging.error(f"Failed to shift {stats['failed_dates']} date(s) in file: {file_path}")
            return stats
        if stats["shifted"] == 0:
            logging.error(f"No dates shifted in file: {file_path}")
            return stats

        stats["success"] = True
        logging.info(f"Processed file: {file_path} -> {output_file_path} ({stats['shifted']} date(s) shifted)")
        return stats

    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")
        return stats



def process_directory(input_path, shift_days, output_path, recursive, date_format):
    """
    Processes all files in a directory, optionally recursively.

    Returns aggregate stats: files seen, files succeeded, files
    failed or skipped, and total dates shifted.
    """
    aggregate = {"files": 0, "succeeded": 0, "failed": 0, "shifted": 0}
    if output_path and not os.path.exists(output_path):
        os.makedirs(output_path)

    for root, _, files in os.walk(input_path):
        for file in files:
            file_path = os.path.join(root, file)
            if not recursive and root != input_path:
                continue # Skip files in subdirectories if not recursive
            # Keep each subdirectory's files in the matching output
            # subdirectory. Writing by basename alone made two files with
            # the same name in different folders overwrite each other.
            target_dir = output_path
            if output_path and root != input_path:
                target_dir = os.path.join(output_path, os.path.relpath(root, input_path))
            result = process_file(file_path, shift_days, target_dir, date_format)
            aggregate["files"] += 1
            aggregate["shifted"] += result["shifted"]
            if result["success"]:
                aggregate["succeeded"] += 1
            else:
                aggregate["failed"] += 1
        if not recursive:
            break  # Only process the top-level directory
    return aggregate


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
        sys.exit(1)

    if shift_days is None:
        # One draw for the whole run, every file in a directory included,
        # drawn from a range that contains zero: a zero draw shifts every
        # date by nothing and each one still counts as shifted below. The
        # draw is unseeded, so the shift a run used exists only in the log
        # line that follows.
        shift_days = random.randint(-365, 365) # Random shift if not specified
        logging.info(f"Using random shift of {shift_days} days.")
    else:
        logging.info(f"Using shift of {shift_days} days.")
    
    if os.path.isfile(input_path):
        result = process_file(input_path, shift_days, output_path, date_format)
        if not result["success"]:
            logging.error(f"No dates shifted, or a file was skipped or failed, for: {input_path}")
            sys.exit(1)
    elif os.path.isdir(input_path):
        aggregate = process_directory(input_path, shift_days, output_path, recursive, date_format)
        logging.info(f"Files succeeded: {aggregate['succeeded']}, files failed or skipped: {aggregate['failed']}, dates shifted: {aggregate['shifted']}")
        if aggregate["files"] == 0:
            logging.error(f"No files found in directory: {input_path}. No dates shifted.")
            sys.exit(1)
        if aggregate["failed"] or aggregate["shifted"] == 0:
            logging.error("Run failed: a file was skipped or failed, or no dates were shifted.")
            sys.exit(1)
    else:
        logging.error(f"Invalid input path: {input_path}. Must be a file or directory.")
        sys.exit(1)


if __name__ == "__main__":
    main()