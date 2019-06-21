#!/usr/bin/env python3
"""
A sampe script to populate a Website Contacts and Categories 
MySQL database from WhoisXML API data.
(c) WhoisXML API, Inc. 2019.
"""

import sys
import os
import binascii
import datetime
import argparse
import gzip
import pandas as pd
import mysql.connector as my

VERSION = "0.0.1"
MYNAME = sys.argv[0].replace('./', '')

parser = argparse.ArgumentParser(description='''
A sampe script to populate a Website Contacts and Categories 
MySQL database from WhoisXML API data.
See usage examles in the supplied README file.''',
                                 prog=MYNAME,
                                 formatter_class=argparse.RawTextHelpFormatter)

# Mysql setup
parser.add_argument('--version',
                    help='Print version information and exit.',
                    action='version',
                    version=MYNAME + ' ver. ' + VERSION + '\n(c) WhoisXML API Inc.')
parser.add_argument('--quiet', action='store_true', help='Suppress all informative messages.')
parser.add_argument('--mysql-host', default='127.0.0.1', type=str,
                    help='Host name or IP address to reach MySQL server (optional). Default: Localhost.')
parser.add_argument('--mysql-port', default='3306', type=str,
                    help='Port of MySQL database (optional). Default: 3306')
parser.add_argument('--mysql-user', type=str, required=False, default='',
                    help='User name to login to the MySQL database. Default: system user.')
parser.add_argument('--mysql-password', type=str, required=True, default='',
                    help='Password to login to the MySQL database')
parser.add_argument('--mysql-database', type=str, required=True,
                    help='The name of the MySQL database to load data into.')
parser.add_argument('--mysql-errors', action='store_true', help='Print wrong SQL inserts.')
parser.add_argument('--chunksize', type=int, help=
                    'Maximum size of chunks to be read from the file and committed into the DB at once. Default=100.000',
                    default=100000)
parser.add_argument('--nchunksmax', type=int, help=
                    'Number of chunks to load. Default=0, stands for all. Change for testing purposes.',
                    default=0)
parser.add_argument('--jsonl-file', type=str, required=True,
                    help='The jsonl file to load')
parser.add_argument('--categories-only', action='store_true', help='Categories only file. No contact info included.')
args = parser.parse_args()



