#!/usr/bin/env python2
#
#Script to load ASCII mysql dumps for a tld
#Provided for subscribers of quarterly whois data feeds
#
#Copyright (c) 2010-2021 Whois API LLC,  http://www.whoisxmlapi.com
#

import sys
import os

import argparse
from argparse import RawTextHelpFormatter

import easygui as g

import re

import gzip
import datetime

import mysql
import mysql.connector
from mysql.connector import errorcode

#GlobalSettings
VERSION = "0.0.3"
MYNAME = sys.argv[0].replace('./','')

#Default report frequency of mysql loading when verbose
REPORTFREQ = 1000

#---utility functions (they are here to have a single script)
#Note: we define simple logging functions instead of the use of
#the logging module, as that would be an overkill for this job.

#Logging functions
def print_error_and_exit(message):
    global DIALOG_COMMUNICATION
    if DIALOG_COMMUNICATION:
        _ = g.msgbox('Error. \n ' + message +'\nExiting.','WhoisXML API MySQL loader script')
        exit(1)
    else:
        sys.stderr.write('\nError: ' + message+'\n')
        sys.stderr.flush()
        exit(1)
def print_verbose(message):
    global VERBOSE
    global DEBUG
    if VERBOSE or DEBUG:
        print >> sys.stderr, message
        sys.stderr.flush()
def print_debug(message):
    global DEBUG
    if DEBUG:
        print >> sys.stderr, message
        sys.stderr.flush()
#File and directory utilites
def get_file(path, message):
    """Given a whatever path, verifies if it points to a file.
    If not, gives the error message and the path. 
    If yes,returns the file path"""
    thefile = os.path.normpath(path)
    if not os.path.isfile(thefile):
        print_error_and_exit(message +'\n (File specified: %s)' %(path))
    else:
        return(thefile)

def get_directory(path, message):
    """Given a whatever path, verifies if it points to a directory.
    If not, gives the error message and the path. 
    If yes,returns the file path as a pathlib object"""
    thefile = os.path.normpath(path)
    if not os.path.isdir(thefile):
        print_error_and_exit(message +'\n (Directory specified: %s)' %(path))
    else:
        return(thefile)

#Mysql utility functions
def execute_single_mysql_statement(dbcursor, statement, error_message):
    """Executes a single MySQL statement. If there is a problem, writes the given 
    message and the MySQL message to stderr and exits"""
    global DIALOG_COMMUNICATION
    global DRY_RUN
    
    if DRY_RUN:
        print_verbose("If I were not running dry, I'd execute the following db statement: %s" % statement)
    else:
        if DIALOG_COMMUNICATION:
            try:
                dbcursor.execute(statement)
            except:
                g.exceptionbox("MySQL error in the statemet %s. See the MySQL message below." % (statement), windowtitle)
                exit(1)
        else:
            try:
                print_debug("Executing the following db statement: %s" % statement)
                dbcursor.execute(statement)
            except (mysql.connector.Error) as e:
                print_error_and_exit("MySQL error. %s \n  MySQL said: '%s'" % (error_message, str(e.args)))

def load_gzipped_dumpfile(dbcursor, gzipped_dumpfile):
    """Loads a gzipped dumpfile through the cursor.
    Probably a better solution should be found, this is portable but not optimal"""

    global DRY_RUN
    global REPORTFREQ
    statement = ""
    blank=''
    find_comment = re.compile(r'--')
    find_incomplete = re.compile(r'[^-;]+;')
    nlines = 0
    try:
        for line in gzipped_dumpfile:
            nlines += 1
            if nlines % REPORTFREQ == 0:
                print_verbose("At %s loaded  %d lines\n" % (str(datetime.datetime.now()),nlines))
            if find_comment.match(line) or line.strip() is blank:  # ignore sql comment lines
                continue
            if not find_incomplete.search(line):  # keep appending lines that don't end in ';'
                statement += line
            else:  
                statement += line
                print_debug("Statement: %s" % (statement))
                if not DRY_RUN:
                    dbcursor.execute(statement)
                    statement = ""
    except:
        if DIALOG_COMMUNICATION:
            g.exceptionbox(
                "MySQL error in the statemet %s. Probably a bad sql file. See the MySQL message below.\n(Note: please care to drop the created database manually.)" % (statement), windowtitle)
            exit(1)
        else:
            raise
    if DRY_RUN:
        print_verbose("Not loading anything, dry run.")
                    
