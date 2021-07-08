# User interaction module of Whois API LLC end user scripts
#
#Copyright (c) 2010-2021 Whois API LLC,  http://www.whoisxmlapi.com
#

import sys
import os

import argparse
from argparse import RawTextHelpFormatter

import easygui as g

import re

#Logging functions
def print_error_and_exit(message):
    global DIALOG_COMMUNICATION
    if DIALOG_COMMUNICATION:
        _ = g.msgbox('Error. \n ' + message +'\nExiting.','WhoisXML API MySQL loader script')
        exit(1)
    else:
        sys.stderr.write('\nError: ' + message+'\n')
        sys.stderr.flush()
        exit(1)
def print_verbose(message):
    global VERBOSE
    global DEBUG
    if VERBOSE or DEBUG:
        sys.stderr.write(message + '\n')
        sys.stderr.flush()
def print_debug(message):
    global DEBUG
    if DEBUG:
        sys.stderr.write(message + '\n')
        sys.stderr.flush()
#File and directory utilites
def get_file(path, message):
    """Given a whatever path, verifies if it points to a file.
    If not, gives the error message and the path. 
    If yes,returns the file path"""
    thefile = os.path.normpath(path)
    if not os.path.isfile(thefile):
        print_error_and_exit(message +'\n (File specified: %s)' %(path))
    else:
        return(thefile)

def get_directory(path, message):
    """Given a whatever path, verifies if it points to a directory.
    If not, gives the error message and the path. 
    If yes,returns the file path as a pathlib object"""
    thefile = os.path.normpath(path)
    if not os.path.isdir(thefile):
        print_error_and_exit(message +'\n (Directory specified: %s)' %(path))
    else:
        return(thefile)
