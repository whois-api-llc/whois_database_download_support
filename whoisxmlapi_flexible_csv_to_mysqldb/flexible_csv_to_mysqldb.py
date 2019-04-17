#!/usr/bin/env python3
import argparse
from argparse import RawTextHelpFormatter
import sys
import os
import re
import csv
import glob
import shutil
import tarfile
from concurrent.futures import ThreadPoolExecutor as TPE
from time import sleep
import gzip
import copy
import mysql.connector

# GlobalSettings
VERSION = "0.0.2"
MYNAME = sys.argv[0].replace('./', '')


def mysql_LIKE_value_format(s):
    s = s.replace('\\', '')
    s = re.sub('(\")', '\\"', s)
    s = re.sub('(\')', "\\'", s)
    return s


def mysql_LIKE_query_format(s):
    s = s.replace("_", "\\_")
    return s


def directory_check_or_create(directory):
    if os.path.exists(directory):
        if os.path.isfile(directory):
            return False
        elif os.path.isdir(directory):
            return True
    else:
        os.makedirs(directory)
        return True


def parse_arguments():
    parser = argparse.ArgumentParser(description='''Python script to load csvs whois records into one table of your mysql database.\n\n
                                                    A script for data feed subscribers of WhoisXML API\n
                                                    See usage examles in the supplied README file.''',
                                     prog='load_csvs_data', formatter_class=RawTextHelpFormatter)

    parser.add_argument('-v', '--version',
                        help='Print version information and exit.',
                        action='version', version=MYNAME + ' ver. ' + VERSION + '\n(c) WhoisXML API LLC.')

    parser.add_argument('--dry-run', action='store_true',
                        help='Check input files. After unpacking it should be CSV files with same set of headers.')
    parser.add_argument('--temp-dir', type=str, required=False, default='tmpcsv/',
                        help='''Temparary directory to unpack archives.
                                You need to have space to unpack all archives.
                                Default: "tmpcsv/"''')
    parser.add_argument("--threads", required=False, type=int, default=4,
                        help="Count of threads. Default: 4 threads.")

    # Mysql setup
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
    parser.add_argument('--mysql-table', type=str, default='whoisdata',
                        help='The name of the MySQL table to load data into. Default: "whoisdata".')
    parser.add_argument('--overwrite-mysql-table', action='store_true',
                        help='''Create or overwrite the table. 
                        IMPORTANT: If the table already exists it will DROP and CREATE it again.
                        REQUIRED if the table does not yet exist.''')
    parser.add_argument('--mysql-errors', action='store_true', help='Print wrong SQL inserts.')

    parser.add_argument('--all-fields-as-text', action='store_true',
                        help='If this option is specified, all the fields except id and domainName will be imported as type "text"')
    
    parser.add_argument('FILE', nargs='+',
                        help='''The CSV files to operate on. Also it can be path. 
                                All files have to be CSVs or archives with CSVs.''')

    args = parser.parse_args()
    return args


def mysql_query(process):
    def decorator(*args, **kwargs):
        try:
            db_settings = kwargs['db_settings']
            mysql_connection = mysql.connector.connect(**db_settings)
            cursor = mysql_connection.cursor()

            res = process(cursor=cursor, **kwargs)
        except Exception as e:
            print(str(e))
            res = None
        finally:
            cursor.close()
            mysql_connection.commit()
            mysql_connection.close()

        return res

    return decorator


@mysql_query
def get_database_list(database, **kwargs):
    query = 'SHOW DATABASES LIKE "{0}"'.format(database)
    query = mysql_LIKE_query_format(query)
    cursor = kwargs['cursor']
    try:
        cursor.execute(query)
    except:
        return []

    database_list = []
    for db in cursor:
        database_list.append(db[0])

    return database_list


