#!/usr/bin/env python
#
# Script to download data from WhoisXML API subscriptions
# Provided for subscribers of quarterly whois data feeds
#
# Copyright (c) 2010-2021 Whois API, Inc,  http://www.whoisxmlapi.com
#

import sys
import os
from argparse import RawTextHelpFormatter, ArgumentParser
import easygui as g
import re
import datetime

import whois_utils.WhoisDataFeed as wdf
import whois_utils.whois_user_interaction as whois_user_interaction

from whois_utils.whois_user_interaction import *

# GlobalSettings
VERSION = "4.0.1"
MYNAME = sys.argv[0].replace('./', '')
MYDIR = os.path.abspath(os.path.dirname(__file__))
FEEDCONFIGDIR = MYDIR

# Read the list of supported formats.
# Probably the directory with "feeds.ini" should be given more precisely.
formatmatrix = wdf.feed_format_matrix(FEEDCONFIGDIR)
feed_descriptions = wdf.feed_descriptions(FEEDCONFIGDIR)

#We need the plans to feeds mapping
try:
    plans_feeds_matrix = {}
    plansfile = open(os.path.dirname(os.path.abspath(__file__))+\
                     "/new_generation_plans.dat",'rt')
    for line in plansfile.readlines():
        [m_plan, m_feeds] = line.strip().split(':')
        plans_feeds_matrix[m_plan] = m_feeds.split(",")
    plansfile.close()
except:
    print_error_and_exit('Problem with new_genration_plans.dat.')