#---end of utiliy functions
#
if len(sys.argv) > 1 and sys.argv[-1].strip() != '--interactive':
    DIALOG_COMMUNICATION = False
    
    #command-line version, load_mysql_data.pyw has been started
    #Here we parse the command-line and get the values of the arguments
    parser = argparse.ArgumentParser(description='Python script to load mysql dumps into your mysql database\n\nA script for data feed subscribers of WhoisXML API\nSee usage examles in the supplied README file.', prog='load_mysql_data', formatter_class=RawTextHelpFormatter)
    #Vebosity, version, etc.
    parser.add_argument('--version',
                            help = 'Print version information and exit.',
                        action = 'version', version = MYNAME + ' ver. ' + VERSION +'\n(c) WhoisXML API LLC.')
    parser.add_argument('-v', '--verbose', help='Print messages. Recommended. \nIf not specifies, the script runs quietly,\nonly errors are reported.', action='store_true')
    parser.add_argument('-d', '--debug', help='Debug mode, even more messages', action='store_true')
    parser.add_argument('--interactive', help='Interactive mode. \nIf proivded as a first argument, \nyou will be prompted for the parameters in GUI dialogue windows.')
    #Mysql setup
    parser.add_argument('--mysql-user', help='User name to login to the MySQL database (optional)')
    parser.add_argument('--mysql-password', help='Password to login to the MySQL database (optional)')
    parser.add_argument('--mysql-database', help='The name of the MySQL database to load data into. \nNot to be used with the --tlds option\nbut needed for loading a single file')
    parser.add_argument('--mode', help='Operation mode (required). \nWhen "full", \nschema and data are loaded from a single file. \nWhen per_table, \ndata are loaded from separate table files', choices=['full', 'per_table'], required=True)
    parser.add_argument('--dump-file', help='The dump file to be used when loading full.\nNot to be used with the --tlds option')
    parser.add_argument('--schema-file', help='The schema file to be used \n when loading per_table.\nNot to be used with the --tlds option')
    parser.add_argument('--schema-files-directory', help='The schema file directory to be used \nwhen loading per_table.\nTo be used with the --tlds option only.')
    parser.add_argument('--table-files-directory', help='The directory where the dumps of all tables \nreside when loading per_table.\nIf used with --tlds, the table files for each tld \nshould reside in its $tld/tables subdirectory.')
    parser.add_argument('--tlds', help='load data for these tlds')
    parser.add_argument('--dump-files-dir', help='The dump files for the tld-s are in this directory. \nOnly for --tlds, both full and per_table')
    parser.add_argument('--db-version', help= 'The quarterly db version to load.\nRequired for --tld Format: vNN, e.g. v19')
    parser.add_argument('--schema-only', help='If specified, the table files are not loaded.', action='store_true')
    parser.add_argument('--data-only', help='Load data from table files \ninto an existing database \nwith already loaded schema', action='store_true')
    parser.add_argument('--no-create-db', help= 'Do not create the database(s) newly\n(should exists already)', action='store_true')
    parser.add_argument('--dry-run', help= 'Do not do anything,\njust verify the existence of the necessary files', action='store_true')
    args = parser.parse_args()
    args = vars(args)
