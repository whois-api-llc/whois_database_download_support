Documentation for the WhoisXML API

MySQL ASCII dump loader Python script

load_mysql_data.py

Document version 1.0 dated 2017-07-27

Copyright (c) 2010-2017 Whois API LLC,  http://www.whoisxmlapi.com

The script is  provided for our subscribers to load  ASCII MySQL dumps
obtained from our quarterly feeds into MySQL databases.

It is  a cross-platform solution for  end-users. It should be  used on
Windows  and Linux/Unix  type  systems and  does  not require  special
experience apart from the ability to use MySQL.

Script availability:
--------------------

The primary location of this script is the public GitHub repository

https://github.com/whois-api-llc/data_feed_and_database_support

The script is located in the subdirectory

whoisxmlapi_mysql_loaders

In addition, WhoisXML API subscribers can access the scripts from the
following URLs:

From the quarterly gtld sample and production URLs, versions from v19 or above:

http://domainwhoisdatabase.com/whois_database/sample/gtlds/$ver/mysql_loader_scripts
http://domainwhoisdatabase.com/whois_database/$ver/docs/mysql_loader_scripts

From the quarterly cctld sample and production URLs, versions from v5 or above:

http://domainwhoisdatabase.com/whois_database/sample/cctlds/$ver/mysql_loader_scripts
http://domainwhoisdatabase.com/domain_list_quarterly/$ver/docs/mysql_loader_scripts

(Please replace $ver with the appropriate version, e.g. v5 or v20 .)

Contents
--------
1. Installation
2. Obtaining data to be loaded
3. Basic use
4. Advanced use

1. Installation
---------------

In  what follows  we  describe how  to make  the  script working.  The
installation takes a few minutes only.

The script itself does not need installation, it runs from anywhere if
its dependencies  are met. All  software needed  to run the  script is
free on  each platform. So  if you are  using other Python  scripts of
WhoisXML  API,  it  is  possible  that  you do  not  have  to  do  any
installation, just start the scripts.  You may just try starting it by
double  clicking (Windows)  or running  it from  command-line (do  not
forget to ensure execution permissions, aka. load_mysql_data.py.

Step 1. MySQL setup

Make sure that you have a MySQL database installed and running and you
have  a MySQL  user who  is able  to create  databases. Typically  the
"root" user should be used for the purpose.

The  present  script was  developed  and  tested using  the  following
versions of mysql:

- MySQL  Ver 14.14 Distrib 5.7.19, for Linux (x86_64)
- MySQL Community Server (GPL) ver. 5.7.17-log on Windows 10 64 bit

It should, however, work with earlier versions (5.1+) of MySQL, too.

In  a  production environment  use  the  solution with  caution,  make
backups of  your relevant databases  in advance. (The script  does not
drop databases, however, it does not  verify the contents of the files
to be  loaded, so using it  with other files than  the ones downloaded
from WhoisXML API can be a security risk.)

Step 2: Install Python

The  script has  been developed  with Python  2.7.12 and  it has  been
tested  with Python  2.7.13  on  Windows. It  should  work with  newer
versions  of series  2 Python,  and it  is likely  that it  works with
earlier versions of the 2.7. series  (It is reported to work e.g. with
2.7.10 and 2.7.11).

-On Linux systems, use your package manager, e.g. "apt-get install python".
-On Windows systems, download the installer from
    www.python.org, series 2 (2.7.x) for your platform, then start and
    go through the installation procedure. Be careful to install with
    the following options enabled:
          -"Install pip" (this is the default)
	  -"Add Python to path"

Step 3: Install Dependencies

     The script depends on Python-mysql.
     
     It is available to download for your architecture at
     http://dev.mysql.com/downloads/connector/python (choose the
     version for python 2.7) On Linux systems it is usually available
     in OS packages, e.g. "python-mysqldb" and
     "python-mysql.connector" on Ubuntu (apt-get install)

     Additional required python packages are

     argparse
     easygui

     On both Windows and Linux you can install them by the
     (root/administrator) command-line:

     pip install <dependency>

     where <dependency> is one of the above three
     packages. Alternatively, you may find these as software packages
     for your system (aka "apt-get install python-easygui")

If these  steps were made,  the script's  dependencies are met,  it is
ready for use.

2. Obtaining data to be loaded
------------------------------

This script is designed for  the data obtainable from subscriptions of
quarterly  feeds. Please  note that  you  will need  the username  and
password for your WhoisXML API data feed subscription to access data.

The MySQL dumps are in the subdirectories of the directory "mysqldump"
of the database, e.g.

http://domainwhoisdatabase.com/whois_database/v20/database_dump/mysqldump.

We recommend to replicate this directory structure in your computer in
some folder. For you can do  it with our downloader scripts, with your
browser or your favorite recursive download utility.
(To  remain with  the pythonic  approach we  recommend to  use the  our
downloader script  "get_whois_info", available  for you also,  see the
reference manual. We have downloaded the  data (for the tlds "aaa" and
"aarp") used in the preparation of this manual with the command-line:

./get_whois_info.py -c whois_database -l YOUR_SUBSCRIPTION_USERNAME -p YOUR_SUBSCRIPTION_PASSWORD -f mysqldump --version v20 --tld aaa aarp

see the documentation of get_whois_info for more details.)

