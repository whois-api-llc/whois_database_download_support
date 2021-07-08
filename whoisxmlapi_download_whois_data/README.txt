Documentation for the WhoisXML API

Whois data download utility

download_whois_data.py

Release version 3.0.0 dated 2021-04-19.

Copyright (c) 2010-2021 Whois API, Inc.  http://www.whoisxmlapi.com
-------------------------------------------------------------------

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

Contents
--------
1. List of files
2. Installation
3. Access credentials
4. Basic use: GUI operation
5. Command-line operation, examples
6. Setting up stored authentication credentials
7. Remarks on the operation of the script

1. List of files
----------------

README.txt		: this file
README_python2.txt	: installation instructions for series 2 Python
README.SSL.txt		: documentation on how to set up ssl key-based authentication
SPECIFICATIONS.txt      : specifications of the scripts. For developers and advanced users.
FAQ.txt			: frequently asked questions
download_whois_data.py  : the script to run
install_p12.py		: ssl key and cert installer script, see README.SSL.txt
feeds.ini		: the configuration file describing the feeds supported by the script.
			  Not intended to be edited by end-users.
new_generation_plans.dat: description of the feeds available in new-generation subscription plans.
			  Not intended to be edited by end-users.
requirements.txt	: description of package requirements that can be used with pip3 in a
			  Python virtual environment (Linux, Mac OS X)
requirements_windows.txt: description of package requirements which can be used with pip on Windows
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

As  of version  1.*,  the script  can  be run  with  both Python3  and
Python2. It has  been tested with Python 3.6.9 and  2.7.15, and should
work with newer versions, too. The following description addresses the
installation  with  Python3, as  Python2  retires  on 2020.01.01.  If,
however, you want to use the program with Python2 for some reason, the
script supports this, please  read "README_python2.txt" instead of the
following installation steps, which apply for series 3 Python.

NOTE: To  maintain compatibility with  the previous versions,  it does
not specifically  require series 3  Python, it will start  the default
Python interpreter.  To make sure that  it runs with Python 3, replace
the first line of the file "download_whois_data.py", which reads

/usr/bin/env python

with

/usr/bin/env python3

using a programmer's text editor. 


Step 1: Install Python

Python is easy to install on most platforms:

- On Linux systems, use your package manager, e.g. "apt-get install
  python3".

-On Windows, download the installer  from www.python.org, the series 3
    for  your platform,  then start  and go  through the  installation
    procedure.  Be  careful  to  install  with  the  following  option
    enabled: -"Add Python to path"

- On  Mac  OS  X  you  also   need  to  download  the  installer  from
  www.python.org, and follow the instructions.  Or you may opt for the
  Homebrew approach, see e.g. https://docs.brew.sh/Homebrew-and-Python

Step 2: Install Dependencies

Additional required python packages are:

requests
easygui
argparse

On   both  Windows   and   Linux   you  can   install   them  by   the
(root/administrator) command-line:

     pip3 install <dependency>

