#!/usr/bin/env python3
"""
A script to load netblocks csv data into a MySQL database.
Consult the supplied documentation for details.
"""
import datetime
import sys
import os
import argparse
import pandas as pd
import mysql.connector as my
REMARKS_FIELD=True
try:
    import sqlescapy
except:
    sys.stdout.write('WARNING: Python package sqlescapy not installed. Will not import the "remark" fields.')
    REMARKS_FIELD = False

VERSION = "0.0.3"
MYNAME = sys.argv[0].replace('./', '')

parser = argparse.ArgumentParser(description='''
Python script to create or update a MySQL netblocks database
using WhoisXML API csv netblocks data. 
See usage examles in the supplied README file.''',
                                 prog='load_csvs_data',
                                 formatter_class=argparse.RawTextHelpFormatter)

# Mysql setup
parser.add_argument('--version',
                    help='Print version information and exit.',
                    action='version',
                    version=MYNAME + ' ver. ' + VERSION + '\n(c) WhoisXML API Inc.')
parser.add_argument('--quiet', action='store_true', help='Suppress all informative messages.')
parser.add_argument('--mysql-host', default='127.0.0.1', type=str,
                    help='Host name or IP address to reach MySQL server (optional). Default: localhost.')
parser.add_argument('--mysql-port', default='3306', type=str,
                    help='Port of MySQL database (optional). Default: 3306')
parser.add_argument('--mysql-user', type=str, default='',
                    help='User name to login to the MySQL database. Default: system user.')
parser.add_argument('--mysql-password', type=str, default='',
                    help='Password to login to the MySQL database')
parser.add_argument('--mysql-database', type=str, required=True,
                    help='The name of the MySQL database to load data into.')
parser.add_argument('--table-prefix', type=str, default='',
                    help='A string prefix added to the processed tables. Default: empty.')
parser.add_argument('--contacts-file', type=str, help=
                    'Name of the contacts file to load. Gzipped csv, as downloaded. Can be daily or full.')
parser.add_argument('--netblocks-file', type=str, help=
                    'Name of the netblocks file to load Gzipped csv, as downloaded. Can be daily or full. If full it is important to specify --full-netblocks-file')
parser.add_argument('--full-netblocks-file',
                    action='store_true', help='Netblocks file is a full one, not a daily update.')
parser.add_argument('--chunksize', type=int, help=
                    'Maximum size of chunks to be read from the file and committed into the DB at once. Default=500.000',
                    default=500000)
parser.add_argument('--nchunksmax', type=int, help=
                    'Number of chunks to load. Default=0, stands for all. Change for testing purposes.',
                    default=0)
parser.add_argument('--no-mysql-error-reports',
                    action='store_true', help='Do not print wrong SQL inserts.')
parser.add_argument('--no-inetnum-index', action='store_true',
                    help='Disable the creation of the index idx_inetnum on the inetnumFirst and inetnumLast field, which is needed for "BETWEEN"-based queries, for full netblocks files.')
parser.add_argument('--r-tree-index', action='store_true',
                    help='Add the column ip_poly to the netblocks table to support effeicient search using spatial R-tree index. It is recommended to add it to perform efficient queries, see docs.')



#parsing arguments
args = parser.parse_args()


