Documentation for WhoisXML API
MySQL binary dump loader scripts

Document version 1.0 dated 2017-07-24

Copyright (c) 2010-2021 Whois API LLC,  http://www.whoisxmlapi.com

The scripts are provided for our subscribers to load binary mysql dumps
obtained from our  quarterly feeds into MySQL  databases.  The scripts
can be used also as an example to create custom loader scripts.

Script availability:
--------------------

The primary location of this script is the public GitHub repository

https://github.com/whois-api-llc/whois_database_download_support

The script is located in the subdirectory

whoisxmlapi_percona_loaders

Contents:
---------

1. List of files

2. Obtaining data

3. Software environment

4. Using the script

1. List of files:
----------------

README			  : this file
load_mysql_utils.sh	  : utility functions used in all scripts
			    	This should be there in the same
				directory as the script itself.
load_whois_percona.sh:     : The script to run.
whoiscrawler_mysql_schema.sql : The schema file needed by the script.
			      By default it should be in the same directory
			      as the script.
legacy			: a directory containing legacy versions of
			  the script which were in use before July 2017.

2. Obtaining data
-----------------

Data files which can be loaded by these scripts can be obtained from

http://domainwhoisdatabase.com/whois_database/v20/database_dump/percona

(replace v20 by the actual version)

and for cctlds from

http://www.domainwhoisdatabase.com/domain_list_quarterly/v6/database_dump/percona/

(replace v6 by the actual version)

3. Software environment
-----------------------

The present version was tested with

mysql  Ver 14.14 Distrib 5.7.18

and

GNU bash, 4.3.48(1)-release

on a machine running Ubuntu Linux 16.4.02 LTS.

The scripts are standard ones which have to work with earlier versions
of bash  also on  other systems  (Linux, Mac OS  X, and  Windows).  It
should be compatible with other version of MySQL, too.

If you run into an incompatibility, please contact our support.

4. Using the script
-------------------

Step 1. : obtain data
.....................
We assume that you are working in the directory where this scripts and
the files listed in Section 1. reside.

Create a subdirectory for the data to be downloaded, say "whois_data"

Download the data from

http://domainwhoisdatabase.com/whois_database/v20/database_dump/percona/

(please replace v20 with the database version you are using)

into this directory. You need the files $tld.7z for the tld-s you are
interested in. You can use the provided md5 and sha sums to verify
your downloads.

Assume now, that you are interested in the domains "aaa" and "aarp",
so you have "aaa.7z" and "aarp.7z" in the directory "whois_data".

Step 2. Verify your files
.........................
This step can be omitted, but it is recommended to do it.
Run the following command-line in the script's directory:

./load_whois_percona.sh --import-data-dir=whois_data --tlds=aaa,aarp --db-version=v20 --verbose --dry-run

(--tlds should be replaced by the comma-separated list of tld-s you
are interested in, and you have to provide the version, v20 in our case.
--dry-run ensures that the script will not yet do anything with MySQL)

If the script does not report any error, you have all the required
data files. Notice also that the script has extracted the 7zipped data.

Step 3. Verify your database
............................

Please verify that the databases named "whoiscrawler_$dbver_$tld" do
not yet exist in your mysql. If they exist, please drop them.

Verify that you have a user in MySQL who can create tables, etc. The
easiest way is to use the root user. If you set up ~/my.cnf so that
the root user logs in without a password when issuing the "mysql"
command, you will not need to specify the mysql user and password.

In case of large domains, it is also recommended to make the fine
tuning settings on your database as described in the Reference Manual
of the database release.

Make sure that your mysql server stores its data in /var/lib/mysql .
If it stores them in some other directory, you will have to add the
--mysql-data-dir=DIRECTORY option to the command-line in the next
step, where DIRECTORY is the respective directory of your server.

During the load process the script has to restart your mysql server
several times. You are supposed to run it with a superuser so this
should be possible. The mysql stop and start commands are configured
in lines 25 and 26 of the script. By default we provide a standard
Linux setting which is the default of most Linux systems (and other
System V type UNIX-like systems). If you use an other platform, please
customize these lines (e.g. "net stop MySQL57" and "net start MySQL57"
on Windows.)

Step 4. Load the data
.....................

To load your data, do

sudo ./load_whois_percona.sh --import-data-dir=whois_data --tlds=aaa,aarp --db-version=v20 --verbose

You need to have write permission to mysql-s directory to succeed. The
easiest way is to run your script as root, e.g. with sudo, as above.
You may set up some less risky way to do it without sudo, however.

If your ~/my.cnf is not set up to enable the root user (or some other
user with database creation permissions), please use the --mysql-user
and --mysql-password options, too, in order to specify the required
username and password.

You will now have the data loaded into the respective databases.