if len(sys.argv) > 1 and sys.argv[-1].strip() != '--interactive':
    DIALOG_COMMUNICATION = False
    # command-line version, load_mysql_data.pyw has been started
    # Here we parse the command-line and get the values of the arguments
    parser = ArgumentParser(
        description='\n'.join(['Python script to download data from WhoisXML API feeds.',
                               'For data feed subscribers of WhoisXML API\n',
                               'See usage examles in the supplied README file.']),
        prog=MYNAME,
        formatter_class=RawTextHelpFormatter)
    # Vebosity, version, etc.
    parser.add_argument('--version',
                        help='Print version information and exit.',
                        action='version',
                        version=MYNAME + ' ver. ' + VERSION + '\n(c) WhoisXML API, Inc.')
    parser.add_argument('-v', '--verbose',
                        help='\n'.join(['Print messages. Recommended.',
                                        'If not specifies, the script runs quietly,',
                                        'only errors are reported.']),
                        action='store_true')
    parser.add_argument('-d', '--debug', help='Debug mode, even more messages', action='store_true')
    parser.add_argument('--maxtries', type=int,
                        help='Maximum number of tries when downloading. Defaults to 3.')
    parser.add_argument('--no-resume',
                        help='Disable resuming the download of a partially or completely downloaded file',
                        action='store_true')
    parser.add_argument('--no-premature',
                        help='Do not download files from daily feeds if the completion indicator is not there. Only effects daily feeds having download_ready_files',
                        action='store_true')
    parser.add_argument('--only-changed',
                        help='Use the added/dropped tlds lists instead of supported tlds to avoid checking all supported TLDs.',
                        action='store_true')
    parser.add_argument('--interactive',
                        help='\n'.join([
                            'Interactive mode.',
                            'If proivded as a first argument, ',
                            'you will be prompted for the parameters in GUI dialogue windows.']))
    parser.add_argument('--username', help='Username.')
    parser.add_argument('--password', help='Password (legacy/quarterly) or key (new-generation).')
    parser.add_argument('--sslauth',
                help='Enable ssl authentication instead of the default password authentication.',
                action='store_true')
    parser.add_argument('--plan',
                        type=str,
                        help='Subscription plan for new-generation access. The --password should be the key for the access. Implies --no-resume.')
    parser.add_argument('--disable-ssl-verification',
                        help='Disable ssl verification. Temporary solution, use this if and only if you get "Invalid ssl certificate" erros in spite of having the certificate. This is an issue that occurs e.g. with python 3.8 in case of feeds hosted on bestwhois.org. Will produce ssl warnings.',
                        action = 'store_true')
    parser.add_argument('--cacertfile',
                        help='\n'.join(['Location of the CA certificate for ssl auth.',
                                        'Defaults to whoisxmlapi.ca next to the script.']),
                        default=MYDIR + '/whoisxmlapi.ca')
    parser.add_argument('--crtfile',
                        help='\n'.join(['Location of the cert file for ssl auth.',
                                        'Defaults to client.crt next to the script.']),
                        default=MYDIR + '/client.crt')
    parser.add_argument('--keyfile',
                        help='\n'.join(['Location of the key file for ssl auth.',
                                        'Defaults to client.key next to the script.']),
                        default=MYDIR + '/client.key')
    parser.add_argument('--list-feeds',
                        help='List supported feeds. Other arguments are ignored',
                        action='store_true')
    parser.add_argument('--feed', help='Use this feed')
    parser.add_argument('--describe-feed',
                        action='store_true',
                        help='Print the description and data formats of the feed and exit.')
    parser.add_argument('--list-dataformats',
                        help='List the data formats supported by the feed',
                        action='store_true')
    parser.add_argument('--dataformats', help='The data formats to be downloaded.')
    parser.add_argument('--db-version',
                        help='\n'.join(['The quarterly db version to load.',
                                        'Required for daily feeds Format: vNN, e.g. v19']))
    parser.add_argument('--startdate',
                        help='The starting date for quarterly feed download, format: YYYYMMDD')
    parser.add_argument('--enddate',
                        help='\n'.join([
                            'The end date for quarterly feed download, format: YYYYMMDD.',
                            'If not provided, data are loaded for the startdate only.']))
    parser.add_argument('--list-supported-tlds',
                        help='download data for these tlds.',
                        action='store_true')
    parser.add_argument('--tlds',
                        help='\n'.join(['Download data for these tlds.',
                                        ('For data formats which are tld independent,'
                                         'you must chose a single supported by the feed,'
                                         'but it will be ignored.')]))
    parser.add_argument('--all-tlds',
                        help='Download data for all available tlds. Overrides --tlds',
                        action='store_true')
    parser.add_argument('--output-dir', help='Directory to download files into.')
    args = parser.parse_args()
    args = vars(args)
    whois_user_interaction.VERBOSE = args['verbose']
    whois_user_interaction.DEBUG = args['debug']
    whois_user_interaction.DIALOG_COMMUNICATION = False
    wdf.set_verbosity(args['debug'], args['verbose'], False)
    #Checking if we have feeds from the ini
    if formatmatrix == {}:
        print_error_and_exit(
            "Feed configuration invalid, probably missing feeds.ini file.\nPlease place the feeds.ini file supplied with the program next to the program.")
    # The user wants to list feeds
    if args['list_feeds']:
        sys.stdout.write("\n")
        if args['plan'] is not None:
            availablefeeds = plans_feeds_matrix[args['plan']]
            sys.stdout.write("\nSupported feeds and data formats in plan %s:"%args['plan'])
        else:
            sys.stdout.write("\nSupported feeds and data formats:")
            availablefeeds = formatmatrix.keys()
        sys.stdout.write('\n\n')
        for feed in availablefeeds:
            sys.stdout.write("- Feed: %.60s \n" % feed)
            sys.stdout.write("  Description: %s \n"% feed_descriptions[feed])
            sys.stdout.write("  Formats: ")
            for f in formatmatrix[feed]:
                sys.stdout.write("%s " % f)
            sys.stdout.write("\n")
        sys.stdout.write("\n\n")
        exit(6)
    # Check if feed is specified and valid
    if args['feed'] is None:
        print_error_and_exit(
            'You must specify a feed.'
            'See --list_feeds for the list of supported feeds and their data formats.')
    if args['feed'] not in set(formatmatrix.keys()):
        print_error_and_exit(
            'Invalid feed.'
            'See --list_feeds for the list of supported feeds and their data formats.')
    #If new-generation authentication is used, the plan should be compatible with the feed
    if args['plan'] is not None:
        if args['feed'] not in set(plans_feeds_matrix[args['plan']]):
            print_error_and_exit("Feed %s unavailable in plan %s."%(args['feed'], args['plan']))
    # The user wants data formats for this feed
    if args['list_dataformats']:
        sys.stdout.write("Data formats for feed %s: " % args['feed'])
        for f in formatmatrix[args['feed']]:
            sys.stdout.write("%s " % f)
        sys.stdout.write("\n")
        exit(6)
    if args['describe_feed']:
        sys.stderr.write("- Feed: %.60s \n" % args['feed'])
        sys.stderr.write("  Description: %s \n"% feed_descriptions[args['feed']])
        sys.stderr.write("  Formats: ")
        for f in formatmatrix[args['feed']]:
            sys.stderr.write("%s " % f)
        sys.stderr.write("\n")
        exit(6)
    # Collect and vaidate data formats
    try:
        args['dataformats'] = args['dataformats'].split(',')
    except:
        print_error_and_exit('No data formats specified')
    for f in args['dataformats']:
        if f not in set(formatmatrix[args['feed']]):
            print_error_and_exit('Feed %s does not support the data format %s.' % (args['feed'], f))
    # When using NAF, disable resume download
    if args['plan'] is not None:
        print_debug("No resume for new-generation access.")
        args['no_resume'] = True
    # Create feeds
    feeds=[]
    for dataformat in args['dataformats']:
        the_feed = wdf.WhoisDataFeed()
        the_feed.set_maxtries(args['maxtries'])
        the_feed.set_no_resume(args['no_resume'])
        the_feed.set_feed_type(FEEDCONFIGDIR, args['feed'], dataformat)
        feeds.append(the_feed)

    # Set database version for quarterly feeds
    if the_feed.is_quarterly:
        if re.match(r'^v[0-9]+$', str(args['db_version'])) is not None:
            for f in feeds:
                f.set_quarterly_dbversion(args['db_version'])
        else:
            print_error_and_exit(
                'Database version not specified for quarterly feed, or invalid format. '
                'Should be e.g. "v20".')
    # Set intervals for daily feeds
    elif the_feed.is_daily:
        if args['startdate'] is None or not re.match(r'^[0-9]{8}$', str(args['startdate'])):
            print_error_and_exit(
                'Start date must be specified for a daily feed, in the format YYYYMMDD')
        startdate = datetime.datetime.strptime(args['startdate'], '%Y%m%d')
        if args['enddate'] is not None:
            if re.match(r'^[0-9]{8}$', str(args['enddate'])):
                enddate = datetime.datetime.strptime(args['enddate'], '%Y%m%d')
                if enddate < startdate:
                    print_error_and_exit('End date must be later than start date.')
            else:
                print_error_and_exit('End date must be in the format YYYYMMDD')
        else:
            enddate = None
        # set up the date intervals of the feeds
        for f in feeds:
            f.set_daily_feed_interval(startdate, enddate)
    # setup login credentials
    for the_feed in feeds:
        if args['sslauth']:
            if args['disable_ssl_verification']:
                the_feed.set_login_credentials(
                    'ssl',
                    cacertfile=False,
                    keyfile=args['keyfile'],
                    crtfile=args['crtfile'])

            else:
                the_feed.set_login_credentials(
                    'ssl',
                    cacertfile=args['cacertfile'],
                    keyfile=args['keyfile'],
                    crtfile=args['crtfile'])
        elif args['username'] is not None and args['password'] is not None \
             and args['plan'] is None:
                the_feed.set_login_credentials(
                    'password',
                    login = args['username'],
                    password = args['password'])
        elif args['plan'] is not None:
            if args['password'] is None:
                args['password'] = ''
            the_feed.set_login_credentials(
                'NAF',
                naf_subscription=args['plan'],
                password=args['password'])
        else:
            the_feed.set_login_credentials('password')
    the_feed.test_http_access()
    if not the_feed.loginOK:
        print_error_and_exit(
            'Login failed. \n'
            'Some possible reasons:\n'
            '  -bad username or password specified in the command-line \n'
            '  -bad username or password in ~/.whoisxmlapi_login.ini\n'
            '  -invalid ssl auth credentials if sslauth used\n'
            '  -wrong or non-existing quarterly database version specified\n')
    # Update list of available tlds
    dontneedtlds = True
    #note: the user may mix tld dependent and independent feeds
    for the_feed in feeds:
        the_feed.open_http_session()
        dontneedtlds = dontneedtlds and the_feed.tldindependent
    else:
        available_tlds = []
    if not dontneedtlds:
        for the_feed in feeds:
            if not the_feed.tldindependent:
                the_feed.set_use_alt_tlds(args["only_changed"])
                the_feed.update_supported_tlds()
                available_tlds.append(set(the_feed.supported_tlds))
        available_tlds = sorted(list(frozenset().union(*available_tlds)))

    if args['list_supported_tlds']:
        sys.stderr.write("Available tlds:\n")
        for tld in available_tlds:
            sys.stderr.write('%s, ' % tld)
        sys.stderr.write("\n")
        exit(6)
    # Here we have the set of available tlds
    if dontneedtlds:
        args['tlds'] = ['ALL']
    else:
        if args['all_tlds']:
            args['tlds'] = available_tlds
        else:
            # We set up the tld set as the intersection of the ones given in
            # --tlds and the supported one.
            # Verify supported tlds list
            try:
                args['tlds'] = args['tlds'].split(',')
            except:
                print_error_and_exit('You must specifiy the list of tlds to download')
            tldsset = set(args['tlds'])
            args['tlds'] = list(tldsset.intersection(set(available_tlds)))
    if args['tlds'] == []:
        print_error_and_exit('All specified tlds are either unsupported or have no data for the given day(s).')
    # verify if the output directory exists
    if args['output_dir'] is None:
        print_error_and_exit('Please specify the output directory.')
    args['output_dir'] = os.path.abspath(args['output_dir'])
    if not(os.path.isdir(args['output_dir'])):
        print_error_and_exit('The output directory %s does not exist' % args['output_dir'])
    # Now we have set up everything to do some downloading