else:
    args = {}
    #Interacitve version with easygui
    DIALOG_COMMUNICATION = True
    #Things you cannot do when interactive
    #Note: set the next two to True for console debug
    args['verbose'] = True
    args['debug'] = False
    #
    args['schema_only'] = False
    args['data_only'] = False
    args['no_create_db'] = False
    args['mysql_database'] = None
    args['dry_run'] = False
    #other defaults
    args['table_files_directory'] = None
    args['dump_files_dir'] = None
    args['schema_file'] = None
    args['dump_file'] = None
    args['tlds'] = None
    args['db_version'] = None
    
    #default window title
    windowtitle='WhoisXML API MySQL loader script'
    #let's start
    answer = g.msgbox('This is %s: a script to load  MySQL backups from quarterly feeds a MySQL databases. \n(C) WhoisXML API LLC.\n\nPlease make sure that the files are downloaded and you have a MySQL user on your machine who can create databases.\n\nPress O.K. to start.' % (MYNAME,), windowtitle)
    if answer == None:
        exit(6)
    #First of all, get mysql credentials
    answer = g.enterbox('Please enter your MySQL username (with database creation permissions, e.g. root)', windowtitle, default = 'root')
    if answer == None or answer == '':
        exit(6)
    args['mysql_user'] = answer
    answer = g.passwordbox('Please enter your MySQL password for user %s' % (args['mysql_user'],), windowtitle)
    if answer == None:
        exit(6)
    args['mysql_password'] = answer
    #quickly check mysql credentials to avoid work in vain
    try:
        mysql_config = {}
        mysql_config['user'] = args['mysql_user']
        mysql_config['password'] = args['mysql_password']
        dbconnection = mysql.connector.connect(**mysql_config)
        dbcursor=dbconnection.cursor()
        dbcursor.execute(
                "CREATE DATABASE {}".format('WhoisXMLAPI_TEST_DATABASE_TO_BE_DELETED'))
        dbcursor.execute(
            "DROP DATABASE {}".format('WhoisXMLAPI_TEST_DATABASE_TO_BE_DELETED'))
        dbconnection.close()
    except:
        g.exceptionbox("Something is wrong with your mysql credentials. See the mysql message below.", windowtitle)
        exit(6)
    _ = g.msgbox('Successfully logged in to MySQL,\ncreated and dropped a DB.\n\nMySQL credentials are O.K.\nPress O.K. to proceed')
    #decide mode
    choices=['Import sql dump file(s) containing schema + data in one file.', 'Import schema + tables from separate files.']
    answer = g.choicebox("What would you like to do?", windowtitle, choices)
    if answer == None:
        exit(6)
    if choices.index(answer) == 0:
        args['mode'] = 'full'
    else:
        args['mode'] = 'per_table'
    #decide whether the user want a single file
    choices = ['Specify the actual files for a tld with path.', 'Specify tlds and the directories where the files are.']
    answer = g.choicebox('How would you like to specify the input?', windowtitle,choices)
    if answer == None:
        exit(6)
    if choices.index(answer) == 0:
        filespecification = 'files'
    else:
        filespecification = 'tlds'
    if args['mode'] == 'full' and filespecification == 'files':
        #In this case we just need a single dump file
        answer = g.fileopenbox(title=windowtitle, msg='Please choose the gzipped dump file')
        if answer == None:
            exit(6)
        args['dump_file'] = answer
    if args['mode'] == 'per_table' and filespecification == 'files':
        #In this case we need a schema file and a tables directory
        answer = g.fileopenbox(title=windowtitle, msg='Please choose the gzipped schema file for loading')
        if answer == None:
            exit(6)
        args['schema_file'] = answer
        args['schema_files_directory'] = None
        answer = g.diropenbox(title=windowtitle, msg='Please choose the directory with the table files')
        if answer == None:
            exit(6)
        args['table_files_directory'] = answer
    #If tlds are specified, the user should keep the structure of the download folder
    if filespecification == 'tlds':
        _ = g.msgbox('In the following dialog box, please choose the directory where you have dowloaded your data. It should have a subdirectory for each tld named after the tld, with the schema and/or data files for each tld. Normally you should see subdirectiories named after tlds in the selection box when you are in the proper directory.', windowtitle)
        answer = g.diropenbox(title=windowtitle, msg='Please choose the directory with downloaded data')
        if answer == None:
            exit(6)
        downloaded_data_directory = answer
        #List the schema files and deduce the available tlds
        tlds = os.listdir(downloaded_data_directory)
        _ = g.msgbox('Note: if you do not see valid tld names to choose in the following dialog box, you made a bad choice in the previous window. Please cancel and start the program again in that case.', windowtitle)
        answer = g.multchoicebox('Please choose the tlds for which you want to load data.', windowtitle, tlds)
        if answer == None:
            exit(6)
        try:
            answer.remove('Add more choices')
        except:
            pass
        if len(answer) == 0:
            exit(6)
        #make a comma-separated string to be compatible with the command-line version
        tldslist = answer
        tldslist_underscore = {}
        for tld in tldslist:
            tldslist_underscore[tld] = tld.replace('.', '_')
        print tldslist_underscore
        tldsstr = tldslist[0]
        for tld in answer[1:]:
            tldsstr += ',' + tld
        args['tlds'] = tldsstr
        #Now we try to deduce the database version
        for tld in tldslist:
            samplefilenames = os.listdir(os.path.normpath(downloaded_data_directory + "/" + tld))
            print samplefilenames
            samplefilenames = filter(lambda x: re.search('whoiscrawler_v[0-9]+_' + tldslist_underscore[tld] + '.+sql.gz$', x), samplefilenames)
            if len(samplefilenames) == 0:
                print_error_and_exit('The specified directory does not contain files in the appropriate structure.')
            dbvers=[]
            for samplefilename in samplefilenames:
                try:
                    verstring = re.search(r'whoiscrawler_v[0-9]+_', samplefilename).group()
                    verstring = re.search(r'v[0-9]+', verstring).group()
                    dbvers.append(verstring)
                except:
                    print "Didnt match"
            dbvers = list(set(dbvers))
            if len(dbvers) != 1:
                print_error_and_exit('There are files from different database versions in your subdircetory.')
            args['db_version'] = dbvers[0]
        if args['mode'] == 'full':
            args['dump_files_dir'] = downloaded_data_directory
            args['dump_file'] = None
            args['schema_files_directory'] = None
            args['schema_file'] = None
        if args['mode'] == 'per_table':
            args['dump_files_dir'] = None
            args['dump_file'] = None
            args['schema_files_directory'] = downloaded_data_directory
            args['table_files_directory'] = downloaded_data_directory
            args['schema_file'] = None

