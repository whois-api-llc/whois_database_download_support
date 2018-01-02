# class to represent data feeds, part of Whois API LLC end user scripts
#
# Copyright (c) 2010-2017 Whois API LLC,  http://www.whoisxmlapi.com
#

import sys
import os
import tempfile
import ConfigParser
import re

import datetime

import requests

import whois_utils.whois_web_download_utils as whois_web_download_utils

import whois_utils.whois_user_interaction as whois_utils_interaction
from whois_utils.whois_user_interaction import *

def set_interaction_verbosity(debug, verbose, dialog_communication):
    set_verbosity(debug, verbose, dialog_communication)
    
def feed_format_matrix(config_dir):
    """Utility function to list formats available for feeds"""
    feeds_config = ConfigParser.ConfigParser()
    feeds_config.read(os.path.abspath(os.path.join(config_dir, 'feeds.ini')))
    formatmatrix={}
    for data in feeds_config.sections():
        [feed, dataformat] = data.split("__")
        if feed in formatmatrix.keys():
            formatmatrix[feed].append(dataformat)
        else:
            formatmatrix[feed] = [dataformat]
    return(formatmatrix)

def feed_descriptions(config_dir):
    """Utility function to list formats available for feeds"""
    feeds_config = ConfigParser.ConfigParser()
    feeds_config.read(os.path.abspath(os.path.join(config_dir, 'feeds.ini')))
    description={}
    for data in feeds_config.sections():
        [feed, dataformat] = data.split("__")
        try:
            thisdescription = feeds_config.get(data, 'description')
        except:
            thisdescription = None
        if thisdescription != None:
            description[feed] = thisdescription
        if thisdescription == None and feed not in description.keys():
            description[feed] = feed
    return(description)