@mysql_query
def is_table_exists(table, **kwargs):
    cursor = kwargs['cursor']
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{0}'
        """.format(table.replace('\'', '\'\'')))
    if cursor.fetchone()[0] == 1:
        return True

    return False


@mysql_query
def create_database(database, mysql_errors, **kwargs):
    query = 'CREATE DATABASE {0}'.format(database)
    cursor = kwargs['cursor']
    cursor.execute(query)

    return True


@mysql_query
def drop_table(table, mysql_errors, **kwargs):
    cursor = kwargs['cursor']
    query = 'DROP TABLE IF EXISTS `%s`' % table
    try:
        cursor.execute(query)
    except Exception as e:
        print(str(e))
        if mysql_errors:
            print(query)
        sys.exit('Unable to drop table.')
        
@mysql_query
def create_table(headers, table, mysql_errors, **kwargs):
    fields = []
    fields.append('`id` bigint(20) NOT NULL AUTO_INCREMENT')
    for field in headers:
        if 'domainName' == field:
            fields.append('`%s` varchar(256) DEFAULT NULL' % field)
        else:
            if args.all_fields_as_text:
                fields.append('`%s` TEXT DEFAULT NULL' % field)
            else:
                try:
                    fields.append('`%s` %s DEFAULT NULL' % (field, field_types[field]))
                except KeyError:
                    fields.append('`%s` TEXT DEFAULT NULL' % field)
    fields.append('PRIMARY KEY (`id`)')
    fields.append('KEY `domainName` (`domainName`)')

    cursor = kwargs['cursor']

    query = 'CREATE TABLE `{0}` ({1}) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8'.format(
        table, ', '.join(fields))
    try:
        cursor.execute(query)
    except Exception as e:
        print(str(e))
        if mysql_errors:
            print(query)
        sys.exit('Unable to create table.')


def nullify(L):
    """Convert empty strings in the given list to None."""

    # helper function
    def f(x):
        if (x == ''):
            return ''
        else:
            return x

    return [f(x) for x in L]


@mysql_query
def loadcsv(csvfile, table, mysql_errors, **kwargs):
    """
    Open a csv file and load it into a sql table.
    Assumptions:
     - the first line in the file is a header
    """
    print('Loading: %s.' % csvfile)

    cursor = kwargs['cursor']
    db_settings = kwargs['db_settings']

    with open(csvfile, encoding="utf8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        numfields = len(headers)

        query = buildInsertCmd(table, numfields)

        # ' INSERT INTO table (a,b,c) VALUES (1,2,3)'
        for row in reader:
            vals = []
            for field in headers:
                vals.append(mysql_LIKE_value_format(row[field]))

            vals = nullify(vals)
            values = list(headers)
            values.extend(vals)
            insert = query % tuple(values)
            try:
                cursor.execute(insert)
            except Exception as e:
                if mysql_errors:
                    print(str(e))
                    print(insert)

    print('Done: %s ' % csvfile)
    return


def check_and_create_table(csvfile, table, mysql_errors, **kwargs):
    with open(csvfile, encoding="utf8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        if not is_table_exists(table=table, **kwargs):
            create_table(headers=headers, table=table, mysql_errors=mysql_errors, **kwargs)
    return


@mysql_query
def get_table_fields(table, mysql_errors, **kwargs):
    cursor = kwargs['cursor']
    cursor.execute("SELECT * FROM %s LIMIT 0" % table)
    cursor.fetchone()
    field_names = [i[0] for i in cursor.description]
    return field_names


def is_table_have_same_set_of_headers(csvfile, table, mysql_errors, **kwargs):
    with open(csvfile, encoding="utf8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        table_headers = get_table_fields(table=table, mysql_errors=mysql_errors, **kwargs)
        table_headers.remove('id')

        if headers == table_headers:
            return True
    return False


def buildInsertCmd(table, numfields):
    """
    Create a query string with the given table name and the right
    number of format placeholders.
    example:
    >>> buildInsertCmd("foo", 3)
    'insert into foo values (%s, %s, %s)' 
    """
    assert (numfields > 0)
    placeholders_fields = (numfields - 1) * '%s, ' + '%s'
    placeholders = (numfields - 1) * '"%s", ' + '"%s"'
    query = "insert into %s (%s) values (%s)" % (table, placeholders_fields, placeholders)
    return query


def get_system_username():
    try:
        import pwd
    except ImportError:
        import getpass
        pwd = None

    if pwd:
        return pwd.getpwuid(os.geteuid()).pw_name
    else:
        return getpass.getuser()


def check_and_return_files(files):
    file_list = []
    for file in files:
        if os.path.isfile(file):
            file_list.append(file)
        if os.path.isdir(file):
            file_list.extend(glob.glob(os.path.join(file, '**/*'), recursive=True))
    file_list = [f for f in file_list if os.path.isfile(f)]
    file_set = set(file_list)
    return file_set


def get_csv_headers(csvfile):
    with open(csvfile, encoding="utf8") as f:
        reader = csv.DictReader(f)
        try:
            headers = reader.fieldnames
        except:
            return []
    return headers


def find_incorrect_csvs(csvfs, headers_of_first_csv):
    if not csvfs:
        return []
    csvf = csvfs.pop()
    headers = get_csv_headers(csvf)
    res = find_incorrect_csvs(csvfs, headers_of_first_csv)
    if headers_of_first_csv != headers:
        res.append(csvf)
    return res


if __name__ == "__main__":
    args = parse_arguments()

    #Set up the dictionary of fields if necessary
    if not args.all_fields_as_text:
        try:
            field_types_file = open(sys.path[0] + '/' + 'field_types.csv', 'r')
        except FileNotFoundError:
            sys.stderr.write("\nThe file 'field_types.csv' was not found next to the script.\n")
            sys.stderr.write("Put the file there or use the --all-fields-as-text option.\n\n")
        field_types = {}
        for field_record in field_types_file:
            field_record_split = field_record.split(',')
            field_types[field_record_split[0]]=field_record_split[1]
            
    file_set = check_and_return_files(args.FILE)

    # Removing temp dir if it exists.
    try:
        shutil.rmtree(args.temp_dir)
    except:
        pass

    directory_check_or_create(args.temp_dir)

    csvfs = []
    for i, file in enumerate(file_set):
        if file.lower().endswith('.tar.gz'):
            print('Unpacking .TAR.GZ archive: %s' % file)

            tmp_dir = os.path.join(args.temp_dir, str(i))
            directory_check_or_create(tmp_dir)

            tar = tarfile.open(file, 'r|gz')
            tar.extractall(tmp_dir)

            csvfs.extend(glob.glob(tmp_dir + '/**/*.csv', recursive=True))

        elif file.lower().endswith('.gz'):
            print('Unpacking .GZ archive: %s' % file)

            tmp_dir = os.path.join(args.temp_dir, str(i))
            directory_check_or_create(tmp_dir)

            csvf = os.path.join(tmp_dir, os.path.basename(file)[:-3])
            with gzip.open(file, 'rb') as f_in, open(csvf, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

            csvfs.append(csvf)

        else:
            print('CSV file: %s' % file)
            csvfs.append(file)

    csvfs.sort()

    if csvfs:
        standard_header = get_csv_headers(csvfs[0])
        print('Standard header CSV file: %s' % csvfs[0])
        incorrect_csvfs = find_incorrect_csvs(copy.deepcopy(csvfs), standard_header)
        if incorrect_csvfs:
            sys.exit('Error: Files with wrong headers: %s.' % ' '.join(incorrect_csvfs))

    if not args.dry_run and csvfs:

        db_settings = {'host': args.mysql_host,
                       'port': args.mysql_port,
                       'password': args.mysql_password,
                       }

        if args.mysql_user:
            db_settings['user'] = args.mysql_user
        else:
            db_settings['user'] = get_system_username()

        try:
            dbs = get_database_list(database=args.mysql_database, db_settings=db_settings)
        except:
            sys.exit('Error: Can\'t connect to MySQL server.')

        if args.mysql_database not in dbs:
            print('Database "%s" do not exist. Trying to create database.' % args.mysql_database)
            ret = create_database(db_settings=db_settings, database=args.mysql_database, mysql_errors=args.mysql_errors)
            if not ret:
                sys.exit('Error: Unable to create database "%s".' % args.mysql_database)

        db_settings['database'] = args.mysql_database

        if not args.overwrite_mysql_table:
            print('Adding whois records to existing table.')
            if not is_table_exists(db_settings=db_settings, table=args.mysql_table):
                sys.exit('MySQL table "%s" do not exists. Use --overwrite-mysql-table to create it.' % args.mysql_table)

        if args.overwrite_mysql_table:
            print('Droping table if it exists.')
            drop_table(db_settings=db_settings, table=args.mysql_table, mysql_errors=args.mysql_errors)
            print('Creating table "%s".' % args.mysql_table)
            check_and_create_table(db_settings=db_settings, csvfile=csvfs[0], table=args.mysql_table,
                                   mysql_errors=args.mysql_errors)
        else:
            result = is_table_have_same_set_of_headers(db_settings=db_settings, csvfile=csvfs[0], table=args.mysql_table,
                                                       mysql_errors=args.mysql_errors)
            if result:
                print('Existed table have same set of fields as input CSV file.')
            else:
                sys.exit('Existed table have another set of fields as input CSV file.\n' +
                         'Use --overwrite-mysql-table to recreate table with correct set of fields')

        executor = TPE(max_workers=args.threads)
        for csvf in csvfs:
            executor.submit(loadcsv, db_settings=db_settings, csvfile=csvf, table=args.mysql_table,
                            mysql_errors=args.mysql_errors)

        print('All archives was unpacked. CSV files put to the queues.')
        executor.shutdown()

    # Removing tar temp file
    print('Removing temp folder.')
    shutil.rmtree(args.temp_dir)

    if args.dry_run:
        print('Dry run status: Ok.')