#Uncomment the following 3 lines to debug dialogs:
#    _ = g.msgbox('All right. This was just the demo. If you like it, the script will have such an interface. Your choiches will be dumped to STDOUT and I will exit.', windowtitle)
#    print filespecification, args
#    exit(6)

#Global variables which influence the operation of the script
#Extensive messages (implies VERBOSE)
DEBUG = args['debug']
#More messages 
VERBOSE = args['verbose']
#Do everything without touching the database
DRY_RUN = args['dry_run']

#Echo args for debug
if DEBUG:
    print MYNAME,' was invoked with the arguments:', args

#Verify option dependencies and set up the configuration
load_mode=None
#If the user wants to load data, etc. from the same file:
if args['mode'] == 'full':
    #check for incompatible arguments
    if args['table_files_directory'] != None:
        print_error_and_exit('Inconsistent arguments: if --mode is "full", you cannot specify "table-files-directory"')
    if args['schema_file'] != None:
        print_error_and_exit('Inconsistent arguments: if --mode is "full", you cannot specify "schema-file"')
    if args['data_only'] or args['schema_only']:
        print_error_and_exit('Inconsistent arguments: if --mode is "full", you cannot load "schema-only" or "data-only"')
    #Distill file names to be used and verify file existence
    #check if the file is given directly
    if args['dump_file'] != None:
        if args['dump_files_dir'] != None or args['tlds'] != None or args['db_version'] != None:
            print_error_and_exit(
                'Inconsistent argumens: If you specify a dump file, do not use "--tlds", "--db-version" or "dump-files-dir"')
        tobeloaded={}
        #collect this file
        load_file = get_file(args['dump_file'], 'The specified database dump does not exist.')
        tobeloaded['firstfile']=load_file
        mysql_database=args['mysql_database']
        if mysql_database == None:
            mysql_database=os.path.basename(load_file).split('.')[0].replace('_mysql', '').replace('_schema', '')
        if mysql_database == '':
            print_error_and_exit('Cannot determine MySQL database name')
        tobeloaded['mysql_database'] = mysql_database
        tobeloaded['next_files'] = []
        stufftoload = [tobeloaded]
    else:
        #if we are here, the tlds, db_version, etc are defined
        tlds=args['tlds'].split(",")
        #dictionary to make potentially dotted tlds underscored
        tlds_underscore = {}
        for tld in tlds:
            tlds_underscore[tld] = tld.replace('.', '_')
        print_verbose("Tlds to load: " + str(tlds))
        dbver = args['db_version']
        if dbver == None:
            print_error_and_exit("You have not specified the database version. Please use --db-version.")
        if re.match(r'^v[0-9]+$', dbver) == None:
            print_error_and_exit("Invalid database version specification. Should be vNN, e.g. v6 or v20")
        print_verbose("Database version: %s " % dbver)
        filesdir = get_directory(args['dump_files_dir'], "The specified database dump directory does not exist.")
        stufftoload=[]
        for tld in tlds:
            thistld={}
            #the file
            #the four lines below are a quick and dirty solution to support cctld data in which files are named domains_whoiscrawler*
            thisfile = os.path.join(os.path.join(filesdir, tld),'whoiscrawler_'+ dbver + "_" + tld+'_mysql.sql.gz')
            nameprefix=''
            if not os.path.isfile(thisfile):
                thisfile = os.path.join(os.path.join(filesdir, tld),'domains_whoiscrawler_'+ dbver + "_" + tlds_underscore[tld] + '_mysql.sql.gz')
                nameprefix='domains_'
            if not os.path.isfile(thisfile):
                print_error_and_exit('Data file for tld "%s" does not exist' % (tld,))
            else:
                thistld['firstfile']=thisfile
            #the database
            thistld['mysql_database'] = nameprefix + 'whoiscrawler_' + dbver + '_' + tlds_underscore[tld]
            thistld['next_files'] = []
            stufftoload.append(thistld)
