Documentation for the WhoisXML API

WHOIS CSV to JSON converter scripts

Copyright (c) 2010-2017 Whois API LLC,  http://www.whoisxmlapi.com
-------------------------------------------------------------------

The scripts are provided for our subscribers.

The aim of the script is to convert WHOIS data downloaded in CSV
format to JSON.

It is a cross-platform solution for end-users. It should be used on
Windows and Linux/Unix type systems and does not require special
experience.

The user should be familiar, however, with the feeds and data formats,
which are described in the reference manuals of the respective feeds.

Script availability:
--------------------

The primary location of this script is the public GitHub repository

https://github.com/whois-api-llc/whois_database_download_support

The scripts are located in the subdirectory

whoisxmlapi_csv2json

Contents
--------

1. Quickstart
2. Options of transform_json.py
3. A less portable verbose version: transform_json_verbose.py
4. Output file format

1. Quickstart
-------------

The fastest way of using the script is the following:

- Make sure you have either Python 2 (tested with 2.7.10) or Python 3
  installed and working on your system. 

- Install the following Python packages:

  argparse, csv, multiprocessing, json
  
  You can do it with pip, Python's package manager 
  ("pip install <package name>" in a command-line)
  or with the package manager of your system.

- Download "simple", "regular" or "full" CSV files from WhoisXML API
  data feeds. You can use this script with files from quarterly
  databases as well as daily feeds. 

  Consult the documentation of WhoisXML API data download products 
  for more information. The manuals are available from

  http://www.domainwhoisdatabase.com/docs/

- Having your CSV files in a given directory, say "foo/", you can
  convert them to JSON by using the script in command-line the
  following way:
  
  transform_json.py -i foo/
  
  The script will not produce any output. 
  Depending on the number of files, the process may take a
  longer time.
  
  The JSON files will be next to their CSV counterparts with the same
  basename.

2. Options of transform_json.py
-------------------------------

The script is self-documenting, you can obtain the description with 

  transform_json.py --help

The output lists the options:
---
usage: transform_json.py [-h] [--version] -i PATH [--key KEY]
                         [--threads THREADS] [--force] [--human-readable]

Convert CSV to JSON format

optional arguments:
  -h, --help            show this help message and exit
  --version             Print version information and exit.
  -i PATH, --path PATH  input directory with uncompressed CSVs or single CSV
                        file
  --key KEY             primary key field for records, default "domainName"
  --threads THREADS     number of threads, default 1
  --force               overwrite existent files
  --human-readable      generate human readable output

--
Comments:

- The script supports multi-threaded operation with the --threads option.
- The --human-readable option results in JSON files well-readable as text.
- See also the description of the output file format in Section 

3. A less portable verbose version: transform_json_verbose.py
-------------------------------------------------------------

If you want to follow the progress of the conversion, there is another
script available under the name "transform_json_verbose.py".

It requires Python 3 and an additional python package, "tqdm", to work.

In addition to the options of transform_json.py, this script produces
a verbose output by default:

-A progress bar showing the status of the reading of files.

-A message about writing JSON files.

These can be suppressed by the 

--no-progress

and 

--quiet 

options respectively. 

Apart from this, the operation of the script is the same as that of
transform_json.py.

4. Output file format
---------------------

The resulting file contains a single JSON string. Within this at first
level, there is each record as a value in a key-value pair, where the
key is the filed specified by the --key option of the scripts, the
domain name by default. In the value, the non-empty fields of the
record appear as key-value pairs.

If the --human-readable option was set, the file contains proper
indentations and newlines to be well readable as plain text. Without
the option, a JSON file for machine processing is obtained.
