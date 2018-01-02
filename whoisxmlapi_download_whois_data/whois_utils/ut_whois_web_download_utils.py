#!/usr/bin/env python

import whois_web_download_utils
import requests
import urlparse
import os
import shutil
import unittest


def filename_from_url(url):
    "Return filename from an URL"
    filename = os.path.basename(urlparse.urlparse(url).path)
    return(filename)

class TestMd5(unittest.TestCase):
    def test_md5(self):
        """This tests the md5 verifier function md5_check"""
        #File and its md5
        self.assertTrue(whois_web_download_utils.md5_check('ut_directory/foo.csv.gz','ut_directory/foo.csv.gz.md5'))
        #File does not exist
        self.assertFalse(whois_web_download_utils.md5_check('ut_directory/baz.csv.gz','ut_directory/foo.csv.gz.md5'))
        #Neither file, nor md5 exist
        self.assertFalse(whois_web_download_utils.md5_check('ut_directory/baz.csv.gz','ut_directory/bar.csv.gz.md5'))
        #File's md5 is not the given md5
        self.assertFalse(whois_web_download_utils.md5_check('ut_directory/bar.csv.gz','ut_directory/foo.csv.gz.md5'))
    def test_download_file_with_test(self):
        """Test downloading with verification"""
        testdir='./ut_directory'
        testfile_url='http://bestwhois.org/domain_name_data/domain_names_whois/2017_06_03_aero.csv.gz'
        testfile_md5url='http://bestwhois.org/domain_name_data/domain_names_whois/hashes/2017_06_03_aero.csv.gz.md5'
        test_login = 'koniorm@gmail.com'
        test_password = 'CCrsXzcCxQ4D'
        test_session = requests.Session()
        test_session.auth = (test_login, test_password)
        #Removing files if they are there
        try:
            os.remove(os.path.join(testdir, filename_from_url(testfile_url)))
            os.remove(os.path.join(testdir, filename_from_url(testfile_md5url)))
        except:
            pass
        whois_web_download_utils.web_download_and_check_file(testfile_url, testfile_md5url, test_session, testdir, 5)
        self.assertTrue(whois_web_download_utils.md5_check(
            os.path.join(testdir, filename_from_url(testfile_url)),
            os.path.join(testdir, filename_from_url(testfile_md5url))))
        #Now we copy a wrong md5 to the place of the right one
        shutil.copy(os.path.join(testdir, 'foo.csv.gz.md5'), os.path.join(os.path.join(testdir, filename_from_url(testfile_md5url))))
        whois_web_download_utils.web_download_and_check_file(testfile_url, testfile_md5url, test_session, testdir, 5)
        self.assertTrue(whois_web_download_utils.md5_check(
            os.path.join(testdir, filename_from_url(testfile_url)),
            os.path.join(testdir, filename_from_url(testfile_md5url))))
        
suite = unittest.TestLoader().loadTestsFromTestCase(TestMd5)
unittest.TextTestRunner(verbosity=3).run(unittest.TestSuite([suite]))