#Processing for per_table mode           
if args['mode'] == 'per_table':
    #check for incompatible arguments
    if args['table_files_directory'] == None:
        print_error_and_exit('You must specify table-files-directory when loading per table')
    if args['dump_file'] != None:
        print_error_and_exit('Inconsistent arguments: if --mode is "per_table", \nyou cannot specify "dump-file"')
    #This is an xor below:
    if (args['tlds'] != None) == (args['schema_file'] != None):
        print_error_and_exit('Inconsistent arguments: please use either --tlds or --schema-file')
    if (args['tlds'] != None) == (args['schema_files_directory'] == None):
        print_error_and_exit('Inconsistent arguments: if --mode is "per table" and you use --tlds, please also provide --schema-files-dir')
    if args['tlds'] != None and args['mysql_database'] != None:
        print_error_and_exit('Inconsistent arguments: when loading with --tlds, \nyou cannot specify the database,\nit defaults to "whoiscrawler_$version_$tld"')
    #Checking for the existence of schema files and collecting them
    thistld={}
    if args['schema_file'] != None:
        print_debug("Loading per_table from given files.")
        #Get schema file
        thistld['firstfile'] = get_file(args['schema_file'], 'The specified schema_file does not exist')
        #Determine the database name
        mysql_database=args['mysql_database']
        if mysql_database == None:
            #if not given, generating from the schema file name
            mysql_database=os.path.basename(thistld['firstfile']).split('.')[0].replace('_mysql', '').replace('_schema', '')
        if mysql_database == '':
            print_error_and_exit('Cannot determine MySQL database name')
        thistld['mysql_database'] = mysql_database
        print_verbose('Deduced MySQL database name: %s' % (mysql_database,))
        #Get table files
        tablefiles = os.listdir(os.path.normpath(args['table_files_directory']))
        tablefiles = filter(lambda x: re.search(r'^.+_mysql.sql.gz$', x), tablefiles)
        tablefiles.sort()
        tablefiles = [os.path.normpath(os.path.join(args['table_files_directory'], x)) for x in tablefiles]

        if len(tablefiles) != 4:
            print_error_and_exit("Not all of the required table files are found. Please verify the table files directory")
        print_verbose("All %d table files found." % (len(tablefiles)))
        print_debug("Table files: %s" % (str(tablefiles)))
        thistld['next_files'] = tablefiles
        stufftoload = [thistld]
    else:
        print_debug("Loading per_table with tlds")
        #This is when tld, db version, etc. are defined, and we are loading per_table
        tlds=args['tlds'].split(",")
        #dictionary to make potentially dotted tlds underscored
        tlds_underscore = {}
        for tld in tlds:
            tlds_underscore[tld] = tld.replace('.', '_')
        print_verbose("Tlds to load: " + str(tlds))
        dbver = args['db_version']
        if dbver == None:
            print_error_and_exit("You have not specified the database version. Please use --db-version.")
        if re.match(r'^v[0-9]+$', dbver) == None:
            print_error_and_exit("Invalid database version specification. Should be vNN, e.g. v6 or v20")
        print_verbose("Database version: %s " % dbver)
        stufftoload=[]
        for tld in tlds:
            thistld={}
            schemadir = get_directory(args['schema_files_directory'],"Schema files directory not found")
            #the file
            thisfile = os.path.join(os.path.join(schemadir, tld),'whoiscrawler_'+ dbver + "_" + tlds_underscore[tld]+'_mysql_schema.sql.gz')
            #The few lines before are a quick and dirty solution to support the different naming conventions of cctlds
            nameprefix=''
            if not os.path.isfile(thisfile):
                #cctld case
                thisfile = os.path.join(os.path.join(schemadir, tld),'domains_whoiscrawler_'+ dbver + "_" + tlds_underscore[tld]+'_mysql_schema.sql.gz')
                nameprefix='domains_'
            if not os.path.isfile(thisfile):
                print_error_and_exit('Schema file for tld "%s" not found at %s' % (tld,str(thisfile)))
            else:
                thistld['firstfile']=thisfile
            #the database
            thistld['mysql_database'] = nameprefix + 'whoiscrawler_' + dbver + '_' + tlds_underscore[tld]
            #table files
            tablefiles = os.listdir(os.path.normpath(os.path.join(os.path.join(args['table_files_directory'], tld),'tables')))
            tablefiles = filter(lambda x: re.search(r'^.+_mysql.sql.gz$', x), tablefiles)
            tablefiles.sort()
            tablefiles = [os.path.normpath(os.path.join(os.path.join(os.path.join(args['table_files_directory'], tld), 'tables'), x)) for x in tablefiles]
            print tablefiles
            if len(tablefiles) != 4:
                print_error_and_exit(
                    "Not all of the required table files are found for tld %s. Please verify the table files directory" %
                    (tld))
            print_verbose("All %d table files found for tld %s." % (len(tablefiles), tld))
            print_debug("Table files: %s" % (str(tablefiles)))
            thistld['next_files'] = tablefiles
            stufftoload.append(thistld)