else:
    # Interacitve version with easygui
    args = {}
    DIALOG_COMMUNICATION = True
    args['no_premature'] = False
    args['only_changed'] = False
    #With dialogs we are always verbose but never debug
    whois_user_interaction.VERBOSE = True
    whois_user_interaction.DEBUG = False
    whois_user_interaction.DIALOG_COMMUNICATION = True
    wdf.set_verbosity(False, True, True)
    if formatmatrix == {}:
        print_error_and_exit(
            "Feed configuration data not found, probably missing feeds.ini file.\nPlease place the feeds.ini file supplied with the program next to the program.")
    # Things you cannot do when interactive
    # Note: set the next two to True for console debug
    args['cacertfile'] = MYDIR + '/whoisxmlapi.ca'
    args['crtfile'] = MYDIR + '/client.crt'
    args['keyfile'] = MYDIR + '/client.key'
    args['verbose'] = True
    args['debug'] = False
    args['no_resume'] = True
    # Default window title
    windowtitle = 'WhoisXML API MySQL data downloader script'

    answer = g.msgbox('\n'.join([
        'This is %s: a script to download data feeds from WhoisXML API subscriptions.'
        '(C) WhoisXML API LLC.', '',
        'Please make sure that you have the username and password', '',
        'Press O.K. to start.']) % MYNAME,
        windowtitle)
    if answer is None:
        exit(6)

    plans = ['Legacy/quarterly'] + list(plans_feeds_matrix.keys())
    answer = g.choicebox('Choose your subscripton plan. \n Choose "Legacy/quarterly" if your username and password differ',
                              windowtitle,
                              plans)
    if answer is None:
        exit(6)
    if answer != 'Legacy/quarterly':
        args['plan'] = answer
        nafmode = True
        feeds = plans_feeds_matrix[answer]
    else:
        feeds = formatmatrix.keys()
        nafmode = False
    # a not very elegant solution to overcome limitations of easygui
    feedoptions = []
    feedorder = []
    for feed in sorted(feeds):
        feedoptions.append(feed.ljust(42) + ": " + feed_descriptions[feed])
        feedorder.append(feed)
    answer = g.choicebox('\n'.join([
        'Choose a feed you would like to download data from.',
        'Note: you have to be a subscriber of that.']), windowtitle, feedoptions)
    if answer is None:
        exit(6)
    feedno = feedoptions.index(answer)
    args['feed'] = feedorder[feedno]
    if len(formatmatrix[args['feed']]) > 2:
        answer = g.multchoicebox('Choose the preferred data format(s)',
                                 windowtitle, formatmatrix[args['feed']])
        if answer is None:
            exit(6)
        args['dataformats'] = answer
    else:
        args['dataformats'] = formatmatrix[args['feed']]
        g.msgbox("The feed supports a single data format: %s.\nData will be downloaded in this format."%args['dataformats'][0]) 


    # Start initializing feed
    feeds = []
    for dataformat in args['dataformats']:
        the_feed = wdf.WhoisDataFeed()
        the_feed.set_no_resume(args['no_resume'])
        the_feed.set_feed_type(FEEDCONFIGDIR, args['feed'], dataformat)
        feeds.append(the_feed)
    # If a quarterly feed is chosen, we must get the dbversion
    if the_feed.is_quarterly:
        while the_feed.dbversion is None:
            answer = g.enterbox(
                "You have chosen a quarterly feed. Please suppy the database version, e.g. 'v20'",
                windowtitle)
            if re.match(r'^v[0-9]+$', answer) is not None:
                the_feed.set_quarterly_dbversion(answer)
                args['db_version'] = answer
            else:
                answer = g.ynbox('Invalid database name format. Try again?')
                if not answer:
                    exit(1)
        args['db-version'] = answer
        for f in feeds:
            f.set_quarterly_dbversion(answer)
    elif the_feed.is_daily:
        startdate = None
        while startdate is None:
            answer = g.enterbox('\n'.join([
                'You have chosen a daily feed. Please specify the first day to download data for ',
                "in the form 'YYYYMMDD', e.g. '20170728'"]), windowtitle)
            if answer is None:
                exit(6)
            if not re.match(r'^[0-9]{8}$', answer):
                startdate = None
            else:
                startdate = answer
                args['startdate'] = answer
        startdate = datetime.datetime.strptime(startdate, '%Y%m%d')
        enddate = None
        while enddate is None:
            answer = g.enterbox('\n'.join([
                'Please suppy the last day you are interested',
                "in the format 'YYYYMMDD', e.g. '20170728'",
                'Leve blank and press O.K. if you want do download a single day only.']),
                windowtitle)
            if answer is None:
                exit(6)
            if not (re.match(r'^[0-9]{8}$', answer) or answer == ''):
                args['enddate'] = answer
                enddate = None
            else:
                args['startdate'] = answer
                enddate = answer
        if enddate == '':
            enddate = None
        else:
            enddate = datetime.datetime.strptime(enddate, '%Y%m%d')
        print_verbose('Start date: %s\nEnd date: %s' % (str(startdate), str(enddate)))
        for f in feeds:
            f.set_daily_feed_interval(startdate, enddate)


    # Check if the ssl key file exists and decide upon auth type
    answer=False
    if (
        os.path.isfile(args['keyfile']) and
        os.path.isfile(args['crtfile']) and
        os.path.isfile(args['cacertfile'] and not nafmode)
    ):
        answer = g.ynbox('\n'.join(['SSL auth config detected.',
                                    'Do you want to use ssl auth?',
                                    '(If not, we go for password auth.)']),
                         windowtitle)
    if answer:
        args['sslauth'] = True
        args['disable_ssl_verification'] = True
    else:
        args['sslauth'] = False
        # Get and verify user acces credentials for the feed

    defaultusername = ''
    while not the_feed.loginOK:
        if args['sslauth']:
            the_feed.set_login_credentials('ssl', cacertfile=False)
        else:
            if not nafmode:
                answer = g.enterbox('\n'.join([
                    'Enter your username for the chosen WhoisXML API feed.',
                    'Leave it empty if you have configured ~/.whoisxmlapi_login.ini']),
                    windowtitle, default=defaultusername)
                if answer is None:
                    exit(6)
                args['username'] = answer
                defaultusername = answer
            else:
                answer = ''
            if not nafmode and answer.strip() != '':
                answer = g.passwordbox('Enter your password for the user %s' % (args['username'],),
                                       windowtitle)
                if answer is None:
                    exit(6)
            elif nafmode:
                answer = g.passwordbox('Enter your API key serving as your username and password',
                                       windowtitle)
                if answer is None:
                    exit(6)
            # If the username is an empty string, the password will be also one.
            args['password'] = answer
            if nafmode:
                the_feed.set_login_credentials(
                    'NAF',
                    naf_subscription=args['plan'],
                    password=args['password'])
            else:
                the_feed.set_login_credentials(
                    'password',
                    login=args['username'],
                    password=args['password'])
        the_feed.test_http_access()
        if not the_feed.loginOK:
            answer = g.ynbox('\n'.join([
                'Login failed. '
                'Bad login/password, '
                'or nonexistent database version or bad ssl auth credentials.',
                'If read from ~/.whoisxmlapi_login.ini, then it is probably wrong there.',
                'To re-enter database version, quit now and start again.',
                'Try again?']))
            if not answer:
                exit(1)
    for the_feed in feeds:
        if args['sslauth']:
            the_feed.set_login_credentials('ssl', cacertfile=False)
        elif nafmode:
            the_feed.set_login_credentials(
                    'NAF',
                    naf_subscription=args['plan'],
                    password=args['password'])
        else:
            the_feed.set_login_credentials('password',
                                           login=args['username'],
                                           password=args['password'])

    # Feed has been set up now.
    # For daily feeds, get date range
    # Update list of available tlds
    dontneedtlds = True
    #note: the user may mix tld dependent and independent feeds
    for the_feed in feeds:
        the_feed.open_http_session()
        the_feed.set_use_alt_tlds(args["only_changed"])
        the_feed.update_supported_tlds()
        dontneedtlds = dontneedtlds and the_feed.tldindependent
    if dontneedtlds:
        args['tlds'] = ['ALL']
    else:
        available_tlds = [set(the_feed.supported_tlds) for the_feed in feeds]
        available_tlds = sorted(frozenset().union(*available_tlds))
        answer = g.multchoicebox('\n'.join([
            'Choose the TLDs for which you want to load data.']),
                                 windowtitle, available_tlds)
        if answer is None:
            exit(6)
        args['tlds'] = answer
        print_verbose('Tlds to load: %s' % (str(args['tlds']),))

    # Choose the output root directory
    answer = g.diropenbox(
        title=windowtitle,
        msg='Choose the directory to download files into.')
    if answer is None:
        exit(6)
    args['output_dir'] = answer