def print_verbose(message):
    #Function to give some feedback
    if not args.quiet:
        sys.stderr.write(
            MYNAME + ' ' + datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S') + ': ' + message + '\n')
        sys.stderr.flush()

def is_gz_file(filepath):
    #Check if the file is gzipped by checking it magic number
    with open(filepath, 'rb') as test_f:
        return binascii.hexlify(test_f.read(2)) == b'1f8b'
        
def getfield(dataobj, field_name):
    """Get the field from a data object
    or return None if it does not exist
    or is an empty string."""
    try:
        result = dataobj.__getattribute__(field_name)
    except AttributeError:
        result = None
    try:
        if result.isspace():
            result = None
    except AttributeError:
        pass
    return(result)

def getdictval(dictionary, key):
    """Get a value from a dictionary or None if 
    does not exist or is an empty string."""
    try:
        result = dictionary[key]
    except KeyError:
        result = None
    if not result or not result.strip():
        result = None
    return(result)
    
#Some minor checks: if any files
if args.jsonl_file is not None:
    if not os.path.isfile(args.jsonl_file):
        raise ValueError(
            'the specified file "%s" does not exist'%args.jsonl_file)
    print_verbose('Will load data from %s\n'%args.jsonl_file)


#Here we connect the database
print_verbose("Opening db connection.")
cnx = my.connect(user=args.mysql_user, password=args.mysql_password,
                 host=args.mysql_host, database=args.mysql_database,
                 port=args.mysql_port)
cnx.set_charset_collation(charset='utf8mb4', collation='utf8mb4_unicode_ci')
#Defining the cursor
cursor = cnx.cursor(dictionary=True)
print_verbose("Turning off foreign key checks.")
cursor.execute("SET foreign_key_checks = 0")

#Main job: inserting data
nerrors = 0
nchunks = 0
nrecords = 0
#Opening input file
if is_gz_file(args.jsonl_file):
    print_verbose('Opening gzipped input file %s'%args.jsonl_file)
    infile = gzip.open(args.jsonl_file, 'rt', encoding='utf-8')
else:
    print_verbose('Opening input file %s'%args.jsonl_file)
    infile = open(args.jsonl_file, 'rt')
for chunk in pd.read_json(infile, chunksize=args.chunksize, lines=True, encoding='UTF-8'):
    records = [r for r in chunk.itertuples()]
    for r in records:
        #Main fields
        main_data = [getfield(r, 'domainName'), getfield(r, 'countryCode')]
        if main_data[0] is None:
            print_verbose("Record error: undefined domain name in "+ str(r))
            error_count += 1
            continue
        if args.categories_only:
            cursor.execute(
                'INSERT INTO domain(domainName, countryCode) values(%s,%s)',
                main_data)
            recordid=cursor.lastrowid
        else:
            #Meta fields
            main_data.append(getdictval(getfield(r, 'meta'), 'title'))
            main_data.append(getdictval(getfield(r, 'meta'), 'description'))
            #socialLinks fields
            main_data.append(getdictval(getfield(r, 'socialLinks'), 'facebook'))
            main_data.append(getdictval(getfield(r, 'socialLinks'), 'googlePlus'))
            main_data.append(getdictval(getfield(r, 'socialLinks'), 'instagram'))
            main_data.append(getdictval(getfield(r, 'socialLinks'), 'twitter'))
            main_data.append(getdictval(getfield(r, 'socialLinks'), 'linkedIn'))
            cursor.execute(
                'INSERT INTO domain(domainName, countryCode, meta_title, meta_description, socialLinks_facebook, socialLinks_googlePlus, socialLinks_instagram, socialLinks_twitter, socialLinks_linkedIn) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                main_data)
            recordid=cursor.lastrowid
            #Child records
            #emails
            for child in getfield(r, 'emails') or []:
                cursor.execute(
                    'INSERT INTO email(domainID, description, email) VALUES(%s,%s,%s)', (
                        recordid,
                        getdictval(child, 'description'),
                        getdictval(child, 'email')))
            #phone numbers
            for child in getfield(r, 'phones') or []:
                cursor.execute(
                    'INSERT INTO phone(domainID, description, phoneNumber, callHours) VALUES(%s,%s,%s,%s)', (
                        recordid,
                        getdictval(child, 'description'),
                        getdictval(child, 'phoneNumber'),
                        getdictval(child, 'callHours')))
            #postal addresses    
            for child in getfield(r, 'postalAddresses') or []:
                cursor.execute(
                    'INSERT INTO postalAddress(domainID, postalAddress) VALUES(%s,%s)', (
                    recordid,
                    child))
            #company names
            for child in getfield(r, 'companyNames') or []:
                cursor.execute(
                    'INSERT INTO companyName(domainID, companyName) VALUES(%s,%s)', (
                    recordid,
                    child))
        #Now upserting category
        for child in getfield(r, 'categories') or []:
            cursor.execute(
                'INSERT IGNORE INTO category(category) VALUES(%s)',
                (child,))
            cursor.execute(
                'INSERT INTO domain_category(categoryID, domainID) VALUES(%s, %s)',
                (child, recordid))
        nrecords += 1
    cnx.commit()
    print_verbose(
        'Committed chunk %d (%d records of max %d)\n' % (
            nchunks + 1, len(records), args.chunksize))
    nchunks += 1
    if nchunks == args.nchunksmax:
        break
    
print_verbose("Committed %d records into domains"%nrecords)
print_verbose("Total number of errors: %d "%nerrors)
print_verbose("Closing input file")
infile.close()
print_verbose("Turning on foreign key checks.")
cursor.execute("SET foreign_key_checks = 1")
print_verbose("closing db connection.")
cnx.close()

