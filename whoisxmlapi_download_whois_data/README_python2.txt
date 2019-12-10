Supplement for the documentation of the WhoisXML API

Whois data download utility

download_whois_data.py

Release version 1.0.0 dated 2019-12-10.

Copyright (c) 2010-2017 Whois API, Inc. http://www.whoisxmlapi.com
-------------------------------------------------------------------

The present file supplements README.txt's as a replacement for steps 1
and 2 in  Section 2, Installation, intended for legacy  Python 2 users
as opposed to the Python 3-based description of the main README. It is
recommended to switch to  Python 3 as the support of  Python 2 ends on
2020-01-01.

Step 1: Install Python

The script has been tested with Python 2.7.15. If for some reason you
have an earlier main version of Python 2, such as Python 2.6, you
shall have compatibility issues.  (This is the case when you use the
default Python on certain releases of CentOS or RHEL ver. 6.) It is
always possible on those systems to set up Python 2.7.x in parallel,
consult the documentation of your system.

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

where <dependency> is one of the above three packages. Alternatively,
you may find these as software packages for your system (aka "apt-get
install python-easygui")

If these  steps were made,  the script's  dependencies are met,  it is
ready for use.

The script  supports the  access of the  data via  ssl-encrypted pages
using ssl key-based authentication. Those clients who want to use this
possibility should read the file

README.SSL.txt

to do the necessary steps for configuring this kind of access.