print_verbose('Feed to download from: %s' % (args['feed'],))
print_verbose('Data format(s): %s' % (str(args['dataformats']),))

if feeds[0].is_quarterly:
    print_verbose('Quarterly feed database version: %s' % (args['db_version'],))
if feeds[0].is_daily:
    print_verbose('Daily feed start date: %s\nend date: %s' % (str(startdate), str(enddate)))

print_verbose('Tlds(s) (only the supported ones): %s' % (str(args['tlds']),))

# The main job will start here
total_failed = []
total_premature = []
for f in feeds:
    f.set_download_premature(not args['no_premature'])
    f.download_feed_into_directory(args['tlds'], args['output_dir'])
    total_failed += f.failed
    total_premature += f.premature
    total_premature = list(set(total_premature))
# removing duplicates as some feeds might download redundantly
total_failed = list(set(total_failed))
print_verbose('Download finished.')
all_ok = True
if len(total_failed) > 0:
    print_verbose('The following URLs have failed (probably they do not exist.):')
    for u in total_failed:
        print_verbose(u)
    print_verbose('Re-run with the same settings to retry, but this maybe normal.')
    retcode = 2
    all_ok = False
    
if len(total_premature) > 0:
    print_verbose('The data in the following feeds in the formats on the listed dates were not completely generated when downloading:')
    for s in sorted(total_premature):
        print_verbose("\t" + s)
    if args['no_premature']:
        print_verbose("The respective downloads were skipped, try again later.")
    else:
        print_verbose("The downloaded files can be missing or incomplete.")
    all_ok = False
    retcode = 3
    
if all_ok:
    print_verbose('Everything has been downloaded successfully.')
    retcode = 0



if DIALOG_COMMUNICATION:
    _ = g.msgbox('\n'.join([
        '%s has finished its activity.',
        'Please take a look at the terminal window to see the log.',
        'Afterwards, press OK to close this window and quit.']) % MYNAME, windowtitle)

#We exit with 2 if any file which was supposed to be there failed to download.
exit(retcode)