def print_verbose(message):
    #Function to give some feedback
    if not args.quiet:
        sys.stderr.write(
            MYNAME + ' ' + datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S') + ': ' + message + '\n')
        sys.stderr.flush()

#Some minor checks: if any files
if args.contacts_file is not None:
    if not os.path.isfile(args.contacts_file):
        raise ValueError(
            'the specified contacts file "%s" does not exist'%args.contacts__file)
    print_verbose('Will load full contacts data from %s\n'%args.contacts_file)
if args.netblocks_file is not None:
    if not os.path.isfile(args.netblocks_file):
        raise ValueError(
            'the specified netblocks file "%s" does not exist'%args.netblocks_file)
    print_verbose('Will load netblocks data from %s\n'%args.netblocks_file)
    if args.full_netblocks_file:
        print_verbose('It is supposed to be a full netblocks file.')
    else:
        print_verbose('It is supposed to be a daily update netblocks file.')

        
#Contacts table config
contactsFieldnames = ['type', 'id', 'name', 'email', 'phone',
                      'country', 'city']
#A recommended estimate:
contactsSchema = {'type':('varchar', 16),
                  'id': ('varchar', 64),
                  'name':('varchar', 128),
                  'email':('varchar', 128),
                  'phone':('varchar', 64),
                  'country':('varchar', 32),
                  'city': ('varchar', 64)}
contactsSchemaPK = 'id'
contactsTableName = args.table_prefix + 'contacts'


#Netblocks table config (without ip_polygon)
netblocksFullFieldnames = ['inetnum', 'inetnumFirst', 'inetnumLast',
                    'as_number', 'as_name', 'as_route', 'as_domain', 'netname',
                    'modified', 'country', 'city', 'org_id', 'abuse_contacts',
                    'admin_contacts', 'tech_contacts', 'maintainers',
                    'domain_maintainers', 'lower_maintainers', 'routes_maintainers',
                    'source', 'remarks', 'as_type']
netblocksTableName = args.table_prefix + 'netblocks'
netblocksSchema = {'inetnum': ('varchar', 33),
                   'inetnumFirst': ('bigint', None),
                   'inetnumLast': ('bigint', None),
                   'as_number': ('integer', None),
                   'as_name': ('varchar', 64),
                   'as_route': ('varchar', 64),
                   'as_domain': ('varchar', 32),
                   'netname': ('varchar', 32),
                   'modified': ('date', None),
                   'country': ('varchar', 2),
                   'city': ('varchar', 16),
                   'org_id': ('varchar', 64),
                   'source': ('varchar', 8),
                   'remarks': ('text', None),
                   'as_type':('varchar', 32)}
netblocksSchemaPK = 'inetnum'
#Initial guess form ax lengths
inetnum_maxlength = 33
contact_maxlength = 64

#end config

def maxfieldlengths(fieldnames, data):
    """This returns the maximum field lengths of a tuple list"""
    maxlengths = {}
    for field in fieldnames:
        try:
            maxlengths[field] = max([len(record[field]) for record in data])
        except TypeError:
            maxlengths[field] = None
    return maxlengths

def fieldlengthsfromschema(tablename):
    """
    This returns data types, column names and
    maximum field lengths for the columns of the table
    """
    cursor.execute(
        "select COLUMN_NAME,DATA_TYPE,CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS where TABLE_NAME=%s and TABLE_SCHEMA=%s",
        (tablename, args.mysql_database,))
    columns = {}
    for column in cursor.fetchall():
        columns[column['COLUMN_NAME']] = (column['DATA_TYPE'], column['CHARACTER_MAXIMUM_LENGTH'])
    return columns


def createtablestring(tablename, schemadict, pkname):
    """This generates a "create table" ddl from the given schema"""
    ddlstring = 'CREATE TABLE %s(' % tablename
    comma = ''
    for colname in schemadict.keys():
        if schemadict[colname][1] is None:
            ddlstring += comma+"%s %s" % (colname, schemadict[colname][0])
        else:
            ddlstring += comma+"%s %s(%d) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci" % (
                colname, schemadict[colname][0], schemadict[colname][1])
        if colname == pkname:
            ddlstring += (' PRIMARY KEY ')
        comma = ', '
    ddlstring += ')'
    return ddlstring

def altertablestring(tablename, new_field_lengths):
    """
    Alter the table so that all the new records fit into it
    """
    from_current_schema = fieldlengthsfromschema(tablename)
    modifylist = []
    for fieldname in from_current_schema.keys():
        if from_current_schema[fieldname][1] is not None and \
           new_field_lengths[fieldname] > from_current_schema[fieldname][1]:
            modifylist.append((fieldname, from_current_schema[fieldname][0],
                               new_field_lengths[fieldname]))
    if modifylist != []:
        modifystring = 'ALTER TABLE %s ' % (tablename)
        comma = ''
        for coldata in modifylist:
            modifystring += comma
            modifystring += 'MODIFY %s %s(%s) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci' % coldata
            comma = ','
    else:
        modifystring = None
    return modifystring

#End of utility functions.

#Here we connect the database
print_verbose("Opening db connection.")
cnx = my.connect(user=args.mysql_user, password=args.mysql_password,
                 host=args.mysql_host, database=args.mysql_database,
                 port=args.mysql_port)

cursor = cnx.cursor(dictionary=True)
print_verbose("Turning off foreign key checks.")
cursor.execute("SET foreign_key_checks = 0")

#Load contacts data if file is given
if args.contacts_file != None:
    print_verbose("Inserting or updating contacts records.")
    nchunks = 0
    #we create the table for contats if it does not exist
    if fieldlengthsfromschema(contactsTableName) == {}:
        cursor.execute(createtablestring(contactsTableName, contactsSchema, contactsSchemaPK))

    for chunk in pd.read_csv(args.contacts_file, chunksize=args.chunksize, compression='gzip',
                             sep=',', parse_dates=True,
                             header=None, names=contactsFieldnames,
                             keep_default_na=False):
        chunklist = []
        for row in chunk.itertuples():
            record = {}
            for col in contactsFieldnames:
                record[col] = row.__getattribute__(col)
            chunklist.append(record)
        #Extend vachars if needed
        cursor.execute(
            altertablestring(contactsTableName, maxfieldlengths(contactsFieldnames, chunklist)))
        for row in chunklist:
            insertstring = 'REPLACE INTO %s (' % contactsTableName
            comma = ''
            for fieldname in contactsFieldnames:
                insertstring += comma +  fieldname
                comma = ','
            insertstring += ') VALUES('
            comma = ''
            for fieldname in contactsFieldnames:
                insertstring += comma+"'%s'" % row[fieldname].replace("'", "\\'")
                comma = ','
            insertstring += ')'
            try:
                cursor.execute(insertstring)
            except Exception as e:
                if not args.no_mysql_error_reports:
                    print('Error with: ', insertstring, ' : ', str(e))
        cnx.commit()
        print_verbose(
            'Committed chunk %d (%d records of max %d)\n' % (
                nchunks + 1, len(chunklist), args.chunksize))
        nchunks += 1
        if nchunks == args.nchunksmax:
            break

# Load actual netblocks data
if args.netblocks_file != None:
    #we create the table for contats if it does not exist
    nchunks = 0
    if fieldlengthsfromschema(netblocksTableName) == {}:
        cursor.execute(createtablestring(netblocksTableName, netblocksSchema, netblocksSchemaPK))
        cursor.execute(
            'alter table %s add foreign key(org_id) references contacts(id)'%netblocksTableName
        )
        if args.r_tree_index:
            cursor.execute(
                'alter table %s add column ip_poly polygon not null, add spatial index(ip_poly)'
                % netblocksTableName)
    #create connecting tables if they do not exist
    contacts_lists = {'abuse_contacts': [], 'admin_contacts': [], 'tech_contacts': [],
                      'maintainers': [], 'domain_maintainers': [],
                      'lower_maintainers':[], 'routes_maintainers': []}
    for contact_type in contacts_lists.keys():
        if fieldlengthsfromschema(args.table_prefix + contact_type) == {}:
            cursor.execute(
                'CREATE TABLE %s(inetnum varchar(33) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci, id varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci, primary key (inetnum, id), FOREIGN KEY(inetnum) REFERENCES %s(inetnum) , FOREIGN KEY(id) REFERENCES %s(id))' % (
                    args.table_prefix + contact_type, netblocksTableName, contactsTableName))
    #Set up the field names. If it is a daily file, we add 'action'
    file_fields = netblocksFullFieldnames
    if not args.full_netblocks_file:
        file_fields = ['action'] + file_fields
    for chunk in pd.read_csv(args.netblocks_file, chunksize=args.chunksize, compression='gzip',
                             sep=',', parse_dates=True,
                             header=None, names=file_fields,
                             keep_default_na=False):
        chunklist = []
        contacts_lists = {'abuse_contacts': [], 'admin_contacts': [], 'tech_contacts': [],
                          'maintainers': [], 'domain_maintainers': [],
                          'lower_maintainers':[], 'routes_maintainers': []}
        for row in chunk.itertuples():
            record = {}
            if args.full_netblocks_file:
                action = 'add'
            else:
                action = row.__getattribute__('action')
            if action == 'drop':
                record['inetnum'] = row.__getattribute__('inetnum')
                for contact_type in contacts_lists.keys():
                    #we add a single element, which will mean drop
                    contacts_lists[contact_type].append((record['inetnum']))
            else:
                for col in netblocksFullFieldnames:
                    record[col] = row.__getattribute__(col)
                chunklist.append(record)
                if inetnum_maxlength < len(record['inetnum']):
                    inetnum_maxlength = len(record['inetnum'])
                for contact_type in contacts_lists.keys():
                    for contact in [s.strip() for s in record[contact_type].split(' ')]:
                        if contact != '':
                            contacts_lists[contact_type].append((record['inetnum'], contact))
                            if contact_maxlength < len(contact):
                                contact_maxlength = len(contact)
        #Now we modify the connection tables if needed
        for contact_type in contacts_lists.keys():
            cursor.execute(
                altertablestring(
                    contact_type, {'inetnum': inetnum_maxlength, 'id': contact_maxlength}))
        cursor.execute(
            altertablestring(
                netblocksTableName, maxfieldlengths(netblocksFullFieldnames, chunklist)))
        #We have the data so we write them into the db
        #First we delete connectors for the records which will be deleted
        print_verbose("Deleting unnecessary contact links.")
        for contact_type in contacts_lists.keys():
            contact_tablename = args.table_prefix + contact_type
            for contact_row in contacts_lists[contact_type]:
                if len(contact_row) == 1:
                    insertstring = 'DELETE FROM %s WHERE inetnum=\'%s\' '% (
                        contact_tablename, contact_row[0])
                    try:
                        cursor.execute(insertstring)
                    except Exception as e:
                        if not args.no_mysql_error_reports:
                            print('Error with: ', insertstring, ' : ', str(e))
        #Now we add netblocks records
        print_verbose("Inserting, updating, and deleting netblock records.")
        for row in chunklist:
            if len(row) == 1:
                insertstring = "DELETE FROM %s WHERE inetnum='%s'" % (
                    netblocksTableName, row['inetnum'])
            else:
                insertstring = 'REPLACE INTO %s (' % netblocksTableName
                comma = ''
                for fieldname in netblocksFullFieldnames:
                    if fieldname in set(netblocksSchema.keys()):
                        insertstring += comma +  fieldname
                        comma = ','
                if args.r_tree_index:
                    insertstring += ', ip_poly) VALUES('
                else:
                    insertstring += ') VALUES('
                comma = ''
                for fieldname in netblocksFullFieldnames:
                    if fieldname in set(netblocksSchema.keys()):
                        if str(row[fieldname]).strip() == '':
                            insertstring += comma + 'Null'
                        else:
                            if netblocksSchema[fieldname][0] == 'varchar':
                                insertstring += comma + "'%s'" % row[fieldname].replace(
                                    "'", "\\'")
                            elif netblocksSchema[fieldname][0] == 'date':
                                insertstring += comma + datetime.datetime.strptime(
                                    row[fieldname], "%Y-%m-%dT%H:%M:%SZ").strftime(
                                        '\'%Y-%m-%d %H:%M:%S\'')
                            elif fieldname == 'remarks':
                                if REMARKS_FIELD:
                                    insertstring += comma + "'%s'" % sqlescapy.sqlescape(row['remarks'])
                                else:
                                    insertstring += comma + 'Null'
                            else:
                                insertstring += comma + "'%s'" % row[fieldname]
                        comma = ','
                if args.r_tree_index:
                    insertstring += ", ST_GEOMFROMWKB(ST_AsWKB(Polygon(LineString(Point(%f,-1),Point(%f,-1),Point(%f,1),Point(%f,1), Point(%f, -1)))),0)" % (
                        row['inetnumFirst'] - 0.5,
                        row['inetnumLast'] + 0.5,
                        row['inetnumLast'] + 0.5,
                        row['inetnumFirst'] -0.5,
                        row['inetnumFirst'] - 0.5)
                insertstring += ')'
            try:
                cursor.execute(insertstring)
            except Exception as e:
                if not args.no_mysql_error_reports:
                    print('Error with: ', insertstring, ' : ', str(e))
        #Now we fill in the contacts:
        print_verbose("Creating or updating contact links")
        for contact_type in contacts_lists.keys():
            contact_tablename = args.table_prefix + contact_type
            for contact_row in contacts_lists[contact_type]:
                if len(contact_row) == 2:
                    insertstring = 'REPLACE INTO %s(inetnum, id) VALUES(\'%s\', \'%s\')' % (
                        contact_tablename, contact_row[0], contact_row[1])
                    try:
                        cursor.execute(insertstring)
                    except Exception as e:
                        if not args.no_mysql_error_reports:
                            print('Error with: ', insertstring, ' : ', str(e))
        cnx.commit()
        print_verbose(
            'Committed chunk %d (%d records of max %d)\n' % (
                nchunks + 1, len(chunklist), args.chunksize))
        #limit chunks
        nchunks += 1
        if nchunks == args.nchunksmax:
            break


print_verbose("Turning on foreign key checks.")
cursor.execute("SET foreign_key_checks = 1")
if args.full_netblocks_file and not args.no_inetnum_index:
    print_verbose("Creating index on inetnumFirst, inetnumLast pairs (this may take some time).")
    try:
        cursor.execute(
            "CREATE INDEX %s_idx_inetnum ON %s(inetnumFirst, inetnumLast);"%(
                args.table_prefix, netblocksTableName))
    except Exception as e:
        if not args.no_mysql_error_reports:
            print('Error creating index:', str(e))

print_verbose("closing db connection.")
cnx.close()
