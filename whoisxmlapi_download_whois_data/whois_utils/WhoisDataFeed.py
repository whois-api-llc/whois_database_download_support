# class to represent data feeds, part of Whois API LLC end user scripts
#
# Copyright (c) 2010-2021 Whois API LLC,  https://www.whoisxmlapi.com
#

import sys
import os
import tempfile
import re

try:
    import ConfigParser
except ModuleNotFoundError:
    import configparser as ConfigParser

import datetime

import requests

from requests.packages.urllib3.exceptions import SubjectAltNameWarning
requests.packages.urllib3.disable_warnings(SubjectAltNameWarning)

import whois_utils.whois_web_download_utils as whois_web_download_utils

import whois_utils.whois_user_interaction as whois_user_interaction
from whois_utils.whois_user_interaction import *

#Python3 compatibility hack
try:
    unicode('')
except NameError:
    unicode = str

def set_verbosity(debug, verbose, dialog_communication):
    whois_user_interaction.DIALOG_COMMUNICATION = dialog_communication
    whois_user_interaction.VERBOSE = verbose
    whois_user_interaction.DEBUG = debug

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
        self.maxtries = 1
        self.no_resume = False
        self.authtype = 'password'
        self.download_premature = True
        
    def set_maxtries(self, maxtries):
        """Set the maximum number of download attempts"""
        if maxtries != None:
            self.maxtries = maxtries
    def set_no_resume(self, no_resume):
        """Set no_resume mode to the given value"""
        self.no_resume = no_resume

    def set_download_premature(self, download_premature):
        """Force downloading premature files"""
        self.download_premature = download_premature
        
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
            self.access_test_file=self.feeds_config.get(feed_name + '__' + data_format, 'access_test_file')
            self.download_masks=self.feeds_config.get(feed_name + '__' + data_format, 'download_masks').split(',')
            #Removing temporarily
            #self.sha256path=self.feeds_config.get(feed_name + '__' + data_format, 'sha256_path')
        except:
            print_error_and_exit('data feed "%s" does not exist or it does not support the format "%s"\n'
                % (feed_name, data_format))
        #URL: oldschool or NAF
        try:
            self.main_url = self.feeds_config.get(feed_name + '__' + data_format, 'main_url')
        except:
            self.main_url = None
        try:
            self.naf_url = self.feeds_config.get(feed_name + '__' + data_format, 'naf_url')
        except:
            self.naf_url = None
            
        if self.main_url is None and self.naf_url is None:
            print_error_and_exit('data feed "%s" with "%s" does not have a valid URL\n'
                % (feed_name, data_format))
        #optional arguments
        try:
            self.md5path = self.feeds_config.get(feed_name + '__' + data_format, 'md5_path')
        except:
            self.md5path = None
        try:
            self.md5mask = self.feeds_config.get(feed_name + '__' + data_format, 'md5_mask')
        except:
            self.md5mask='$filename.md5'
        try:
            self.statuspath = self.feeds_config.get(feed_name + '__' + data_format, 'status_path')
        except:
            self.statuspath = None
        try:
            self.download_ready_file = self.feeds_config.get(feed_name + '__' + data_format, 'download_ready_file')
        except:
            self.download_ready_file = None
        try:
            self.description = self.feeds_config.get(feed_name + '__' + data_format, 'description')
        except:
            self.description = 'No description about this feed. Consult the documentation.'
        #tld-independent feeds do not need any tld specificaiton
        try:
            self.tldindependent = self.feeds_config.get(feed_name + '__' + data_format, 'tldindependent')
        except:
            self.tldindependent = False
        #Type of the feed, daily/quarterly
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
        if self.tldindependent:
            self.supported_tlds_url = None
        else:
        #How to determine supported tlds
            #For NAF subscriptions we just try getting the NAF-based url:
            try:
                self.naf_supported_tlds_url = self.feeds_config.get(feed_name + '__' + data_format, 'naf_supported_tlds_url')
            except:
                self.naf_supported_tlds_url = None
            #The legacy URL has to be there
            try:
                #by default we assume that there is an url for supported tlds
                self.supported_tlds_url = self.feeds_config.get(feed_name + '__' + data_format, 'supported_tlds_url')
            except:
                #If the url was not specified, supported tlds should be listed in the config
                self.supported_tlds_url = None
                try:
                    tlds = self.feeds_config.get(feed_name + '__' + data_format, 'supported_tlds_list')
                    self.supported_tlds = [tld.strip() for tld in tlds.split(' ')]
                except:
                    print_error_and_exit('Config error: cannot determine supported TLDS url config in feed "%s" , format "%s"\n'
                    % (feed_name, data_format))
                    exit(1)        
            #Determining supported tlds for those archive feeds which have year-named subdirectories
            try:
                #by default we assume that there is an url for archive supported tlds
                self.supported_tlds_url_archive = self.feeds_config.get(feed_name + '__' + data_format, 'supported_tlds_url_archive')
            except:
                #If the url for archive supported is not provided, we assume that it is not relevant
                self.supported_tlds_url_archive = None
            try:
                #by default we assume that there is an url for archive supported tlds
                self.naf_supported_tlds_url_archive = self.feeds_config.get(feed_name + '__' + data_format, 'naf_supported_tlds_url_archive')
            except:
                #If the url for archive supported is not provided, we assume that it is not relevant
                self.naf_supported_tlds_url_archive = None
        #download_masks_archive: archive feed specific, it is for support of old_data subdirs
        try:
            self.download_masks_archive = self.feeds_config.get(feed_name + '__' + data_format, 'download_masks_archive').split(',')
        except:
            self.download_masks_archive = None
                
        #in any case we fix urls
        self.fix_base_url()

        

    def fix_base_url(self):
        """Sets the base url based on the auth type. 
        Can be invoked arbitrary times.
        TODO: ssl basenames are hard-wired here"""
        if self.authtype == 'password':
            self.main_url=self.main_url.replace('https://direct.bestwhois.org','https://bestwhois.org')
            self.main_url=self.main_url.replace('https://direct.domainwhoisdatabase.com','https://www.domainwhoisdatabase.com')
            try:
                self.supported_tlds_url=self.supported_tlds_url.replace('https://direct.bestwhois.org','https://bestwhois.org')
                self.supported_tlds_url=self.supported_tlds_url.replace('https://direct.domainwhoisdatabase.com','https://www.domainwhoisdatabase.com')
            except:
                #explicit list is given, supported tlds url is none
                pass
            #archive supported tlds url if relevant
            try:
                self.supported_tlds_url_archive=self.supported_tlds_url_archive.replace('https://direct.bestwhois.org','https://bestwhois.org')
                self.supported_tlds_url_archive=self.supported_tlds_url_archive.replace('https://direct.domainwhoisdatabase.com','https://www.domainwhoisdatabase.com')
            except:
                #has no supported tlds url archive
                pass
        elif self.authtype == 'ssl':
            self.main_url=self.main_url.replace('https://bestwhois.org','https://direct.bestwhois.org')
            self.main_url=self.main_url.replace('https://www.domainwhoisdatabase.com', 'https://direct.domainwhoisdatabase.com')
            try:
                self.supported_tlds_url=self.supported_tlds_url.replace('https://bestwhois.org','https://direct.bestwhois.org')
                self.supported_tlds_url=self.supported_tlds_url.replace('https://www.domainwhoisdatabase.com', 'https://direct.domainwhoisdatabase.com')
            except:
                #explicit list is given, supported tlds url is none
                pass
            try:
                self.supported_tlds_url_archive=self.supported_tlds_url_archive.replace('https://bestwhois.org','https://direct.bestwhois.org')
                self.supported_tlds_url_archive=self.supported_tlds_url_archive.replace('https://www.domainwhoisdatabase.com', 'https://direct.domainwhoisdatabase.com')
            except:
                #explicit list is given, supported tlds url is none
                pass
        elif self.authtype == 'NAF':
            if self.naf_subscription == '':
                raise ValueError('Subscription plan not specified')
            self.main_url = self.naf_url.replace('$plan', self.naf_subscription)
            if not self.tldindependent and self.supported_tlds_url is not None:
                    self.supported_tlds_url = self.naf_supported_tlds_url.replace('$plan', self.naf_subscription)
            #archive supported tlds url if relevant
            try:
                self.supported_tlds_url_archive=self.naf_supported_tlds_url_archive.replace('$plan', self.naf_subscription)
                self.supported_tlds_url_archive=self.naf_supported_tlds_url_archive.replace('$plan', self.naf_subscription)
            except:
                #has no supported tlds url archive
                pass
        else:
            raise ValueError('Invalid auth type: %s' % authtype)

        
    def set_login_credentials(self, authtype, login='', password='', naf_subscription = '', cacertfile = 'whoisxmlapi.ca', keyfile = 'client.key', crtfile = 'client.crt'):
        """setup login credentials"""
        if authtype == 'password':
            self.authtype = 'password'
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
        elif authtype == 'ssl':
            #SSL authentication
            self.authtype = 'ssl'
            self.cacertfile = cacertfile
            self.keyfile = keyfile
            self.crtfile = crtfile
            self.loginOK = False
        elif authtype == 'NAF':
            self.authtype = 'NAF'
            self.naf_subscription = naf_subscription
            if self.naf_subscription == '':
                raise ValueError("Subscription type has to be provided for NAF authentication")
            if password.strip() != '':
                self.password = password
            else:
                print_debug("Reading config for new-generation auth")
                try:
                    password_config=ConfigParser.ConfigParser()
                    password_config.read(os.path.abspath(os.path.join(os.path.expanduser('~/'), '.whoisxmlapi_ng.ini')))            
                    if self.feed_name != None and self.feed_name in set(set(password_config.sections())):
                        self.password = password_config.get(self.feed_name, 'password')
                        self.loginOK = False
                    else:
                        self.password = password_config.get('default', 'password')
                    self.loginOK = False
                except:
                    print_error_and_exit('Supposed to read password config ~/.whoisxmlapi_ng.ini, but it was not found')
            self.loginOK = False
        else:
            raise ValueError('Invalid auth type: %s' % authtype)
        self.fix_base_url()
        
    def test_http_access(self):
        """This tests if the object can access the root directory using the provided http credentials"""
        test_session = requests.Session()
        if self.authtype == "password":
            test_session.auth = (self.login, self.password)
        elif self.authtype == "ssl":
            test_session.verify= self.cacertfile
            test_session.cert = (self.crtfile, self.keyfile)
        elif self.authtype == 'NAF':
            test_session.auth = (self.password, self.password)
        else:
            raise ValueError("Auth method not specified in feed.")
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
        print_debug("Auth type: %s" % self.authtype)
        try:
            probe = test_session.get(accesstest)
        except requests.exceptions.SSLError:
            print_error_and_exit("Invalid SSL credentials specified.")            
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
        if self.authtype == 'password':
            self.session.auth = (self.login, self.password)
            self.sessionopen = True
        elif self.authtype == 'ssl':
            self.session.verify= self.cacertfile
            self.session.cert = (self.crtfile, self.keyfile)
            self.sessionopen = True
        elif self.authtype == 'NAF':
            self.session.auth = (self.password, self.password)
            self.sessionopen = True
        else:
            raise ValueError("Auth method not specified in feed.")
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
        elif self.is_daily and self.supported_tlds_url != None:
            """daily feeds: listing available for dates"""
            """except when we were given the tlds explicityl"""
            ndays = (self.enddate - self.startdate).days + 1
            self.supported_tlds = []
            for day in range(ndays):
                sptldsdate = self.startdate + datetime.timedelta(days=day)
                datestr = sptldsdate.strftime('_%Y_%m_%d')
                print_verbose('Getting list of supported tlds on day %d (%s) of %d days.' %(day+1, datestr, ndays))
                thisdaysyear = sptldsdate.year
                url = self.supported_tlds_url.replace('$_date', datestr).replace('$year',sptldsdate.strftime('%Y')).replace('$month',sptldsdate.strftime('%m'))
                if self.supported_tlds_url_archive != None and thisdaysyear != datetime.date.today().year:
                    url = self.supported_tlds_url_archive.replace('$_date', datestr).replace('$year',sptldsdate.strftime('%Y')).replace('$month',sptldsdate.strftime('%m'))
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
                url = self.supported_tlds_url.replace('$_date', '').replace('/$year','').replace('/$month','')
                self.supported_tlds = self.get_url_contents(url).strip().split(',')
                self.supported_tlds = list(set(self.supported_tlds))
            if self.supported_tlds == None or self.supported_tlds == []:
                print_error_and_exit('No tlds found.\n In case of some daily feeds it can be normal:\n it just means that there are no data available for the given day(s).')
            self.supported_tlds = sorted(list(set(self.supported_tlds)))
        else:
            """other feed types: not yet supported"""
            pass
        try:
            self.supported_tlds.remove('')
        except:
            pass


    def check_download_ready_on_day(self, the_date, targetdir):
        """Checks if the download_ready file is generated for the given daily feed on the given date"""
        if self.is_quarterly or self.download_ready_file is None:
            #This function works only for daily feeds
            print_verbose("Dowload ready check unsupported for feed: %s format: %s date: %s."%(
                self.feed_name,
                self.data_format,
                the_date.strftime("%Y-%m-%d")))
            return True
        mask = self.substitute_mask(self.download_ready_file,
                                    '', '',the_date, '')
        url = self.main_url + '/' + self.statuspath + '/' + mask
        dlready = whois_web_download_utils.web_download_file(url, self.session, targetdir, self.maxtries, True)
        return dlready

    def set_supported_tlds(self, feed):
        """sets the list of tlds of the feed to that of another feed
        if the feed name is the same, only the data format differs"""
        if self.feed_name == feed.feed_name:
            self.supported_tlds = feed.supported_tlds
        
    def actual_url(self, url, dbversion, tld, date):
        """Utility to substitute particular data into a download URL"""
        tldunderscore = tld.replace('.', '_')
        if self.dbversion != None:
            return(url.replace('$dbversion', dbversion).replace('$tldunderscore', tldunderscore).replace('$tld', tld).replace('$_date', date.strftime('_%Y_%m_%d')).replace('$date', date.strftime('%Y_%m_%d')).replace('$minusdate', date.strftime('%Y-%m-%d')).replace('$year', date.strftime('%Y')))
        else:
            return(url.replace('$tldunderscore', tldunderscore).replace('$tld', tld).replace('$_date', date.strftime('_%Y_%m_%d')).replace('$date', date.strftime('%Y_%m_%d')).replace('$minusdate', date.strftime('%Y-%m-%d')).replace('$month', date.strftime('%m')).replace('$year', date.strftime('%Y')))

    def substitute_mask(self, mask, dbversion, tld, date, filename):
        """Utility to substitute particular data into a string 'mask'. Intended for md5 and sha masks originally"""
        tldunderscore = tld.replace('.', '_')
        if self.dbversion != None:
            return(mask.replace('$dbversion', dbversion).replace('$tldunderscore', tldunderscore).replace('$tld', tld).replace('$_date', date.strftime('_%Y_%m_%d')).replace('$date', date.strftime('%Y_%m_%d')).replace('$minusdate', date.strftime('%Y-%m-%d')).replace('$month', date.strftime('%m')).replace('$filename', filename))
        else:
            return(mask.replace('$tldunderscore', tldunderscore).replace('$tld', tld).replace('$_date', date.strftime('_%Y_%m_%d')).replace('$date', date.strftime('%Y_%m_%d')).replace('$minusdate', date.strftime('%Y-%m-%d')).replace('$month', date.strftime('%m')).replace('$filename', filename))


    def download_feed_into_directory(self, tlds, targetdir):
        """This will download the data of the feed into the given directory"""
        self.downloaded = []
        self.failed = []
        self.premature = []
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
                    #First we check that it is not an earlier day from an archive feed
                    thisday = startdate + datetime.timedelta(days=day)
                    thisdaysyear = thisday.year
                    if self.download_masks_archive == None or (
                            self.download_masks != None and thisdaysyear == datetime.date.today().year):
                        thismask = self.actual_url(mask, self.dbversion, tld, thisday)
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
                            thismd5file = self.substitute_mask(self.md5mask, self.dbversion, tld, thisday, thefilename)
                            md5url = mainurl + '/' + self.md5path + '/' + thismd5file
                        else:
                            #md5 unsupported
                            md5url = None
                        #checking download ready
                        if self.is_daily:
                            dlready = self.check_download_ready_on_day(thisday,
                                                                       os.path.join(targetdir, self.feed_name, str(self.statuspath)))
                            if not dlready:
                                self.premature.append("%s %s %s"%(self.feed_name,
                                                                 self.data_format,
                                                                 thisday.strftime("%Y-%m-%d")))
                                if self.download_premature:
                                    print_verbose("Warning NOT READY in feed: %s format: %s date: %s, may download partial files."%(
                                    self.feed_name,
                                    self.data_format,
                                    thisday.strftime("%Y-%m-%d")))
                                else:
                                    print_verbose("Files NOT READY in feed: %s format: %s date: %s, skipping."%(
                                    self.feed_name,
                                    self.data_format,
                                    thisday.strftime("%Y-%m-%d")))
                                    continue
                        #this list is only for $ALLFILES where is no md5 support anyway
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
                            else:
                                print_verbose("No files in %s, this can be normal." % (downloadurl_base))
                                self.failed.append(downloadurl_base)
                    #We do the main job here: downloading
                        for downloadurl in download_urls:
                            success = whois_web_download_utils.web_download_and_check_file(
                                downloadurl, md5url, self.session, thistargetdir, self.maxtries,
                                no_resume=self.no_resume)
                            if success:
                                print_verbose('SUCCESS: downloaded %s.' % (downloadurl))
                                self.downloaded.append(downloadurl)
                            else:
                                print_verbose('Could not download %s. It can be normal if it does not exist.' % (downloadurl))
                                self.failed.append(downloadurl)
                        #We have to treat archive stuff separately
            if self.download_masks_archive != None:
                print_verbose('Examining archive URLs')
                for mask in self.download_masks_archive:
                    for day in range(ndays):
                        thisdaysyear = (startdate + datetime.timedelta(days=day)).year
                        if thisdaysyear != datetime.date.today().year:
                            thismask = self.actual_url(mask.replace('$year',str(thisdaysyear)),
                                                       self.dbversion, tld, (startdate + datetime.timedelta(days=day)))
                            downloadurl = mainurl + '/' + thismask
                            md5url = None
                            thistargetdir=os.path.dirname(os.path.abspath(os.path.join(targetdir, self.feed_name, thismask)))
                            success = whois_web_download_utils.web_download_and_check_file(downloadurl,
                                                                                           md5url,
                                                                                           self.session,
                                                                                           thistargetdir,
                                                                                           self.maxtries,
                                                                                           no_resume=self.no_resume)
                            if success:
                                print_verbose('SUCCESS: downloaded %s.' % (downloadurl))
                                self.downloaded.append(downloadurl)
                            else:
                                print_verbose('Download of %s FAILED. It may not exist, or please try again.' % (downloadurl))
                                self.failed.append(downloadurl)
