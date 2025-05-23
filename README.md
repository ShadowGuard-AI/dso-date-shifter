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

## License
Copyright (c) ShadowStrikeHQ
