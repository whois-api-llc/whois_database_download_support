Documentation for the WhoisXML API

Whois data download utility

download_whois_data.py

Release version 0.0.8 dated 2018-02-23.

Copyright (c) 2010-2017 Whois API LLC,  http://www.whoisxmlapi.com
------------------------------------------------

The script is provided for our subscribers to download data from their
daily and quarterly data feed subscriptions.

The  aim of  the script  is  to support  web download  of WHOIS  data,
especially in order to set up a WHOIS database.

It is  a cross-platform solution for  end-users. It should be  used on
Windows  and Linux/Unix  type  systems and  does  not require  special
experience.

The user should be familiar, however, with the feeds and data formats,
which are described in the reference manuals of the respective feeds.

Script availability:
--------------------

The primary location of this script is the public GitHub repository

https://github.com/whois-api-llc/whois_database_download_support

The script is located in the subdirectory

whoisxmlapi_download_whois_data

In addition, WhoisXML API subscribers can access the scripts from the
following URLs:

Quarterly releases:

http://www.domainwhoisdatabase.com/whois_database/$releaseversion/docs/download_scripts

(replace $version by e.g. v20 or v21, available from v19 on)

Quarterly releases, CCTLDs:

http://domainwhoisdatabase.com/domain_list_quarterly/$releaseversion/docs/download_scripts

(replace $version by e.g. v6 or v7, available from v5 on)

Daily feeds:

http://bestwhois.org/domain_name_data/docs/scripts

(The script is the same for all the locations and can be used
for any of the subscriptions.)

Contents
--------
1. List of files
2. Installation
3. Basic use
4. Advanced use
5. Some remarks on the operation of the script

1. List of files
----------------

README.txt		: this file
README.SSL.txt		: documentation on how to set up ssl key-based authentication
download_whois_data.py  : the script to run
install_p12.py		: ssl key and cert installer script, see README.SSL.txt
feeds.ini		: the configuration file describing the feeds supported by the script.
			  Not intended to be edited by end-users.
whois_utils		: a directory with the modules used by the script.
			  It contains the following files:
			   __init__.py
			   WhoisDataFeed.py
			   whois_user_interaction.py
			   whois_web_download_utils.py

2. Installation
---------------

In  what follows  we describe  how to  make the  script working.   The
installation takes a few minutes only.