print_debug("Stuff to load: %s" % (str(stufftoload)))
print_verbose("Data for %d tlds found and will be loaded into the database." % len(stufftoload))
    
#By now we found what and where to load

#Database connection setup
if not DRY_RUN:
    mysql_config = {}
    if args['mysql_user'] != None:
        mysql_config['user'] = args['mysql_user']
    if args['mysql_password'] != None:
        mysql_config['password'] = args['mysql_password']
    try:
        if mysql_config == {}:
            #TODO
            print_error_and_exit('Reading my.cnf not yet implemented. Please specify a MySQL user and password')
        else:
            dbconnection = mysql.connector.connect(**mysql_config)

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print_error_and_exit("Something wrong with MySQL credentials")
        else:
            print_error_and_exit("MySQL error")
    dbcursor=dbconnection.cursor()
    print_verbose("Testing MySQL connection: OK")
    if not args['no_create_db']:
        #in this case our user has to be able to create a database
        try:
            execute_single_mysql_statement(dbcursor,
                "CREATE DATABASE {}".format('WhoisXMLAPI_TEST_DATABASE_TO_BE_DELETED'), "The specified db user cannot create databases. Please grant or use --no-create-db ")
            execute_single_mysql_statement(dbcursor,
                "DROP DATABASE {}".format('WhoisXMLAPI_TEST_DATABASE_TO_BE_DELETED'), "The specified db user cannot create databases. Please grant or use --no-create-db ")
        except mysql.connector.Error as err:
            print("The specified db user cannot create databases. Please grant or use --no-create-db".format(err))
            print_debug("MySQL_error: {}".format(err))
            exit(1)
    print_verbose("Testing If user can create DB: OK")