Important note: for large domains such  as .com, the data files can be
huge: up to terabytes size. Please take this into account when working
with such  domains. In  such cases  the loading  process is  also very
slow, it can take weeks. Hence, when working with really huge domains,
you  should consider  using  the  bash scripts  we  provide, they  are
slightly more efficient than the  more comfortable and portable Python
version.  Alternatively, the  use  of  binary dumps  may  be a  better
choice.

In our examples we shall load data of the tlds "aaa" and "aarp", so we
shall have our data downloaded in the following structure.

└── mysqldump
    ├── aaa
    │   ├── tables
    │   │   ├── whoiscrawler_v20_aaa_contact_mysql.sql.gz
    │   │   ├── whoiscrawler_v20_aaa_domain_names_whoisdatacollector_mysql.sql.gz
    │   │   ├── whoiscrawler_v20_aaa_registry_data_mysql.sql.gz
    │   │   └── whoiscrawler_v20_aaa_whois_record_mysql.sql.gz
    │   ├── whoiscrawler_v20_aaa_contact_mysql.sql.gz.md5
    │   ├── whoiscrawler_v20_aaa_contact_mysql.sql.gz.sha256
    │   ├── whoiscrawler_v20_aaa_domain_names_whoisdatacollector_mysql.sql.gz.md5
    │   ├── whoiscrawler_v20_aaa_domain_names_whoisdatacollector_mysql.sql.gz.sha256
    │   ├── whoiscrawler_v20_aaa_mysql_schema.sql.gz
    │   ├── whoiscrawler_v20_aaa_mysql_schema.sql.gz.md5
    │   ├── whoiscrawler_v20_aaa_mysql_schema.sql.gz.sha256
    │   ├── whoiscrawler_v20_aaa_mysql.sql.gz
    │   ├── whoiscrawler_v20_aaa_mysql.sql.gz.md5
    │   ├── whoiscrawler_v20_aaa_mysql.sql.gz.sha256
    │   ├── whoiscrawler_v20_aaa_registry_data_mysql.sql.gz.md5
    │   ├── whoiscrawler_v20_aaa_registry_data_mysql.sql.gz.sha256
    │   ├── whoiscrawler_v20_aaa_whois_record_mysql.sql.gz.md5
    │   └── whoiscrawler_v20_aaa_whois_record_mysql.sql.gz.sha256
    └── aarp
        ├── tables
        │   ├── whoiscrawler_v20_aarp_contact_mysql.sql.gz
        │   ├── whoiscrawler_v20_aarp_domain_names_whoisdatacollector_mysql.sql.gz
        │   ├── whoiscrawler_v20_aarp_registry_data_mysql.sql.gz
        │   └── whoiscrawler_v20_aarp_whois_record_mysql.sql.gz
        ├── whoiscrawler_v20_aarp_contact_mysql.sql.gz.md5
        ├── whoiscrawler_v20_aarp_contact_mysql.sql.gz.sha256
        ├── whoiscrawler_v20_aarp_domain_names_whoisdatacollector_mysql.sql.gz.md5
        ├── whoiscrawler_v20_aarp_domain_names_whoisdatacollector_mysql.sql.gz.sha256
        ├── whoiscrawler_v20_aarp_mysql_schema.sql.gz
        ├── whoiscrawler_v20_aarp_mysql_schema.sql.gz.md5
        ├── whoiscrawler_v20_aarp_mysql_schema.sql.gz.sha256
        ├── whoiscrawler_v20_aarp_mysql.sql.gz
        ├── whoiscrawler_v20_aarp_mysql.sql.gz.md5
        ├── whoiscrawler_v20_aarp_mysql.sql.gz.sha256
        ├── whoiscrawler_v20_aarp_registry_data_mysql.sql.gz.md5
        ├── whoiscrawler_v20_aarp_registry_data_mysql.sql.gz.sha256
        ├── whoiscrawler_v20_aarp_whois_record_mysql.sql.gz.md5
        └── whoiscrawler_v20_aarp_whois_record_mysql.sql.gz.sha256


3. Basic use
------------

(Note: in  Linux/UNIX style we  separate directories with "/"  and put
"./" before the  scripts throughout this manual.  On  Windows you need
"\" instead of "/" and you don't need the "./" before the command-line
scripts.)

The  easiest way  to run  the  script is  just double  clicking it  in
Windows or run it  with the --interactive option (./load_mysql_data.py
--interactive).   This will  start a  command-line window  to see  the
progress  on Windows,  but  you  will be  guided  through the  process
through a sequence of dialog  windows. Whenever you press the "Cancel"
button, the script exits without modifying anything.

Even  though the  process  is self-explanatory,  we  outline it  here,
especially since  this also  explains the  concepts necessary  for the
advanced use of the script.

First  you are  asked  for the  mysql credentials  and  they will  get
verified so that you don't work in vain in what follows.

