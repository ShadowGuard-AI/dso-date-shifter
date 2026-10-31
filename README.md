![Banner](banner.png)

# dso-date-shifter
Shifts all dates in a file (or directory of files) by a random or specified number of days. Useful for anonymizing time-series data or log files where exact timing is sensitive, while preserving temporal relationships. - Focused on Tools for sanitizing and obfuscating sensitive data within text files and structured data formats

## Install
`git clone https://github.com/ShadowStrikeHQ/dso-date-shifter`

## Usage
`./dso-date-shifter [params]`

## Parameters
- `-h`: Show help message and exit
- `-s`: Number of days to shift dates by. If not specified, a random shift between -365 and 365 days will be used.
- `-o`: No description provided
- `-r`: Process files in the input directory recursively.
- `-d`: The format of the dates in the files. Defaults to %%Y-%%m-%%d

## Behaviour
- Every date shape the search pattern matches is shifted: YYYY-MM-DD, YYYY/MM/DD, DD/MM/YYYY, DD-MM-YYYY, and two digit year forms such as DD/MM/YY. Each matched date is parsed with the format its own shape implies, using the `-d` format first when it fits, and is written back in the same shape. One shared shift applies to the whole run, so the spacing between dates is preserved.
- A matched date that cannot be parsed, for example 2024-13-45, counts as a failure of the run.
- Exit codes: the run exits 1 when any file is skipped or fails, when a matched date is left unshifted, when a run shifts zero dates, or when a directory holds no files. A run that shifts zero dates prints a plain no dates shifted line and no Processed success line. Exit 0 means at least one date was shifted and no file failed.
- With no `-o` output path, the input files are overwritten in place, as documented above. Use `-o` to keep the originals.

## License
Copyright (c) ShadowStrikeHQ