else:
    #dry run
    dbcursor=None
#Now our db connection is O.K., so we can do the main job.
real_job_start = datetime.datetime.now()
for tobeloaded in stufftoload:
    mysql_database=tobeloaded['mysql_database']
    print_verbose('MySQL database to be used: %s' % (mysql_database))
    if DIALOG_COMMUNICATION:
        answer=g.ynbox("Will now create and populate the database %s.\nIs this right?\n\nNote: if you say yes, I shall start working and all dialogs will disappear. I will work quietly and won't bother you with any windows unless someting comes up. For large tlds this will take a lot of time." %(mysql_database))
        if not answer:
            exit(1)
    #creating database if needed
    if not args['no_create_db']:
        execute_single_mysql_statement(dbcursor,
                                       "CREATE DATABASE {}".format("`"+mysql_database+"`"),
                                           "Cannot create the required db. Probably it exists already.")
        print_verbose('Database created.')

        #Use database
        execute_single_mysql_statement(dbcursor,
                                       "USE {}".format("`"+mysql_database+"`"),
                                       "The required database does not exist")

        #Now the real job: load the dump
        sqlfile_path=tobeloaded['firstfile']
        print_debug('File path to open: %s' % (sqlfile_path))
        now = datetime.datetime.now()
        print_verbose('Loading file %s starting at %s' % (sqlfile_path, str(now)))
        sqlfile=gzip.open(sqlfile_path,'r')
        load_gzipped_dumpfile(dbcursor, sqlfile)
        sqlfile.close()
        print_verbose('File %s loaded at %s, it took %s' % (sqlfile_path, str(now), str(datetime.datetime.now()-now)))
        #Now loading all remaining files
        for additionalfile in tobeloaded['next_files']:
            sqlfile_path=additionalfile
            print_debug('File path to open: %s' % (sqlfile_path))
            now = datetime.datetime.now()
            print_verbose('Loading file %s starting at %s' % (sqlfile_path, str(now)))
            sqlfile = gzip.open(sqlfile_path,'r')
            load_gzipped_dumpfile(dbcursor, sqlfile)
            sqlfile.close()
            print_verbose('File %s loaded at at %s, it took %s' % (sqlfile_path, str(now), str(datetime.datetime.now()-now)))

print_verbose(MYNAME + ' has finished at %s. \nTotal time of loading: %s' % (str(datetime.datetime.now()), str(datetime.datetime.now()-real_job_start)))
#Main job done
#closing db conn
if not args['dry_run']:
    dbconnection.close()
#If we are using dialogs, we say goodbye to the user
if DIALOG_COMMUNICATION:
    _ = g.msgbox("%s has finished its activity in %s time.\nAll data have been loaded.\nPress OK to close this window." %(MYNAME,  str(datetime.datetime.now()-real_job_start)), windowtitle)