The  script  itself does  not  need  installation,  it runs  from  its
directory (where its dependencies reside, hence, it should be run from
there) if  its dependencies are  met. All  software needed to  run the
script is  free on  each platform.  So if you  are using  other Python
scripts of WhoisXML API, it is possible that you do not have to do any
installation, just start the scripts.  You may just try starting it by
double  clicking (Windows)  or running  it from  command-line (do  not
forget to ensure execution permissions, aka. download_whois_data.py.

Step 1: Install Python

The  script has  been developed  with Python  2.7.12 and  it has  been
tested with versions from 2.7.10 to  2.7.13. It should work with newer
versions  of series  2 Python.

If for some  reason you have an  earlier version of Python  2, such as
Python 2.6,  you shall  have compatibility issues.  (This is  the case
when you use the default Python  on certain releases of CentOS or RHEL
ver. 6.) It is always possible on those systems to set up Python 2.7.x
in parallel, consult the documentation of your system.

-On Linux systems, use your package manager, e.g. "apt-get install python".
-On Windows systems, download the installer from
    www.python.org, series 2 (2.7.x) for your platform, then start and
    go through the installation procedure. Be careful to install with
    the following options enabled:
          -"Install pip" (this is the default)
	  -"Add Python to path"

Step 2: Install Dependencies

     Additional required python packages are:

     argparse
     easygui
     requests

     On both Windows and Linux you can install them by the
     (root/administrator) command-line:

     pip install <dependency>

     where <dependency> is one of the above three
     packages. Alternatively, you may find these as software packages
     for your system (aka "apt-get install python-easygui")

If these  steps were made,  the script's  dependencies are met,  it is
ready for use.

The script  supports the  access of the  data via  ssl-encrypted pages
using ssl key-based authentication. Those clients who want to use this
possibility should read the file

README.SSL.txt

to do the necessary steps for configuring this kind of access.

3. Quick-start and basic use
----------------------------

The simplest way to use the script is to start it without any argument
or the  --interactive option. On  Windows systems,  it can be  done by
double  clicking. A  series  of  dialog windows  will  guide the  user
through the  download process and help  to choose what to  download. A
terminal  window will  show up  on Windows,  too, where  the user  can
follow the progress of the download process.

IMPORTANT:  the script  does not  check if  the combination  of dates,
database   versions,  etc.    you  specify   result  in   an  existing
dataset. E.g.   if you specify  future dates,  the script will  try to
download the given files and report that they do not exist. Similarly,
in  case of  quarterly feeds  if  you specify  a nonexistent  database
version the  script will  return an  authentication issue  because you
cannot have access to a yet  not existing directory. Hence, if you get
an error, check the parameters first.

Note:  if   you  download   data  for  quarterly   feeds,  a   set  of
subdirectories  will be  created  (if  they do  not  yet exist)  which
replicate the  directory structure of  the given quarterly  feed.  For
daily feeds  the files  will be downloaded  into a  subdirectory named
after the daily feed.

Setting up a password config file
---------------------------------

The user is prompted for login credentials by default (unless
ssl-based auth is set up).  It can be avoided by creating a file named
.whoisxmlapi_login.ini in your home directory. (On Windows systems,
the right file will be typically
"C:\Users\YourUsername\.whoisxmlapi_login.ini" .)

It is  recommended to set its  permissions so that the  only logged-in
user can read it. It should be a plain text file with contents similar
to the example below:

------------>cut here<----------------
[default]
login = DEFAULT_LOGIN_NAME
password = DEFAULT_PASSWORD

[whois_database]
login = FEED_SPECIFIC_LOGIN_NAME
password = FEED_SPECIFIC_PASSWORD
------------>cut here<----------------

The default section contains the username-password pair to used unless
you  use  a  feed  with  some  other  password.   Feed-specific  login
credentials  can be  specified under  sections named  after the  given
feed, as for  "whois_database" in the example.  (The "default" section
is mandatory, the others are optional.)

If  this file  is  set-up, you  will  not have  to  specify login  and
passwords in the dialogs or in the command-line.

Setting ssl authentication
--------------------------

To do this, read the file README.SSL.txt.  If once you have set up ssl
authentication, you can use  the --sslauth command-line option instead
of the username  and password arguments or  the password configuration
file. When running with  a GUI, if sslauth is set  up, the script will
ask in a  dialog window whether you  want to use this  or use password
auth, e.g. for feeds which you do not have ssl-based access.

4. Advanced use
---------------

The script can  be used with command-line parameters,  too. The option
--help provides a  detailed description of its  options. Some examples
are below.  Please note: the data  for dates in the given examples are
possibly already in archive feeds when you try them. If the respective
files are not found, change the dates to more recent ones.

Examples:

List the supported feeds and data formats:

./download_whois_data.py --list-feeds

List the data formats available for the feed "whois_database"

./download_whois_data.py --feed whois_database --list-dataformats

List tlds  supported by the  feed "domain_names_whois". The  result is
the set of all tlds supported on any of the days.

./download_whois_data.py --feed domain_names_whois --startdate 20170810 --enddate 20170812 --dataformats full_csv --list-supported-tlds

Download mysql  binary dumps (percona)  and simple csv files  for tlds
"aaa" and "abarth"  from the quarterly release v20  into the directory
"download_testdir" (should exist already):

./download_whois_data.py --verbose --feed whois_database --db-version v20 --dataformat percona,simple_csv --tlds aaa,abarth --output-dir download_testdir

Download simple csv files for all tlds from the quarterly release v20
into the directory /tmp (should exist already):

./download_whois_data.py --verbose --feed whois_database --db-version v20 --dataformat simple_csv --all-tlds --output-dir /tmp

Download full  csv files for  the tld aero from 20170810  to 20170812
into "download_testdir" 

./download_whois_data.py --feed domain_names_whois --startdate 20170810 --enddate 20170812 --dataformats full_csv --tlds aero --verbose --output-dir download_testdir

Download  full csv  data for  all tlds  for 2017-08-11  into "download
testdir" (note: the --tlds com is mandatory but it is ignored, you can
choose any other existing tld)

./download_whois_data.py --feed domain_names_whois --startdate 20170811 --dataformats full_csv_all_tlds --tlds com  --verbose --output-dir download_testdir

5. Some remarks on the operation of the script
----------------------------------------------

The script generates a list of files to be downloaded according to the
provided information.  It  does not check in  detail, however, whether
the  data  are fully  correct.  E.g.  if  you specify  a  non-existent
quarterly release, the files will not be found.

When actually downloading a file, the script will restart the download
upon timeout and  some other temporary issues. If the  file is already
there, it will not be downloaded again. Altogether it makes 5 attempts
to  download  each  file  (can   be  overridden  with  the  --maxtries
option). After 5 tries it will give  up. However, if the file does not
exist on the server, it gives up immediately.

For each file, and md5 checksum is also downloaded (except for certain
feeds which do not support md5  checksums. The download is repeated if
the  file does  not match  its downloaded  md5 sum.   This process  is
repeated 5  (or maxtries) times. For  instance, if there was  a broken
downloaded process, and some files  exist but they are broken, running
the script  again will notice this  upon the md5 check  and redownload
the file.   If there  is no  md5 checksum  for the  file, the  file is
downloaded but reported as unverified in the script output.

When  completed, the  script  will  report the  files  which were  not
available  for download.  Note that  this maybe  normal, e.g.  in some
feeds we have files only for changed domains, or a file may not yet be
available for downloading  again. We recommend to run  the script with
the same parameters  later in this case: the  already downloaded files
will not be downloaded again, but the script will make new attempts to
download the missing ones.

Note: some feeds support the download of data for all tlds in a single
file.    For    instance,    "domain_names_whois"   has    a    format
"regular_csv_all_tlds". In that case, somewhat illogically, the script
still asks to select a domain to download data for. Please specify one
of the  domains to proceed, though  script will ignore your  choice in
this case. This will be fixed in the future.