class WhoisDataFeed:
    """This is a class to represent a data feed for downloading. 
    Possible feeds are defined in feeds.ini"""
    def __init__(self):
        #other stuff not set by default
        self.dbversion = None
        self.login = None
        self.password = None
        self.loginOK = False
        self.feed_name = None
        self.data_format = None
        self.maxtries = 5
    def set_maxtries(self, maxtries):
        """Set the maximum number of download attempts"""
        if maxtries != None:
            self.maxtries = maxtries
    def set_feed_type(self, config_dir, feed_name, data_format):
        """Basic config of this feed.
        Sets up its basic data from the file feeds.ini.
        Daily and quarterly feeds specifics are set by other methods"""
        self.feeds_config = ConfigParser.ConfigParser()
        self.feeds_config.read(os.path.abspath(os.path.join(config_dir, 'feeds.ini')))
        #Set everything to default
        self.dbversion = None
        self.startdate = None
        self.enddate = None
        self.login = None
        self.password = None
        self.loginOK = False
        try:
            self.feed_name = feed_name
            self.data_format = data_format
            self.main_url=self.feeds_config.get(feed_name + '__' + data_format, 'main_url')
            self.access_test_file=self.feeds_config.get(feed_name + '__' + data_format, 'access_test_file')
            self.download_masks=self.feeds_config.get(feed_name + '__' + data_format, 'download_masks').split(',')
            #Removing temporarily
            #self.sha256path=self.feeds_config.get(feed_name + '__' + data_format, 'sha256_path')
            self.supported_tlds_url=self.feeds_config.get(feed_name + '__' + data_format, 'supported_tlds_url')
        except:
            print_error_and_exit('data feed "%s" does not exist or it does not support the format "%s"\n'
                % (feed_name, data_format))
        #optional arguments
        try:
            self.md5path=self.feeds_config.get(feed_name + '__' + data_format, 'md5_path')
        except:
            self.md5path=None
        try:
            self.md5mask=self.feeds_config.get(feed_name + '__' + data_format, 'md5_mask')
        except:
            self.md5mask='$filename.md5'
        try:
            self.description=self.feeds_config.get(feed_name + '__' + data_format, 'description')
        except:
            self.description='No description about this feed. Consult the documentation.'
        try:
            self.is_daily = self.feeds_config.getboolean(feed_name + '__' + data_format, 'daily_feed')
            if self.is_daily:
                """If daily feed, reset dbversion"""
                self.dbversion = None
            self.is_quarterly = self.feeds_config.getboolean(feed_name + '__' + data_format, 'quarterly_feed')
        except:    
            sys.stderr.write('Config error: feed type ill-defined for feed "%s" , format "%s"\n'
                             % (feed_name, data_format))
            exit(1)
        if self.is_daily + self.is_quarterly != 1:
            sys.stderr.write('Config error: a feed should be either daily or quarterly, problem with feed "%s" , format "%s"\n'
                             % (feed_name, data_format))
            exit(1)
        
    def set_login_credentials(self, login, password):
        """setup login credentials"""
        if login.strip() != '':
            #if the login name is provided, set up explicitly
            self.login = login
            self.password = password
            self.loginOK = False
        else:
            #Just whitespaces were provided: we try reading the default config ~/.whoisxmlapi_login.ini
            try:
                password_config=ConfigParser.ConfigParser()
                password_config.read(os.path.abspath(os.path.join(os.path.expanduser('~/'), '.whoisxmlapi_login.ini')))            
                if self.feed_name != None and self.feed_name in set(set(password_config.sections())):
                    self.login = password_config.get(self.feed_name,'login')
                    self.password = password_config.get(self.feed_name,'password')
                    self.loginOK = False
                else:
                    self.login = password_config.get('default','login')
                    self.password = password_config.get('default','password')
                    self.loginOK = False
            except:
                print_error_and_exit('Supposed to read password config ~/.whoisxmlapi_login.ini, but it was not found')

    def test_http_access(self):
        """This tests if the object can access the root directory using the provided http credentials"""
        test_session = requests.Session()
        test_session.auth = (self.login, self.password)
        accesstest = self.main_url + '/' + self.access_test_file
        if self.is_quarterly:
            if self.dbversion == None:
                raise ValueError("Quarterly feed accessed without setting dbversion.")
            accesstest=accesstest.replace('$dbversion', self.dbversion)
        elif self.is_daily:
            if self.startdate == None:
                raise ValueError("Quarterly feed accessed without setting date interval")
            accesstest=accesstest.replace('$date', self.startdate.strftime('%Y_%m_%d'))
        print_debug("Trying to access %s" % (accesstest))
        probe = test_session.get(accesstest)
        if probe.status_code == 200:
            self.loginOK = True
            print_verbose('Verifying login: http access OK.')
        else: 
            self.loginOK = False
            print_verbose('Verifying login: http access FAILED.')
        test_session.close()

    def open_http_session(self):
        """This opens a http session for downloading"""
        self.session = requests.Session()
        self.session.auth = (self.login, self.password)
        self.sessionopen = True

    def get_url_contents(self, url):
        """Safely get the contents of an URL. Return an empty string if any error occurs."""
        if not self.sessionopen:
            print_error_and_exit("Trying to download without opening session")            
        response = self.session.get(url)
        print_debug('loading %s returned code %s' % (url, response.status_code))
        if response.status_code != 200:
            return('')
        else:
            return(response.text)

    def set_quarterly_dbversion(self, dbversion):
        """This sets up the db version to be downloaded and filters the tlds"""
        if self.is_quarterly:
            if re.match(r'^v[0-9]+$', dbversion) == None:
                print_error_and_exit("Invalid database version specification. Should be vNN, e.g. v6 or v20")
            else:
                self.dbversion = dbversion
        else:
            print_error_and_exit("You cannot specify database version for a daily feed")

    def set_daily_feed_interval(self, startdate, enddate):
        """This sets up the date interval of a daily feed"""
        if self.is_daily:
            if (not isinstance(startdate, datetime.date)) or (not isinstance(enddate, datetime.date) and enddate != None):
                print_error_and_exit("Invalid start date and end date specification")
            else:
                if enddate != None and enddate < startdate:
                    print_error_and_exit("Ending date is greater than starting date")
                else:
                    self.startdate = startdate
                    if enddate == None:
                        self.enddate = startdate
                    else:
                        self.enddate = enddate
        else:
            print_error_and_exit("You cannot specify date information for a quarterly feed")

    def update_supported_tlds(self):
        """Update the supported tlds list for the feed"""
        if self.is_quarterly:
            """quarterly feeds: a single list"""
            url = self.supported_tlds_url.replace('$dbversion', self.dbversion)
            tlds = self.get_url_contents(url).strip().split(',')
            self.supported_tlds = [tld.strip() for tld in tlds]
        elif self.is_daily:
            """daily feeds: listing available for dates"""
            ndays = (self.enddate - self.startdate).days + 1
            self.supported_tlds = []
            for day in range(ndays):
                datestr = (self.startdate + datetime.timedelta(days=day)).strftime('_%Y_%m_%d')
                print_verbose('Getting list of supported tlds on day %d (%s) of %d days.' %(day+1, datestr, ndays))
                url = self.supported_tlds_url.replace('$_date', datestr)
                print_debug("TLD url: %s" % url)
                supptlds_forday = self.get_url_contents(url).strip().split(',')
                print_debug("Downloaded info: %s" % str(supptlds_forday))
                if supptlds_forday == ['']:
                    print_verbose('No specific list of tlds for day %d (%s) of %d days.' %(day+1, datestr, ndays))
                else:
                    self.supported_tlds += supptlds_forday 
            #If there is no supported_tlds for any day, we get the default one without any date
            if self.supported_tlds == None or self.supported_tlds == []:
                print_verbose('No specific list of tlds found for the dates. Downloading generic list.')
                url = self.supported_tlds_url.replace('$_date', '')
                self.supported_tlds = self.get_url_contents(url).strip().split(',')
                self.supported_tlds = list(set(self.supported_tlds))
                try:
                    self.supported_tlds.remove('')
                except:
                    pass
            if self.supported_tlds == None or self.supported_tlds == []:
                print_error_and_exit('Error updating supported tlds.')
            self.supported_tlds = sorted(list(set(self.supported_tlds)))
        else:
            """other feed types: not yet supported"""
            pass

    def set_supported_tlds(self, feed):
        """sets the list of tlds of the feed to that of another feed
        if the feed name is the same, only the data format differs"""
        if self.feed_name == feed.feed_name:
            self.supported_tlds = feed.supported_tlds
        
    def actual_url(self, url, dbversion, tld, date):
        """Utility to substitute particular data into a download URL"""
        tldunderscore = tld.replace('.', '_')
        if self.dbversion != None:
            return(url.replace('$dbversion', dbversion).replace('$tldunderscore', tldunderscore).replace('$tld', tld).replace('$_date', date.strftime('_%Y_%m_%d')).replace('$date', date.strftime('%Y_%m_%d')).replace('$minusdate', date.strftime('%Y-%m-%d')))
        else:
            return(url.replace('$tldunderscore', tldunderscore).replace('$tld', tld).replace('$_date', date.strftime('_%Y_%m_%d')).replace('$date', date.strftime('%Y_%m_%d')).replace('$minusdate', date.strftime('%Y-%m-%d')))

    def substitute_mask(self, mask, dbversion, tld, date, filename):
        """Utility to substitute particular data into a string 'mask'. Intended for md5 and sha masks originally"""
        tldunderscore = tld.replace('.', '_')
        if self.dbversion != None:
            return(mask.replace('$dbversion', dbversion).replace('$tldunderscore', tldunderscore).replace('$tld', tld).replace('$_date', date.strftime('_%Y_%m_%d')).replace('$date', date.strftime('%Y_%m_%d')).replace('$minusdate', date.strftime('%Y-%m-%d')).replace('$filename', filename))
        else:
            return(mask.replace('$tldunderscore', tldunderscore).replace('$tld', tld).replace('$_date', date.strftime('_%Y_%m_%d')).replace('$date', date.strftime('%Y_%m_%d')).replace('$minusdate', date.strftime('%Y-%m-%d')).replace('$filename', filename))


    def download_feed_into_directory(self, tlds, targetdir):
        """This will download the data of the feed into the given directory"""
        self.downloaded = []
        self.failed = []
        if self.is_quarterly:
            """quarterly feeds: single date"""
            self.update_supported_tlds()
        for tld in tlds:
            mainurl = self.actual_url(self.main_url, self.dbversion, tld, datetime.datetime.now())
            if self.startdate != None:
                startdate = self.startdate
            else:
                startdate = datetime.datetime.now()
            if self.enddate != None:
                ndays = (self.enddate - self.startdate).days + 1
            else:
                ndays = 1
            for mask in self.download_masks:
                for day in range(ndays):
                    thismask = self.actual_url(mask, self.dbversion, tld, (startdate + datetime.timedelta(days=day)))
                    downloadurl = mainurl + '/' + thismask
                    if self.is_daily:
                        thistargetdir=os.path.dirname(os.path.abspath(os.path.join(targetdir, self.feed_name, thismask)))
                    else:
                        thistargetdir=os.path.dirname(os.path.abspath(os.path.join(targetdir, thismask)))
                    print_verbose("downloading %s into %s" % (downloadurl, unicode(thistargetdir)))
                    #Put together md5 name
                    if self.md5path == 'NEXT_TO_FILE':
                        md5url = downloadurl + '.md5'
                    elif self.md5path != None:
                        thefilename = thismask.split('/')[-1]
                        thismd5file = self.substitute_mask(self.md5mask, self.dbversion, tld, (startdate + datetime.timedelta(days=day)), thefilename)
                        md5url = mainurl + '/' + self.md5path + '/' + thismd5file
                    else:
                        #md5 unsupported
                        md5url = None

                    download_urls=[]
                    if not re.search(r'\$ALLFILES', downloadurl):
                        download_urls.append(downloadurl)
                    else:
                        print_verbose("Directory contents detected. Expanding urls")
                        print_verbose("Checksums not supported in this case.")
                        md5url = None
                        downloadurl_base = downloadurl.replace('$ALLFILES','')
                        downloadfiles = whois_web_download_utils.webdir_ls(downloadurl_base, self.session)
                        if downloadfiles != []:
                            for downloadfile in downloadfiles:
                                download_urls.append(downloadurl_base + downloadfile)
                    #We do the main job here: downloading
                    for downloadurl in download_urls:
                        success = whois_web_download_utils.web_download_and_check_file(downloadurl, md5url, self.session, thistargetdir, self.maxtries)
                        if success:
                            print_verbose('SUCCESS: downloaded %s.' % (downloadurl))
                            self.downloaded.append(downloadurl)
                        else:
                            print_verbose('Download of %s FAILED. It may not exist, or please try again.' % (downloadurl))
                            self.failed.append(downloadurl)

        