where <dependency> is one of  the above three packages. Alternatively,
you may find these as software  packages for your system (e.g. "apt-get
install python3-easygui" on Debian-flavor systems).

For advanced Python users:

It is  of course a good  practice to use a  Python virtual environment
for installing the  required packages. If you familiar  with this, you
may use  the supplied  requirements.txt (or  requirments_windows.txt on
Windows)  for installing  the  required packages.  You  may use  these
latter  also without  a  virtual environment,  but it  is  not a  good
practice.

3. Access credentials
---------------------

There are two types of subscriptions:

- Legacy/quarterly access: these users have a separate username and
  password, or an ssl pack for key-based authentication. The data are
  typically downloaded from the domainwhoisdatabase.com or
  bestwhois.org in this case.
  
  The script can be used with the username/password pair or the ssl
  key an cert files.

- New-generation access: these users have the same username and
  password; this is a string also frequently used as an API key.

  An example of a new-generation URL reads

  https://newly-registered-domains.whoisxmlapi.com/datafeeds/Newly_Registered_Domains/custom2/domain_names_new

  where "custom2" is the subscription plan's name.

  The script can be used with this string and the name of the
  subscription plan.

4. Basic use: GUI operation
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

4. Command-line operation, examples
---------------------------------------

The script can  be used with command-line parameters,  too. The option
--help provides a  detailed description of its  options. Some examples
are below.  Please note: the data  for dates in the given examples are
possibly already in archive feeds when you try them. If the respective
files are not found, change the dates to more recent ones.

Examples:
---------

List the supported feeds and data formats:

./download_whois_data.py --list-feeds

List the feeds available in the subscription plan  "lite" with new-generation access:

./download_whois_data.py --plan lite --list-feeds

List the data formats available for the feed "whois_database":

./download_whois_data.py --feed whois_database --list-dataformats

Display the brief description and the list of the data formats
available for the feed "whois_database":

./download_whois_data.py --feed whois_database --describe-feed

List tlds  supported by the  feed "domain_names_whois". The  result is
the set of all tlds supported on any of the days:

./download_whois_data.py --feed domain_names_whois --startdate 20170810 --enddate 20170812 --dataformats full_csv --list-supported-tlds --username JohnDoe --password MyPassword42

In the previous example we have specified the username and password in
the command-line. In the following examples we assume that stored
credentials have been set up according to Section 6.

Download mysql  binary dumps (percona)  and simple csv files  for tlds
"aaa" and "abarth"  from the quarterly release v20  into the directory
"download_testdir" (should exist already):

./download_whois_data.py --verbose --feed whois_database --db-version v20 --dataformat percona,simple_csv --tlds aaa,abarth --output-dir download_testdir

Download simple csv files for all tlds from the quarterly release v20
into the directory /tmp (should exist already):

./download_whois_data.py --verbose --feed whois_database --db-version v20 --dataformat simple_csv --all-tlds --output-dir /tmp

Download full  csv files for  the tld aero from 20210310  to 20210312
into "download_testdir". Use ssl authentication:

./download_whois_data.py --feed domain_names_whois --startdate 20210310 --enddate 20210312 --dataformats full_csv --tlds aero --sslauth --verbose --output-dir download_testdir

Download full csv files for the tld aero from 20210301 to 20210305,
with a new-generation account having the "custom2" subscription plan:

./download_whois_data.py --feed domain_names_whois --startdate 20210301 --enddate 20210305 --dataformats full_csv --tlds aero --plan custom2 --password MY_API_KEY --verbose --output-dir download_testdir 

Download  full csv  data for  all tlds  for 2017-08-11  into "download_testdir":

./download_whois_data.py --feed domain_names_whois --startdate 20170811 --dataformats full_csv_all_tlds  --verbose --output-dir download_testdir

6. Setting up stored authentication credentials
-----------------------------------------------

Setting up a password config file
---------------------------------

The user is prompted for login credentials by default (unless
ssl-based auth is set up).


In the case of legacy/quarterly access,  it can be avoided by creating
a  file  named  .whoisxmlapi_login.ini  in your  home  directory.  (On
Windows    systems,    the    right    file    will    be    typically
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
you use a feed with some other password.  Feed-specific login
credentials can be specified under sections named after the given
feed, as for "whois_database" in the example.  (The "default" section
is mandatory, the others are optional.)  If this file is set-up, you
will not have to specify login and passwords in the dialogs or in the
command-line in the case of the legacy access.

Similarly, in the case of new-generation access, a file named
".whoisxmlapi_ng.ini" can be set up, with the following contents:

------------>cut here<----------------
[default]
plan = custom2
password = YOUR_API_KEY
------------>cut here<----------------

(Replace "custom2"  with your subscription plan,  and "YOUR_API_KEY".)
The file has  the same role as .whoisxmlapi_login.ini,  except that it
does not affect the interactive mode. In interactive mode this file is
ignored.)


Setting ssl authentication
--------------------------

To do this, read the file README.SSL.txt.  If once you have set up ssl
authentication, you can use  the --sslauth command-line option instead
of the username  and password arguments or  the password configuration
file. When running with  a GUI, if sslauth is set  up, the script will
ask in a  dialog window whether you  want to use this  or use password
auth, e.g. for feeds which you do not have ssl-based access.

7. Remarks on the operation of the script
-----------------------------------------

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

In daily data feeds (except for archive feeds) there is a mechanism to
indicate when  the data  of a given  feed in a  given data  format are
complete on the  server and ready for download. The  readiness of data
is indicated by a presence of a  specific file on the server; we refer
to the  data feeds' documentation  for details. The  downloader script
verifies the presence of these files.  By default it gives warnings if
the data  aren't complete yet for  the given day, which  may result in
missing files or downloading partial content. (The missing part of the
data can be downloaded by repeating the download process with the same
parameters.) If  the --no-premature  option is used,  no data  will be
downloaded from the given feed in  the given format for those days for
which the data are not yet complete.

For each file, and md5 checksum is also downloaded (except for certain
feeds which do not support md5  checksums. The download is repeated if
the  file does  not match  its downloaded  md5 sum.   This process  is
repeated 5  (or maxtries) times. For  instance, if there was  a broken
downloaded process, and some files  exist but they are broken, running
the script  again will notice this  upon the md5 check  and redownload
the  file. The  script resumes  the downloading  of a  broken file  by
default. So  if the file  changed on the  server for some  reason, the
broken  file will  be continued  anyway, but  it will  be redownloaded
because of  the md5 mismatch. If  the --no-resume option is  given, no
attempt  is made  to continue  a broken  download, the  files will  be
redownloaded from  scratch if necessary.  If there is no  md5 checksum
for the file, the file is downloaded but reported as unverified in the
script output.

In case of the new-generation access, continuation of downloading is
not yet supported, --no-resume is the default.

When  completed, the  script  will  report the  files  which were  not
available  for download.  Note that  this maybe  normal, e.g.  in some
feeds we have files only for changed domains, or a file may not yet be
available for downloading  again. We recommend to run  the script with
the same parameters  later in this case: the  already downloaded files
will not be downloaded again, but the script will make new attempts to
download the missing ones.