The first choice to made is to decide the load mode:

-all: Import sql dump file(s) per  tld containing schema + data in one
-file.  per_table: Import  schema + tables for each  tld from separate
-files.

The latter is recommended for large domains.

The next choice to be made is  how you would like to specify data. You
may either

-Specify a  file (e.g. mysqldump/aaa/whoiscrawler_v20_aaa_mysql.sql.gz
 for  the  mode  "all")  or  a  schema  file  and  a  table  directory
 (e.g.   "mysqldump/aaa/whoiscrawler_v20_aaa_mysql_schema.sql.gz"  and
 "mysqldump/aaa/tables" for  the mode "per_tables"). This  will load a
 single tld coming from the specified file or files.

or

-Specify  the  directory  where  you have  all  your  downloaded  data
 (mysqldump/)  and  choose from  the  tlds  which  have data  in  your
 directory interactively. This lets you to load multiple tlds.

The second approach is probably simpler unless you have some special
purpose.

Then the script  will prompt for all the necessary  information and do
the job. For each tld, a MySQL  database will be created with the name
"whoiscrawler_$dbver_$tld",  e.g.   "whoiscrawler_v20_aaa".   You  can
follow the  details of  the process in  your terminal  or command-line
window.   (On  Windows you  can  disable  the command-line  window  by
changing the extension  of the script from .py to  .pyw. In that case,
however, you will see only the  dialog windows, e.g.  there will be no
sign of the script's activity when it is doing the main job.)

Please ensure  that the databases  to be created  do not yet  exist on
your  server.  Otherwise  the  script  will stop  with  an  error.  If
something goes wrong when running  the script, please drop the wrongly
or incompletely created databases manually.

As a general  principle, the script first verifies  the consistency of
the provided parameters  and the existence of the  required files (not
their contents,  however) in a first  phase, and does the  real job of
creating and populating databases in a second phase afterwards.

As creating  a database is a  significant step in the  process and the
inappropriate   name  of   the   database  may   reveal  invalid   file
specifications, you are prompted before  the creation of each database
in interactive mode.

Also note that the script may have  a large runtime for huge tlds. For
"com", for  instance, the  size of  the gzipped dump  is order  of 100
gigabytes,  whose  loading  can  take days  and  requires  significant
hardware resources.

4. Advanced use
---------------

The  script   can  be   run  with   command-line  parameters.   It  is
self-documenting:

./load_mysql_data.py --help

gives a full list of options.

As compared to the interactive use, the additional functionalities are

-The way how  you want to specify files and/or  tlds are automatically
 deduced from  the command-line arguments.  You get an  explanation if
 you  use  conflicting  arguments  (e.g. using  --tlds  together  with
 --dump-file is impossible).

-When loading  data for a single  tld, you may specify  a custom MySQL
 database name.

-It has a --debug option for extensive debug messages.

-It has  a --dry-run  option which disables  the interaction  with the
 database. It is good for testing whether the required files exist.

-You  can (and  sometimes  have to,  see the  next  item) disable  the
 creation of the given MySQL database by the --no-create-db option.

-It has  a --schema-only option  to load  a schema file  without table
 data and a --data-only option to  load data from separate table files
 assuming that  the schema is already  loaded. In this way  you can do
 loading of schema and data literally in two steps.

-You may  specify different directory  for the schema files  and table
 files. (Note: in  case of loading a single  domain specified directly
 with files, the --table-files-directory is e.g. mysqldump/aaa/tables,
 while if you specify with --tlds,  it is just mysqldump/, usually the
 same as --schema-files-directory.

Some examples:

1. Load domains aaa, aarp, schema and separate table files

	./load_mysql_data.py --mysql-user root --mysql-password MYSQLROOTPASSWORD --table-files-directory=./mysqldump --schema-files-directory ./mysqldump --db-version v20 --tlds aaa,aarp --mode per_table --verbose

2. Load  domains aaa, aarp, each  from a single sql  file, quietly (no
communication to STDERR or STDOUT)

	./load_mysql_data.py --mysql-user root --mysql-password MYSQLROOTPASSWORD --dump-files-dir ./mysqldump --db-version v20 --tlds aaa,aarp --mode full 

3.       Load       data        from       the       single       file
./mysqldump/aaa/whoiscrawler_v20_aaa_mysql.sql.gz  into  the  database
named "aaa_my_favourite_tld" (instead of "whoiscrawler_v20_aaa", which
would be used without the --mysql-database option):

      ./load_mysql_data.py  --mode full --dump-file ./mysqldump/aaa/whoiscrawler_v20_aaa_mysql.sql.gz --verbose --mysql-user root --mysql-password MYSQLROOTPASSWORD --mysql-database aaa_my_favourite_tld 

4.  "Simulate" the  loading  of  domains aaa,  aarp,  per tables,  not
touching the database

      ./load_mysql_data.py --mysql-user root --mysql-password MYSQLROOTPASSWORD --table-files-directory=./mysqldump --schema-files-directory ./mysqldump --db-version v20 --tlds aaa,aarp --mode per_table --verbose --debug --dry-run

