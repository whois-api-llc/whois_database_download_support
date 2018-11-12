# Web download module of Whois API LLC end user scripts
#
# Copyright (c) 2010-2017 Whois API LLC,  http://www.whoisxmlapi.com
#

from urlparse import urlparse
from HTMLParser import HTMLParser
import requests
import os, hashlib, re
import datetime
import time
import whois_user_interaction
from whois_user_interaction import *
whois_user_interaction.VERBOSE = True
whois_user_interaction.DEBUG = True

class Indexparser(HTMLParser):
    """This parser parses an autoindexed directory and finds files
    which are supposed to be the <a href > attributes not having a slash in them"""
    FileList = []
    def reset_filelist(self):
        self.FileList = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if not re.search(r'/', attr[1]):
                    self.FileList.append(attr[1])

Index_Parser = Indexparser()

def md5_check( path_filename, md5_file_path ):
    """ Determines if the md5 checksum checks out

    Return:
        Returns a true if the checksum is correct,
        false if it is wrong or either the file or the checksum does not exist.
    """
    try:
        calc_check_sum = calc_md5( path_filename )
        with open( md5_file_path ) as md5_file:
            correct_check_sum = md5_file.readline().split()[0].strip()
            if( calc_check_sum == correct_check_sum ):
                return True
            return False
    except:
        return False

def calc_md5( path_filename ):
    """ Calculates the md5 of a file
    
    Return:
        Returns the hex digits in string form representing md5 of file
    """
    hash_md5 = hashlib.md5()
    with open( path_filename , "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def web_download_and_check_file(url, md5url, session, output_dir, maxtries):
    """Given a session, downloads the file and its md5. If it fails according to the md5, retries maxtries times"""
    filename = os.path.basename(urlparse(url).path)
    filename = os.path.abspath(os.path.join(output_dir, filename))
    if md5url != None:
        md5filename = os.path.basename(urlparse(md5url).path)
        md5filename = os.path.abspath(os.path.join(output_dir, md5filename))
    else:
        md5filname=None
        
    gotit = False
    force = False
    giveup = False
    ntries = 0
    while not gotit and not giveup and ntries < maxtries:
        print_verbose('Verified download of %s: attempt #%d' % (url, ntries+1))
        gotfile = web_download_file(url, session, output_dir, maxtries, force)
        if md5url != None:
            gotmd5 = web_download_file(md5url, session, output_dir, maxtries, force)
        else:
            gotmd5 = False
        if gotfile and gotmd5:
            gotit = md5_check(filename, md5filename)
            if not gotit:
                print_verbose('Verified download: attempt #%d failed, md5 does not match. Redownloading.' % (ntries+1))
        elif gotfile and not gotmd5:
            print_verbose('File downloaded but no md5 sum. Unverified. This can be normal.')
            gotit = True
        else:
            print_verbose('File not found, it may not exist on the server.')
            gotit = False
            giveup = True
        ntries += 1
        #second time we redownload_anyway
        force = True
    return gotit
        
        
def web_download_file(url, session, output_dir, maxtries, force):
    """Given a session, downloads the file into the directory. Creates the directory if it does not exists.
    if force, downloads also if it does not exist"""

    filename = os.path.basename(urlparse(url).path)
    filename = os.path.abspath(os.path.join(output_dir, filename))
    print_debug('File to download: %s' % (filename))
    # Make dir to output files to if it 
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    url_print = os.path.basename(url)
    # Redownload file, if problem occurs with network
    ntries = 0
    if os.path.isfile(filename) and not force:
        print_verbose('File %s exists. Not downloading again now.' % (filename))
        return(True)
    else:
        while ntries < maxtries:
            print_debug('Try #%d' % (ntries + 1))
            try:
                r = session.get(url, stream=True, timeout=30)
                print_debug('Status code: %s' % r.status_code)
                if r.status_code == 200:
                    with open(filename, 'wb') as out:
                        if( 'content-length' in (r.headers) ):
                            dl_total_length = int(r.headers.get('content-length'))
                            print_debug('Total length: %s' % (str(dl_total_length)))
                        dl_size=0
                        dl_start_chunk = datetime.datetime.now()

                        sys.stdout.write("\r                                                    ")
                        sys.stdout.flush()
                        for chunk in r.iter_content(chunk_size=(1024*1024)):
                            out.write(chunk)
                            dl_end_chunk = datetime.datetime.now()
                            dl_size += len(chunk)
                            #if dl_start_chunk != 0 and 'content-length' in (r.headers):
                            if 'content-length' in (r.headers):
                                # dl_done = int(100 * dl_size / dl_total_length)
                                dl_done = float(dl_size) / dl_total_length
                                dl_dtdelta = ( dl_end_chunk - dl_start_chunk ).microseconds
                                # sys.stdout.write("\r%s %s" % (dl_done, str( 1024 * 60 / dl_dtdelta) ))
                                # sys.stdout.write("\r{0:.2%} {1}".format(dl_done, str( 1024 * 60 / dl_dtdelta) ))
                                sys.stdout.write("\r{0} Progress: {1:.2%}".format(url_print, dl_done))
                                sys.stdout.flush()
                            dl_start_chunk = datetime.datetime.now()
                            # sys.stdout.write("\rFile has been downloaded successfully".format(1))
                            
                            # Clears line
                    sys.stdout.write("\r{0} [OK]                          ".format(url_print))
                    sys.stdout.flush()
                                    # print "File has been downloaded successfully."
                elif r.status_code == 401:
                    print "HTTP %s Unauthorized. Login credentials are wrong." % r.status_code
                    return False
                elif r.status_code == 404:
                    print "HTTP %s does not exist." % (url_print)
                    ntries = maxtries + 1
                    return False
                else:
                    sys.stdout.write("\r%s [Failed] Status code: %s \n" % (str(url_print), str(r.status_code)))
                    sys.stdout.flush()
                    return False
                    # print "Error HTTP %s File Not Found" % r.status_code
            except requests.exceptions.Timeout or requests.exceptions.ConnectionError:
                sys.stdout.write("\rNetwork timed out. Attempting redownload..")
                sys.stdout.flush()
                time.sleep(4)
                ntries += 1
                continue
            except requests.exceptions.ConnectionError or requests.exceptions.ChunkedEncodingError:
                sys.stdout.write("\rNetwork timed out. Attempting redownload..")
                sys.stdout.flush()
                time.sleep(4)
                ntries += 1
                continue
            except requests.exceptions.ChunkedEncodingError:
                sys.stdout.write("\rChunked Encoding Error. Redownloading")
                sys.stdout.flush()
                time.sleep(4)
                ntries += 1
                continue
            sys.stdout.write('\n')
            sys.stdout.flush()
            return(True)

def webdir_ls(url, session):
    """given the session and the URL, return the list of all files in the direcotry
    as a list of filenames to be appended to the URL
    The URL MUST point to an autoindexed directory (not verified by the function)
    An empty list is returned if something goes wrong.
    """
    rawdirlist = session.get(url, stream=True, timeout=30)
    if rawdirlist.status_code == 200:
        Index_Parser.reset_filelist()
        Index_Parser.feed(rawdirlist.text)
        return(Index_Parser.FileList)
    else:
        return([])
