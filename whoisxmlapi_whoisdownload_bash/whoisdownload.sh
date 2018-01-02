#! /bin/bash

#
# Configuration values.
#
LOGIN_NAME=""
LOGIN_PASSWORD=""

#
# Global variables.
#
LANG=C
LC_ALL=C
VERSION="0.0.16"
VERBOSE="no"
DEBUG="no"
MYNAME=$(basename $0)
TLD=""
TLD_FILE=""
DATE=""
FEEDS=""
NDAYS=""
OUTPUT_DIR=""
DRY_RUN="no"
DRY_RUN_MULTIFILE_LIMIT=10
FILEFORMAT="regular"
#note: database version has to be specified explicitly
DATABASEVERSION="UNSPECIFIED"
START_DIRECTORY=$PWD1
PRINT_URLS=""
PRINT_FEEDS=""
PRINT_FORMATS=""

if [ -f "$HOME/.whoisdownload" ]; then
    source $HOME/.whoisdownload
fi

#
# Prints one specific error message and exits.
#
function printDateMissingAndExit()
{
    echo "Missing date." >&2
    echo "Use the --date=YYYY-MM-dd option to specify date." >&2
    echo "" >&2

    exit 1
}

#
# Prints the version number and exits.
#
function printVersionAndExit()
{
    echo "$MYNAME Version $VERSION"
    echo ""
    exit 0
}

function printHelpAndExit()
{
    echo "Usage: $MYNAME [OPTION]..."
    echo "$MYNAME Downloads information for registered domains."
    echo ""
echo " -h, --help            Print this help and exit."
echo " -v, --version         Print version information and exit."
echo " --verbose             Print more messages."
echo " --data-feeds=FEEDS    One or more data feeds to download."
echo " --tld=TLD             One or more top level domains to download."
echo " --tld-file=FILENAME   Load the list of TLDs from a text file."
echo " --user=USERNAME       User name to login to the data source."
echo " --password=PASSWORD   Password to login to the data source."
echo " --output-dir=PATH     The output directory."
echo " --file-format=FORMAT  Choose the given file format where available."
echo " --db-version=STRING   Set the version to download. Required for quarterly feeds. Format: vNN, e.g. v19"
echo " --n=INTEGER           Sets how many days to download."
echo " --date=YYYY-MM-dd     The date of the files to check. All the date format"
echo "                       formats that the date(1) utility accepts are supported."
    echo ""
    echo "Examples:"
    echo "$MYNAME --user=demo --password=xxxxxxx --date=2015_11_16 --tld=com --output-dir=./tmp --data-feeds=domain_names_whois --file-format=sql"
    echo ""
    echo "$MYNAME --user=demo --password=xxxxxxx --output-dir=./tmp --date=\"2015-10-20\" --date=\"2015-10-21\" --tld=\"org info\" --data-feeds=\"domain_names_new domain_names_dropped\""

    echo ""
    echo "Supported data feeds:"
    echo "  o domain_names_new "
    echo "  o domain_names_dropped "
    echo "  o domain_names_dropped_whois "
    echo "  o domain_names_whois "
    echo "  o domain_names_whois_filtered_reg_country "
    echo "  o domain_names_whois_filtered_reg_country_noproxy "
    echo "  o domain_names_whois_archive "
    echo "  o domain_names_whois_filtered_reg_country_archive "
    echo "  o domain_names_whois_filtered_reg_country_noproxy_archive"
    echo "  o whois_record_delta_whois"
    echo "  o whois_record_delta_domain_names_change"
    echo "  o ngtlds_domain_names_new"
    echo "  o ngtlds_domain_names_dropped"
    echo "  o ngtlds_domain_names_dropped_whois "
    echo "  o ngtlds_domain_names_whois"
    echo "  o ngtlds_domain_names_whois_filtered_reg_country "
    echo "  o ngtlds_domain_names_whois_filtered_reg_country_noproxy "
    echo "  o ngtlds_domain_names_whois_archive"
    echo "  o ngtlds_domain_names_whois_filtered_reg_country_archive "
    echo "  o ngtlds_domain_names_whois_filtered_reg_country_noproxy_archive "
    echo "  o cctld_discovered_domain_names_new"
    echo "  o cctld_discovered_domain_names_whois"
    echo "  o cctld_registered_domain_names_new"
    echo "  o cctld_registered_domain_names_whois"
    echo "  o cctld_registered_domain_names_dropped"
    echo "  o cctld_registered_domain_names_dropped_whois"
    echo "  o whois_database"
    echo "  o whois_database_combined"
    echo "  o domain_list_quarterly"
    echo ""
    echo "The following file formats are available:"
    echo "  o regular or regular_csv"
    echo "  o simple or simple_csv"
    echo "  o full or full_csv"
    echo "  o sql or mysqldump"
    echo "  o all"
    echo ""
    echo ""
    exit 1
}

#
#
# Prints all the arguments but only if the program is in the verbose mode.
#
function printVerbose()
{
    if [ "$VERBOSE" == "true" ]; then
        echo $* >&2
    fi
}

#
# Prints an error message to the standard error. The text will not mixed up with
# the data that is printed to the standard output.
#
function printError()
{
    echo "$*" >&2
}

function printMessage()
{
    echo -n "$*" >&2
}

function printMessageNl()
{
    echo "$*" >&2
}

function printDebug()
{
    if [ "$DEBUG" == "yes" ]; then
        echo "$*" >&2
    fi
}


ARGS=$(\
    getopt -o hv \
        -l "help,verbose,version,user:,password:,tld:,date:,output-dir:,\
data-feeds:,file-format:,tld-file:,db-version:,n:,dry,\
print-feeds,print-urls,print-formats" \
        -- "$@")


if [ $? -ne 0 ]; then
    exit 6
fi

eval set -- "$ARGS"
while true; do
    case "$1" in
        -h|--help)
            shift
            printHelpAndExit
            ;;

        --verbose)
            shift
            VERBOSE="true"
            ;;

        -v|--version)
            shift
            printVersionAndExit
            ;;
        
        --user)
            shift
            LOGIN_NAME=$1
            shift
            ;;

        --password)
            shift
            LOGIN_PASSWORD=$1
            shift
            ;;

        --data-feeds)
            shift
            FEEDS=$1
            shift
            ;;

        --file-format)
            shift
            FILEFORMAT=$1
            shift
            ;;
        
        --db-version)
            shift
	    #format check
	    if echo $1 | grep --quiet -e "v[0-9]*"; then
		DATABASEVERSION=$1
	    else
		printError "Invalid db-version specification. It should be like v19 or v6"
		exit 1
	    fi
            shift
            ;;

        --tld)
            shift
            TLD=$1
            #
            # User might use "all" or leave this empty, both should download all
            # the tlds.
            #
            if [ "$TLD_FILE" ]; then 
                printError "The --tld and --tld-files are mutually exclusive."
                exit 1
            fi

            if [ "$TLD" == "all" ]; then
                TLD=""
            fi
            shift
            ;;

        --tld-file)
            shift
            TLD_FILE=$(readlink -e "$1")
            if ! [ -f "$TLD_FILE" ]; then
                printError "File $TLD_FILE is not found."
                exit 1
            fi
            
            if [ "$TLD" ]; then 
                printError "The --tld and --tld-files are mutually exclusive."
                exit 1
            fi
            shift
            ;;

        --date)
            shift
            #
            # We accept both the 2015-08-29 and the 2015_08_29 notation,
            # internally we use '-'.
            #
            if [ "$DATE" ]; then
                DATE+=" "
            fi
           
            TMPDATE=$(echo "$1" | tr '_' '-')
            TMPDATE=$(date -d "$TMPDATE" "+%Y-%m-%d")
            DATE+="$TMPDATE"
            shift
            ;;

        --n)
            shift
            NDAYS=$1
            shift
            ;;

        --output-dir)
            shift
            OUTPUT_DIR=$1
            shift
            ;;

        --dry)
            shift
            #
            # This is for testing, dry-run => we won't actually download the
            # data files.
            #
            DRY_RUN="yes"
            ;;

        --print-feeds)
            shift
            PRINT_FEEDS="true"
            ;;

        --print-formats)
            shift
            PRINT_FORMATS="true"
            ;;

        --print-urls)
            shift
            PRINT_URLS="true"
            ;;

        --)
            shift
            break
            ;;

        *) 
            ;;
    esac
done

#Conditions to meet when all args are known
#If downloading quarterlies, the database version should be specified
if echo $FEEDS | grep --quiet -e "whois_database\|domain_list_quarterly" && [ $DATABASEVERSION = "UNSPECIFIED" ]; then
    printError "The specified feed needs an explicit database version specification such as --db-version=vNN"
    exit 1
fi
    
#
# $1: the base url for which we need the password
# 
# This function prints the login name for authention. The login name can come
# from the command line or from the configuration file.
#
function login_name()
{
    local base_url="$1"

    if [ "$LOGIN_NAME" ]; then
        echo "$LOGIN_NAME"
        return 0
    fi

    if [ "$base_url" == "http://bestwhois.org" ]; then
        echo "$BESTWHOIS_USER"
        return 0
    elif [ "$base_url" == "http://www.domainwhoisdatabase.com" ]; then
        echo "$WHOISDATABASE_USER"
        return 0
    else
        printError "Base URL '$base_url' not supported."
        return 1
    fi
}


#
# $1: the base url for which we need the password
#
# This function prints the password for authention. The password can come from
# the command line or from the configuration file.
#
function login_password()
{
    local base_url="$1"

    if [ "$LOGIN_PASSWORD" ]; then
        echo "$LOGIN_PASSWORD"
    fi
    
    if [ "$base_url" == "http://bestwhois.org" ]; then
        echo "$BESTWHOIS_PASSWORD"
        return 0
    elif [ "$base_url" == "http://www.domainwhoisdatabase.com" ]; then
        echo "$WHOISDATABASE_PASSWORD"
        return 0
    else
        printError "Base URL '$base_url' not supported."
        return 1
    fi
}

#
# $1: baseUrl
# $2: dirname
# $3: filename
#
function downloadSupportedTlds()
{
    local baseUrl="$1"
    local dirname="$2"
    local filename="$3"
    local fullurl="${baseUrl}/${dirname}/${filename}" 

    mkdir -p $dirname
    pushd $dirname >/dev/null
    
    if [ "$DEBUG" == "yes" ]; then
        printMessage "$fullurl  "
    else
        printMessage "$filename  "
    fi
   
    wget \
        --user="$(login_name $baseUrl)" \
        --password="$(login_password $baseUrl)" \
        $fullurl 2>wget.log >wget.log
    
    if grep --quiet "404 Not Found" wget.log; then
        printError "[NOT FOUND]"
        rm -f wget.log
        popd >/dev/null
        return 1
    elif grep --quiet "Password Authentication Failed" wget.log; then
        printError "[AUTH FAILED]"
        rm -f wget.log
        popd >/dev/null
        return 1
    elif  grep --quiet "403 Forbidden" wget.log; then
        echo "[NONEXISTENT OR UNAVAILABLE RESOURCE]"
        rm -f wget.log
        popd >/dev/null
        return 1
    else
        printMessageNl "[OK]" 
        cat $filename | tr ',' ' '
        rm -f wget.log
        popd >/dev/null
    fi

    return 0
}

function cctldDailyDiscoveredSupportedTldsForDate()
{
    local feed=$1
    local date=$2
    local baseUrl="http://www.domainwhoisdatabase.com"
    local dirname="$(data_feed_parent_dir $feed)/status"
    local filename="supported_tlds_${date}"

    if downloadSupportedTlds $baseUrl $dirname $filename; then
        return 0
    fi

    return 1
}

function cctldDailyDiscoveredSupportedTlds()
{
    local feed=$1
    local baseUrl="http://www.domainwhoisdatabase.com"
    local dirname="$(data_feed_parent_dir "$feed")/status"
    local filename="supported_tlds"

    if downloadSupportedTlds "$baseUrl" "$dirname" "$filename"; then
        return 0
    fi

    return 1
}

#
# $1: data source 
# $2: date in underscored format.
# returns: 0 if everything is ok, 1 otherwise.
#
# This function will load the file from the following url:
# http://bestwhois.org/domain_name_data/domain_names_whois/status/supported_tlds
# to find the supported top level domains.
#
# This is a short list.
#
function bestWhoisSupportedTlds()
{
    local feed=$1
    local baseUrl="http://bestwhois.org"
    local dirname="$(data_feed_parent_dir "$feed")/status"
    local filename="supported_tlds"

    if downloadSupportedTlds "$baseUrl" "$dirname" "$filename"; then
        return 0
    fi

    return 1
}

#
# $1: feed
# $2: date in underscored format.
# returns: 0 if everything is ok, 1 otherwise.
#
# This function will load the file from the URL
# http://bestwhois.org/ngtlds_domain_name_data/domain_names_whois/status/supported_tlds_YYYY_mm_dd 
# to find the supported top level domains for a given date.
#
# This is the longer list, not just a few domain names.
#
function bestWhoisSupportedTldsForDate()
{
    local feed=$1
    local date=$2
    local baseUrl="http://bestwhois.org"
    local dirname="$(data_feed_parent_dir $feed)/status"
    local filename="supported_tlds_${date}"

    if downloadSupportedTlds $baseUrl $dirname $filename; then
        return 0
    fi

    return 1
}

#
# $1: feed
# $2: date
#
function supportedTldsThird()
{
    local feed=$1
    local date_underscore=$(echo "$2" | tr '-' '_')
    local baseUrl
    local dirname
    local filename

    if [ "$feed" == "ngtlds_domain_names_new" -o \
        "$feed" == "ngtlds_domain_names_dropped" -o \
        "$feed" == "ngtlds_domain_names_dropped_whois" -o \
        "$feed" == "ngtlds_domain_names_whois_archive" -o \
        "$feed" == "ngtlds_domain_names_whois_filtered_reg_country" -o \
        "$feed" == "ngtlds_domain_names_whois_filtered_reg_country_archive" -o \
        "$feed" == "ngtlds_domain_names_whois_filtered_reg_country_noproxy" -o \
        "$feed" == "ngtlds_domain_names_whois_filtered_reg_country_noproxy_archive" -o \
        "$feed" == "ngtlds_domain_names_whois" ]; then
        #
        # ngtlds
        # http://bestwhois.org/ngtlds_domain_name_data/domain_names_whois/
        # status/supported_tlds_$YYYY_mm_dd
        #
        baseUrl="http://bestwhois.org"
        dirname="ngtlds_domain_name_data/domain_names_whois/status"
        filename="supported_tlds_$date_underscore"
    else
        # other 
        # http://bestwhois.org/domain_name_data/domain_names_whois/status/supported_tlds
        baseUrl="http://bestwhois.org"
        dirname="domain_name_data/domain_names_whois/status"
        filename="supported_tlds"
    fi

    if downloadSupportedTlds $baseUrl $dirname $filename; then
        return 0
    fi

    return 1
}

function supportedTldsFourth()
{
    local feed=$1
    local baseUrl="http://bestwhois.org"
    local dirname="$(data_feed_parent_dir $feed)"
    local filename="supported_tlds"

    if downloadSupportedTlds $baseUrl $dirname $filename; then
        return 0
    fi

    return 1
}

#
# e. local files(supported_ngtlds or supported_gtlds(currently you named 
# tlds.cf)).
#
function supportedTldsFromFile()
{
    local feed=$1
    local filename;
    
    if [ "$feed" == "ngtlds_domain_names_new" -o \
        "$feed" == "ngtlds_domain_names_dropped" -o \
        "$feed" == "ngtlds_domain_names_whois_archive" -o \
        "$feed" == "ngtlds_domain_names_whois_filtered_reg_country" -o \
        "$feed" == "ngtlds_domain_names_whois_filtered_reg_country_archive" -o \
        "$feed" == "ngtlds_domain_names_whois_filtered_reg_country_noproxy" -o \
        "$feed" == "ngtlds_domain_names_whois_filtered_reg_country_noproxy_archive" -o \
        "$feed" == "ngtlds_domain_names_dropped_whois" -o \
        "$feed" == "ngtlds_domain_names_whois" ]; then
        filename="$START_DIRECTORY/supported_ngtlds"
    else
        filename="$START_DIRECTORY/supported_gtlds"
    fi

    if [ -f "$filename" ]; then
        cat "$filename" | tr ',' ' '
        return 0
    fi

    printError "File $filename not found."
    return 1
}

#
# $1: feed
#
# The purpose of this is to route the tld file downloader to the right location.
function data_feed_parent_dir() 
{
    local feed="$1"

    if [ "$feed" == "domain_names_new" -o \
         "$feed" == "domain_names_dropped" -o \
         "$feed" == "domain_names_dropped_whois" -o \
         "$feed" == "domain_names_whois" -o \
         "$feed" == "domain_names_whois_filtered_reg_country" -o \
         "$feed" == "domain_names_whois_filtered_reg_country_noproxy" -o \
         "$feed" == "domain_names_whois_archive" -o \
         "$feed" == "domain_names_whois_filtered_reg_country_archive" -o \
         "$feed" == "domain_names_whois_filtered_reg_country_noproxy_archive" -o \
         "$feed" == "whois_record_delta_whois" -o \
         "$feed" == "whois_record_delta_domain_names_change" ]; then 
        echo "domain_name_data/$feed"
    elif [ "$feed" == "ngtlds_domain_names_new" -o \
        "$feed" == "ngtlds_domain_names_dropped" -o \
        "$feed" == "ngtlds_domain_names_dropped_whois" -o \
        "$feed" == "ngtlds_domain_names_whois_filtered_reg_country" -o \
        "$feed" == "ngtlds_domain_names_whois_filtered_reg_country_noproxy" -o \
        "$feed" == "ngtlds_domain_names_whois_filtered_reg_country_archive" -o \
        "$feed" == "ngtlds_domain_names_whois_filtered_reg_country_noproxy_archive" -o \
        "$feed" == "ngtlds_domain_names_whois_archive" -o \
        "$feed" == "ngtlds_domain_names_whois" ]; then
        echo "ngtlds_domain_name_data/${feed#ngtlds_}"
    elif [ "$feed" == "cctld_discovered_domain_names_new" -o \
        "${feed}" == "cctld_discovered_domain_names_whois" ]; then
        echo "domain_list/${feed#cctld_discovered_}"
    elif [ "$feed" == "cctld_registered_domain_names_new" -o \
        "$feed" == "cctld_registered_domain_names_dropped" -o  \
        "$feed" == "cctld_registered_domain_names_dropped_whois" -o  \
        "${feed}" == "cctld_registered_domain_names_whois" ]; then
        echo "cctld_domain_name_data/${feed#cctld_registered_}"
    else
        printError "data_feed_parent_dir(): feed not handled: '$feed'"
        return 1
    fi

    return 0
}

#
# and the above rules don't apply to quarterly tlds: 
# http://www.domainwhoisdatabase.com/whois_database/v13/docs/v13.tlds
#
function domainwhoisdatabaseSupportedTlds()
{
    local baseUrl="http://www.domainwhoisdatabase.com"
    local dirname="whois_database/$DATABASEVERSION/docs"
    local filename="${DATABASEVERSION}.tlds"

    if downloadSupportedTlds "$baseUrl" "$dirname" "$filename"; then
        return 0
    fi

    return 1
}

#
# and the above rules don't apply to quarterly cctlds: 
# http://www.domainwhoisdatabase.com/domain_list_quarterly/v3/docs/v3.tlds
#
function domain_list_quarterly_SupportedTlds()
{
    local baseUrl="http://www.domainwhoisdatabase.com"
    local dirname="domain_list_quarterly/$DATABASEVERSION/docs"
    local filename="${DATABASEVERSION}.tlds"

    if downloadSupportedTlds "$baseUrl" "$dirname" "$filename"; then
        return 0
    fi

    return 1
}


#
# 1: data source
# 2: date
#
# This is the main function that should always find what tlds are supported for
# a given data source and date. Calls specific functions for various data
# sources.
#
function allTlds()
{
    local feed=$1
    local date=$2
    local date_underscore=$(echo $date | tr '-' '_')
   
    #
    # The --tld-file will overwrite everything.
    #
    if [ "$TLD_FILE" ]; then
        cat "$TLD_FILE" | tr ',' ' '
        return 0
    fi

    #
    # This one has no tlds.
    #
    if [ "$feed" == "whois_database_combined" ]; then
        return 0
    fi

    # and the above rules don't apply to quarterly tlds: 
    # http://www.domainwhoisdatabase.com/whois_database/v13/docs/v13.tlds
    if [ "$feed" == "whois_database" ]; then
        if ! domainwhoisdatabaseSupportedTlds; then
            printDebug "domainwhoisdatabaseSupportedTlds FAILED"
            return 0
        else 
            printDebug "domainwhoisdatabaseSupportedTlds OK"
        fi

        # This data source is an exception, we go no further.
        return 1
    fi

    # and the above rules don't apply to quarterly cctlds: 
    # http://www.domainwhoisdatabase.com/domain_list_quarterly/v3/docs/v3.tlds
    if [ "$feed" == "domain_list_quarterly" ]; then
        if ! domain_list_quarterly_SupportedTlds; then
            printDebug "domain_list_quarterly_SupportedTlds FAILED"
            return 0
        else 
            printDebug "domain_list_quarterly_SupportedTlds OK"
        fi

        # This data source is an exception, we go no further.
        return 1
    fi

    # If feed is daily cctld domain names new, it is located in different area.
    # The following order(use the first valid one)
    #       1) http://domainwhoisdatabase.com/domain_list/domain_names_new/status/supported_tlds_${YYYY_mm_dd}
    #       2) http://domainwhoisdatabase.com/domain_list/domain_names_new/status/supported_tlds
    #       3) http://domainwhoisdatabase.com/domain_list/domain_names_whois/status/supported_tlds_${YYYY_mm_dd}
    #       4) http://domainwhoisdatabase.com/domain_list/domain_names_whois/status/supported_tlds

    # If feed is daily cctld domain names whois look at :
    #       1) http://domainwhoisdatabase.com/domain_list/domain_names_whois/status/supported_tlds_${YYYY_mm_dd}
    #       2) http://domainwhoisdatabase.com/domain_list/domain_names_whois/status/supported_tlds
    if [ "${feed}" == "cctld_discovered_domain_names_new" ]; then
        if ! cctldDailyDiscoveredSupportedTldsForDate "${feed}" "${date_underscore}"; then
            printDebug "cctldDailyDiscoveredSupportedTldsForDate FAILED"

            if ! cctldDailyDiscoveredSupportedTlds "${feed}"; then
                printDebug "cctldDailyDiscoveredSupportedTlds FAILED"
            else
                printDebug "cctldDailyDiscoveredSupportedTlds OK"
                return 0
            fi

            # This data is explicitly for cctld daily only
            return 1
        else
            printDebug "cctldDailyDiscoveredSupportedTldsForDate OK"
            return 0
        fi
    fi

    if [ "${feed}" == "cctld_discovered_domain_names_new" -o "${feed}" == "cctld_discovered_domain_names_whois" ]; then
        if ! cctldDailyDiscoveredSupportedTldsForDate "cctld_discovered_domain_names_whois" "${date_underscore}"; then
            printDebug "cctldDailyDiscoveredSupportedTldsForDate FAILED"

            if ! cctldDailyDiscoveredSupportedTlds "cctld_discovered_domain_names_whois"; then
                printDebug "cctldDailyDiscoveredSupportedTlds FAILED"
            else
                printDebug "cctldDailyDiscoveredSupportedTlds OK"
                return 0
            fi

            # This data is explicitly for cctld daily only
            return 1
        else
            printDebug "cctldDailyDiscoveredSupportedTldsForDate OK"
            return 0
        fi
    fi



    # 1. for getting tlds of each data feed, please first check the tld file in
    # the following order(use the first valid one)
    # a. $data_feed_parent_dir/status/supported_tlds_$YYYY_mm_dd
    if ! bestWhoisSupportedTldsForDate "$feed" "$date_underscore"; then
        printDebug "bestWhoisSupportedTldsForDate FAILED"
    else
        printDebug "bestWhoisSupportedTldsForDate OK"
        return 0
    fi

    # b. $data_feed_parent_dir/status/supported_tlds
    if ! bestWhoisSupportedTlds "$feed"; then
        printDebug "bestWhoisSupportedTlds FAILED"
    else
        printDebug "bestWhoisSupportedTlds OK"
        return 0
    fi

    # c. for ngtlds related data feeds, use 
    # http://bestwhois.org/ngtlds_domain_name_data/domain_names_whois/
    # status/supported_tlds_$YYYY_mm_dd
    #
    # for other data feeds use 
    # http://bestwhois.org/domain_name_data/domain_names_whois/
    # status/supported_tlds
    #
    if ! supportedTldsThird "$feed" "$date_underscore"; then
        printDebug "supportedTldsThird     FAILED"
    else
        printDebug "supportedTldsThird     OK"
        return 0
    fi

    # d. $data_feed_parent_dir/supported_tlds
    if ! supportedTldsFourth "$feed" "$date_underscore"; then
        printDebug "supportedTldsFourth    FAILED"
    else
        printDebug "supportedTldsFourth    OK"
        return 0
    fi
   
    # e. local files (supported_ngtlds or supported_gtlds).
    if ! supportedTldsFromFile "$feed" "$date_underscore"; then
        printDebug "supportedTldsFromFile  FAILED"
    else
        printDebug "supportedTldsFromFile  OK"
        return 0
    fi
    
}

#
# This function is to find the list of all the supported data sources. 
#
function allFeeds()
{
    echo \
        "domain_names_new \
        domain_names_dropped \
        domain_names_dropped_whois \
        domain_names_whois \
        domain_names_whois_filtered_reg_country \
        domain_names_whois_filtered_reg_country_noproxy \
        domain_names_whois_archive \
        domain_names_whois_filtered_reg_country_archive \
        domain_names_whois_filtered_reg_country_noproxy_archive \
        ngtlds_domain_names_new \
        ngtlds_domain_names_dropped \
        ngtlds_domain_names_dropped_whois \
        ngtlds_domain_names_whois \
        cctld_discovered_domain_names_new \
        cctld_discovered_domain_names_whois \
        whois_record_delta_whois \
        whois_record_delta_domain_names_change \
        whois_database \
        domain_list_quarterly"
}

#
# 1: data source 
# 2: tld
# 3: date 
#
# This function will compose the file path of the data file with the given
# properties using the directory structure specification found here:
#
# http://bestwhois.org/domain_name_data/domain_names_whois/README
#
function filePath()
{
    local feed=$1
    local tld=$2
    local date=$3
    local date_underscore=$(echo $date | tr '-' '_')


    if [ "$feed" == "domain_names_new" ]; then
        echo "domain_name_data/$feed/$tld/$date/add.$tld.csv"
    elif [ "$feed" == "domain_names_dropped" ]; then
        echo "domain_name_data/$feed/$tld/$date/dropped.$tld.csv"
    elif [ "$feed" == "domain_names_dropped_whois" ]; then
        #
        # This one supports various file formats, some others not.
        #
        if [ "$FILEFORMAT" = "regular" -o "$FILEFORMAT" = "regular_csv" ]; then
            echo "domain_name_data/$feed/${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "full" -o "$FILEFORMAT" = "full_o" ]; then
            echo "domain_name_data/$feed/full_${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "sql" -o "$FILEFORMAT" = "mysqldump" ]; then
            echo "domain_name_data/$feed/dropped_mysqldump_${date_underscore}/${tld}/dropped_mysqldump_${date_underscore}_${tld}.sql.gz"
        fi
    elif [ "$feed" == "domain_names_whois" ]; then 
        #
        # This one supports various file formats, some others not.
        #
        if [ "$FILEFORMAT" = "regular" -o "$FILEFORMAT" = "regular_csv" ]; then
            echo "domain_name_data/$feed/${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "full" -o "$FILEFORMAT" = "full_o" ]; then
            echo "domain_name_data/$feed/full_${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "sql" -o "$FILEFORMAT" = "mysqldump" ]; then
            echo "domain_name_data/$feed/add_mysqldump_${date_underscore}/${tld}/add_mysqldump_${date_underscore}_${tld}.sql.gz"
        fi
    elif [ "$feed" == "domain_names_whois_filtered_reg_country" ]; then
        echo "domain_name_data/$feed/filtered_reg_country_${date_underscore}_${tld}.tar.gz"
    elif [ "$feed" == "domain_names_whois_filtered_reg_country_noproxy" ]; then
        echo "domain_name_data/$feed/filtered_reg_country_noproxy_${date_underscore}_${tld}.tar.gz"
    elif [ "$feed" == "domain_names_whois_archive" ]; then
        if [ "$FILEFORMAT" = "regular" -o "$FILEFORMAT" = "regular_csv" ]; then
            echo "domain_name_data/$feed/${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "full" -o "$FILEFORMAT" = "full_csv" ]; then
            echo "domain_name_data/$feed/full_${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "sql" -o "$FILEFORMAT" = "mysqldump" ]; then
            echo "domain_name_data/$feed/add_mysqldump_${date_underscore}.tar.gz"
        fi
    elif [ "$feed" == "domain_names_whois_filtered_reg_country_archive" ]; then
        echo "domain_name_data/$feed/filtered_reg_country_${date_underscore}_${tld}.tar.gz"
    elif [ "$feed" == "domain_names_whois_filtered_reg_country_noproxy_archive" ]; then
        echo "domain_name_data/$feed/filtered_reg_country_noproxy_${date_underscore}_${tld}.tar.gz"
    elif [ "$feed" == "whois_record_delta_whois" ]; then
        #
        # Again, various formats.
        #
        if [ "$FILEFORMAT" = "regular" -o "$FILEFORMAT" = "regular_csv" ]; then
            echo "domain_name_data/$feed/${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "full" -o "$FILEFORMAT" = "full_csv" ]; then
            echo "domain_name_data/$feed/full_${date_underscore}_${tld}.csv.gz"
        fi
    elif [ "$feed" == "whois_record_delta_domain_names_change" ]; then
        echo "$feed/$tld/${date_underscore}/${tld}.csv"
    elif [ "$feed" == "ngtlds_domain_names_new" ]; then
        echo "ngtlds_domain_name_data/domain_names_new/${tld}/${date}/add.${tld}.csv"
    elif [ "$feed" == "ngtlds_domain_names_dropped" ]; then
        echo "ngtlds_domain_name_data/domain_names_dropped/${tld}/${date}/dropped.${tld}.csv"
    elif [ "$feed" == "ngtlds_domain_names_dropped_whois" ]; then
        if [ "$FILEFORMAT" = "regular" -o "$FILEFORMAT" = "regular_csv" ]; then
            echo "ngtlds_domain_name_data/domain_names_dropped_whois/${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "full" -o "$FILEFORMAT" = "full_csv" ]; then
            echo "ngtlds_domain_name_data/domain_names_dropped_whois/full_${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "sql" -o "$FILEFORMAT" = "mysqldump" ]; then
            echo "ngtlds_domain_name_data/domain_names_dropped_whois/dropped_mysqldump_${date_underscore}/${tld}/dropped_mysqldump_${date_underscore}_${tld}.sql.gz"
        fi 

    elif [ "$feed" == "ngtlds_domain_names_whois" ]; then
        if [ "$FILEFORMAT" = "regular" -o "$FILEFORMAT" = "regular_csv" ]; then
            echo "ngtlds_domain_name_data/domain_names_whois/${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "full" -o "$FILEFORMAT" = "full_csv" ]; then
            echo "ngtlds_domain_name_data/domain_names_whois/full_${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "sql" -o "$FILEFORMAT" = "mysqldump" ]; then
            echo "ngtlds_domain_name_data/domain_names_whois/add_mysqldump_${date_underscore}/${tld}/add_mysqldump_${date_underscore}_${tld}.sql.gz"
        fi 
    elif [ "$feed" == "ngtlds_domain_names_whois_filtered_reg_country" ]; then
        echo "$(data_feed_parent_dir ${feed})/filtered_reg_country_${date_underscore}_${tld}.tar.gz"
    elif [ "$feed" == "ngtlds_domain_names_whois_filtered_reg_country_noproxy" ]; then
        echo "$(data_feed_parent_dir ${feed})/filtered_reg_country_noproxy_${date_underscore}_${tld}.tar.gz"

    elif [ "$feed" == "ngtlds_domain_names_whois_archive" ]; then
        if [ "$FILEFORMAT" = "regular" -o "$FILEFORMAT" = "regular_csv" ]; then
            echo "ngtlds_domain_name_data/domain_names_whois_archive/${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "full" -o "$FILEFORMAT" = "full_csv" ]; then
            echo "ngtlds_domain_name_data/domain_names_whois_archive/full_${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "sql" -o "$FILEFORMAT" = "mysqldump" ]; then
            echo "ngtlds_domain_name_data/domain_names_whois_archive/add_mysqldump_${date_underscore}.tar.gz"
        fi
    elif [ "$feed" == "ngtlds_domain_names_whois_filtered_reg_country_archive" ]; then
        echo "$(data_feed_parent_dir ${feed})/filtered_reg_country_${date_underscore}_${tld}.tar.gz"
    elif [ "$feed" == "ngtlds_domain_names_whois_filtered_reg_country_noproxy_archive" ]; then
        echo "$(data_feed_parent_dir ${feed})/filtered_reg_country_noproxy_${date_underscore}_${tld}.tar.gz"


    elif [ "$feed" == "cctld_discovered_domain_names_new" ]; then
        echo "domain_list/domain_names_new/$date/$tld"
    elif [ "$feed" == "cctld_discovered_domain_names_whois" ]; then
        if [ "$FILEFORMAT" = "regular" -o "$FILEFORMAT" = "regular_csv" ]; then
            echo "domain_list/domain_names_whois/${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "full" -o "$FILEFORMAT" = "full_csv" ]; then
            echo "domain_list/domain_names_whois/full_${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "sql" -o "$FILEFORMAT" = "mysqldump" ]; then
            echo "domain_list/domain_names_whois/add_mysqldump_${date_underscore}/${tld}/add_mysqldump_${date_underscore}_${tld}.sql.gz"
        fi 

    elif [ "$feed" == "cctld_registered_domain_names_new" ]; then
        echo "cctld_domain_name_data/domain_names_new/$date/add.$tld.csv"
    elif [ "$feed" == "cctld_registered_domain_names_whois" ]; then
        if [ "$FILEFORMAT" = "regular" -o "$FILEFORMAT" = "regular_csv" ]; then
            echo "cctld_domain_name_data/domain_names_whois/${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "full" -o "$FILEFORMAT" = "full_csv" ]; then
            echo "cctld_domain_name_data/domain_names_whois/full_${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "sql" -o "$FILEFORMAT" = "mysqldump" ]; then
            echo "cctld_domain_name_data/domain_names_whois/add_mysqldump_${date_underscore}_${tld}.sql.gz"
        fi 
    elif [ "$feed" == "cctld_registered_domain_names_dropped" ]; then
        echo "cctld_domain_name_data/domain_names_dropped/$date/dropped.$tld.csv"
    elif [ "$feed" == "cctld_registered_domain_names_dropped_whois" ]; then
        if [ "$FILEFORMAT" = "regular" -o "$FILEFORMAT" = "regular_csv" ]; then
            echo "cctld_domain_name_data/domain_names_dropped_whois/${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "full" -o "$FILEFORMAT" = "full_csv" ]; then
            echo "cctld_domain_name_data/domain_names_dropped_whois/full_${date_underscore}_${tld}.csv.gz"
        elif [ "$FILEFORMAT" = "sql" -o "$FILEFORMAT" = "mysqldump" ]; then
            echo "cctld_domain_name_data/domain_names_whois/dropped_mysqldump_${date_underscore}_${tld}.sql.gz"
        fi 

    #
    # From this point the datasources are at http://www.domainwhoisdatabase.com
    #
    elif [ "$feed" == "whois_database" ]; then
        if [ "$FILEFORMAT" = "regular" -o "$FILEFORMAT" = "regular_csv" ]; then
            echo "$feed/$DATABASEVERSION/csv/tlds/regular/csvs.${tld}.regular.tar.gz"
        elif [ "$FILEFORMAT" = "full" -o "$FILEFORMAT" = "full_csv" ]; then
            echo "$feed/$DATABASEVERSION/csv/tlds/full/csvs.${tld}.full.tar.gz"
        elif [ "$FILEFORMAT" = "simple" -o "$FILEFORMAT" = "simple_csv" ]; then
            echo "$feed/$DATABASEVERSION/csv/tlds/simple/csvs.${tld}.simple.tar.gz"
        elif [ "$FILEFORMAT" = "sql" -o "$FILEFORMAT" = "mysqldump" ]; then
            echo "$feed/$DATABASEVERSION/database_dump/mysqldump/${tld}/whoiscrawler_${DATABASEVERSION}_${tld}_mysql.sql.gz"
        fi
    elif [ "$feed" == "whois_database_combined" ]; then
        if [ "$FILEFORMAT" = "regular" -o "$FILEFORMAT" = "regular_csv" ]; then
            echo "whois_database/${DATABASEVERSION}/csv/tlds_combined"
        elif [ "$FILEFORMAT" = "full" -o "$FILEFORMAT" = "full_csv" ]; then
            echo "whois_database/${DATABASEVERSION}/csv/tlds_combined"
        elif [ "$FILEFORMAT" = "simple" -o "$FILEFORMAT" = "simple_csv" ]; then
            echo "whois_database/${DATABASEVERSION}/csv/tlds_combined"
        elif [ "$FILEFORMAT" = "sql" -o "$FILEFORMAT" = "mysqldump" ]; then
            echo "whois_database/${DATABASEVERSION}/database_dump/mysqldump_combined"
        fi
    elif [ "$feed" == "domain_list_quarterly" ]; then
        if [ "$FILEFORMAT" = "regular" -o "$FILEFORMAT" = "regular_csv" ]; then
            echo "$feed/$DATABASEVERSION/csv/tlds/regular/csvs.${tld}.regular.tar.gz"
        elif [ "$FILEFORMAT" = "full" -o "$FILEFORMAT" = "full_csv" ]; then
            echo "$feed/$DATABASEVERSION/csv/tlds/full/csvs.${tld}.full.tar.gz"
        elif [ "$FILEFORMAT" = "simple" -o "$FILEFORMAT" = "simple_csv" ]; then
            echo "$feed/$DATABASEVERSION/csv/tlds/simple/csvs.${tld}.simple.tar.gz"
        elif [ "$FILEFORMAT" = "sql" -o "$FILEFORMAT" = "mysqldump" ]; then
            echo "$feed/$DATABASEVERSION/database_dump/mysqldump/${tld}/domains_whoiscrawler_${DATABASEVERSION}_${tld}_mysql.sql.gz"
        fi
    else
        echo "Unsupported feed: '$feed'" >&2
        exit 1
    fi
}

#
# 1: data source
#
# This function will find the base url for a given data source.
#
function baseUrl()
{
    local feed=$1
    
    if [ "$feed" == "whois_database" -o "$feed" == "domain_list_quarterly" ]; then
        echo "http://www.domainwhoisdatabase.com"
    elif [ "$feed" == "whois_database_combined" ]; then
        # http://www.domainwhoisdatabase.com/whois_database/v14/database_dump/
        echo "http://www.domainwhoisdatabase.com"
    elif [ "$feed" == "cctld_discovered_domain_names_new" -o \
        "${feed}" == "cctld_discovered_domain_names_whois" ]; then
        echo "http://www.domainwhoisdatabase.com"
    else
        echo "http://bestwhois.org"
    fi
}

#
# $1: the base url
#
# Low level downloader function. Perhaps we should use this everywhere in this
# script.
#
function downloadWithWget()
{
    local baseUrl="$1"
    local dirname="$2"
    local filename="$3"
    local retcode=0

    # Notifying the user. Full url is more informative but a bit long...
    if [ "$DEBUG" == "yes" ]; then
        echo -n "$baseUrl/$dirname/$filename  "
    else
        echo -n "$dirname/$filename  "
    fi

    if [ -e "$dirname/$filename" ]; then
        echo "[FILE EXISTS]"
        return 0
    fi
    
    mkdir -p $dirname

    #
    # Dry run means we are not actually downloading the data files. Good for 
    # testing.
    #
    if [ "$DRY_RUN" == "yes" ]; then
        touch "$dirname/$filename"
        echo "[DRY RUN]"
        return 0
    fi

    pushd $dirname >/dev/null
    wget \
        --user="$(login_name $baseUrl)" \
        --password="$(login_password $baseUrl)" \
        "$baseUrl/$dirname/$filename" 2>wget.log >wget.log

    retcode=$?

    if [ $retcode -gt 128 ]; then
        echo "[ABORTED]"
        echo "Signal received, aborting script."
        exit $retcode
    fi

    if grep --quiet "404 Not Found" wget.log; then
        echo "[NOT FOUND]"
        retcode=1
    elif grep --quiet "Password Authentication Failed" wget.log; then
        echo "[AUTH FAILED]"
        retcode=2
    elif grep --quiet "403 Forbidden" wget.log; then
        echo "[NONEXISTENT OR UNAVAILABLE RESOURCE]"
        retcode=3	
    else
        echo "[OK]"
        retcode=0
    fi
    
    rm wget.log
    popd >/dev/null

    return $retcode
}

#
# 1: data source 
#
# This is the function that is called when downloading aggregated data sources
# that are in multi part targz files.
#
function downloadMultiFile()
{
    local url=$(baseUrl "$feed")
    local dir=$(filePath "$feed" "$tld" "$date")
    local fileName
    local n=0

    #if not dry run, load until the next file is found, otherwise go till DRY_RUN_MULTIFILE_LIMIT
    while [ "$DRY_RUN" = "no" -o  \( $n -lt "$DRY_RUN_MULTIFILE_LIMIT" \) ]; do
        if [ "$FILEFORMAT" = "regular" -o "$FILEFORMAT" = "regular_csv" ]; then
            fileName=$(printf "regular-%s.tar.gz.%04d" ${DATABASEVERSION} $n)
        elif [ "$FILEFORMAT" = "full" -o "$FILEFORMAT" = "full_csv" ]; then
            fileName=$(printf "full-%s.tar.gz.%04d" ${DATABASEVERSION} $n)
        elif [ "$FILEFORMAT" = "simple" -o "$FILEFORMAT" = "simple_csv" ]; then
            fileName=$(printf "simple-%s.tar.gz.%04d" ${DATABASEVERSION} $n)
        elif [ "$FILEFORMAT" = "sql" -o "$FILEFORMAT" = "mysqldump" ]; then
            fileName=$(printf "mysqldump-%s.tar.gz.%04d" ${DATABASEVERSION} $n)
        else
            echo "whois_database_combined cannot have a file-format of 'all'"
            echo "Please specify either regular, full, simple, or sql"
            exit 1
            break
        fi

        downloadWithWget "$url" "$dir" "${fileName}" 
        if [ $? -ne 0 ]; then
            break;
        fi
        
        downloadWithWget "$url" "$dir" "${fileName}.md5" 
        downloadWithWget "$url" "$dir" "${fileName}.sha256" 

        n=$((n+1))
    done
}


#
# Downloads legacy data for whois_database v1 and v2
#
function downloadLegacyQuarterlyFile()
{
    local url=$(baseUrl "$feed")
    if [ "$FILEFORMAT" == "sql" -o "${FILEFORMAT}" == "mysqldump" ]; then
        local dir="$feed/$DATABASEVERSION/database_dump"

        # Download contacts
        fileName="contact_mysql.sql.gz"
        downloadWithWget "$url" "$dir" "${fileName}"

        # Downlaod registry
        fileName="registry_data_mysql.sql.gz"
        downloadWithWget "$url" "$dir" "${fileName}"

        # Download whois record mysql
        fileName="whois_record_mysql.sql.gz"
        downloadWithWget "$url" "$dir" "${fileName}"

        # Download whois sql and mssql based on version
        if [ "${DATABASEVERSION}" == "v1" ]; then
            fileName="whois.sql.gz"
            downloadWithWget "$url" "$dir" "${fileName}"
            downloadWithWget "$url" "$dir" "${fileName}.md5"

            fileName="whois_mssql.sql.gz"
            downloadWithWget "$url" "$dir" "${fileName}"
            downloadWithWget "$url" "$dir" "${fileName}.md5"
        else
            fileName="whois2.sql.gz"
            downloadWithWget "$url" "$dir" "${fileName}"
            downloadWithWget "$url" "$dir" "${fileName}.md5"

            fileName="whois2_mssql.sql.gz"
            downloadWithWget "$url" "$dir" "${fileName}"
            downloadWithWget "$url" "$dir" "${fileName}.md5"
        fi
        
    elif [ "$FILEFORMAT" == "simple" -o "${FILEFORMAT}" == "simple_csv" ]; then
        if [ "${DATABASEVERSION}" == "v1" ]; then
            return
        fi

        local dir="${feed}/${DATABASEVERSION}/csv"
        fileName="whois_v2_db_export_data_csv_simple.tar.gz"
        downloadWithWget "$url" "$dir" "${fileName}"
    else
        echo "v1 contains only 'sql'"
        echo "v2 contains 'simple_csv' and 'sql'"
        return
    fi

    

}

#
# 1: data source 
# 2: tld
# 3: date 
#
# The main function to download one file, a file for a given feed, tld and
# date. A proper message will also be printed about the result.
#
function downloadOneFile()
{
    local feed=$1
    local tld=$2
    local date=$3

    local file=$(filePath "$feed" "$tld" "$date")

    if [ -z "${file}" ]; then
        return
    fi
    local filename=$(basename $file)
    local dirname=$(dirname $file)
    local url=$(baseUrl "$feed")
    local fullurl=$url/$file

    printDebug "*** file      : $file"

    #
    # If filename is empty the given combination does not exist. This should of
    # course never happen.
    #
    if [ -z "$filename" ]; then
        return 0
    fi

    # Notifying the user. Full url is more informative but a bit long...
    if [ "$DEBUG" == "yes" ]; then
        echo -n "$fullurl  "
    else
        echo -n "$dirname/$filename  "
    fi

    if [ -e "$file" ]; then
        echo "[FILE EXISTS]"
        return 0
    fi

    mkdir -p $dirname

    #
    # Dry run means we are not actually downloading the data files. Good for 
    # testing.
    #
    if [ "$DRY_RUN" == "yes" ]; then
        touch "$dirname/$filename"
        echo "[DRY RUN]"
        return 0
    fi

    pushd $dirname >/dev/null

    wget \
        --user="$(login_name $url)" \
        --password="$(login_password $url)" \
        $fullurl 2>wget.log >wget.log

    if grep --quiet "404 Not Found" wget.log; then
        echo "[NOT FOUND]"
    elif grep --quiet "Password Authentication Failed" wget.log; then
        echo "[AUTH FAILED]"
    elif grep --quiet "403 Forbidden" wget.log; then
        echo "[NONEXISTENT OR UNAVAILABLE RESOURCE]"
    else
        echo "[OK]"
    fi

    rm wget.log

    popd >/dev/null
}

#
# 1: data source 
# 2: tld
# 3: date (tbd)
#
# Downloads the files for all the tlds (tld is specified in the command line or
# using a downloaded tld list).
#
function downloadForTld()
{
    local feed=$1
    local tld=$2
    local date=$3

    if [ "$feed" == "whois_database_combined" ]; then
        downloadMultiFile "$feed" 
        return $?
    fi

    if [ "$feed" == "whois_database" ]; then
        if [ "${DATABASEVERSION}" == "v1" -o "${DATABASEVERSION}" == "v2" ]; then
            downloadLegacyQuarterlyFile "$feed"
            return $?
        fi
    fi

    #
    # If no tld is provided all the tld-s are going to be downloaded.
    #
    if [ -z "$tld" ]; then
        tld="$(allTlds "$feed" "$date")"
    fi

    # Feeds with file formats
    # domain_names_dropped_whois
    # domain_names_whois
    # domain_names_whois_archive
    # whois_record_delta_whois
    # ngtlds_domain_names_dropped_whois
    # ngtlds_domain_name_whois
    # ngtlds_domain_name_whois_archive
    # whois_database
    # domain_list_quarterly
    if [ "${FILEFORMAT}" == "all" ] && \
       [    "${feed}" == "domain_names_dropped_whois" -o \
            "${feed}" == "domain_names_whois" -o \
            "${feed}" == "domain_names_whois_archive" -o \
            "${feed}" == "whois_record_delta_whois" -o \
            "${feed}" == "ngtlds_domain_names_dropped_whois" -o \
            "${feed}" == "ngtlds_domain_names_whois" -o \
            "${feed}" == "ngtlds_domain_names_whois_archive" -o \
            "${feed}" == "cctld_discovered_domain_names_whois" -o \
            "${feed}" == "cctld_registered_domain_names_whois" -o \
            "${feed}" == "cctld_registered_domain_names_dropped_whois" -o \
            "${feed}" == "whois_database" -o \
            "${feed}" == "domain_list_quarterly" ]; then
        for oneTld in $tld; do
            FILEFORMAT="simple"
            downloadOneFile "$feed" "$oneTld" "$date"

            FILEFORMAT="regular"
            downloadOneFile "$feed" "$oneTld" "$date"

            FILEFORMAT="full"
            downloadOneFile "$feed" "$oneTld" "$date"
            
            FILEFORMAT="sql"
            downloadOneFile "$feed" "$oneTld" "$date"

            FILEFORMAT="all"
        done

    else
        for oneTld in $tld; do
            downloadOneFile "$feed" "$oneTld" "$date"
        done
    fi
}

#
# 1: data source
# 2: tld
# 3: date 
#
# This function is to download all the files for the feed by calling the
# function that downloads the files for all the tlds.
#
function downloadForFeed()
{
    local feed=$1
    local tld=$2
    local date=$3

    #
    # If no feeds are provided we have to load all possible feeds.
    #
    if [ -z "$feed" ]; then 
        feed=$(allFeeds)
    fi

    for oneFeed in $feed; do
        if [ "${oneFeed}" == "whois_database" -o "${oneFeed}" == "domain_list_quarterly" \
            -o "${oneFeed}" == "whois_database_combined" ]; then
            downloadForTld "$oneFeed" "$tld" "$date"
        else
            local check_feed=$(data_feed_parent_dir "${oneFeed}")
            if [ "${check_feed}" != "" ]; then
                downloadForTld "$oneFeed" "$tld" "$date"
            fi
        fi
    done

}

#
# Processes the date part of the arguments and calls other functions to do the
# job.
#
function downloadForDate()
{
    local feed=$1
    local tld=$2
    local date=$3

    if [ -z "$NDAYS" ]; then
        if [ -z "$date" ]; then
            downloadForFeed "$feed" "$tld" "$oneDate"
        else
            for oneDate in $date; do
                downloadForFeed "$feed" "$tld" "$oneDate"
            done
        fi
    else
        ndays=$((NDAYS))

        if [ "$ndays" -lt 1 ]; then
            echo "Invalid number of days." >&2
            exit 1
        fi

        printVerbose "Downloading data for $ndays days."

        for (( day=0; day<ndays; day++ ))
        do
            thisDate=$(date -d "${DATE}+${day} days" "+%Y-%m-%d")
            downloadForFeed "$feed" "$tld" "$thisDate"
        done

        exit 1
    fi
}

#
# This function is called when the --print-feeds command line option is provided
# by the user. It simply prints all the data feeds.
#
function print_feeds
{
    local feeds=$(allFeeds)
    local feed

    for feed in $feeds; do
        printf "%s\n" $feed
    done
}

#
# This function is called when the --print-urls command line option is provided
# by the user. This is partly for debugging.
#
function print_urls()
{
    local feeds=$(allFeeds)
    local feed
    local url
    local parent_dir

    for feed in $feeds; do
        url=$(baseUrl $feed)
        tld="TLD"
        date="DATE"
        file=$(filePath "$feed" "$tld" "$date")

        printf "%-56s %s/%s\n" $feed $url $file
    done
}


###############################################################################
# If a special job is requested we do that and then exit.
#
if [ "$PRINT_FEEDS" ]; then
    print_feeds
    exit 0
fi

if [ "$PRINT_FORMATS" ]; then
    echo "regular_csv"
    echo "simple_csv"
    echo "full_csv"
    echo "mysqldump"
    echo "all"
    exit 0
fi

if [ "$PRINT_URLS" ]; then
    print_urls
    exit 0
fi

###############################################################################
# Doing the job...
#

# 
# Doing some checks.
#
if [ "$FILEFORMAT" != "regular" -a "$FILEFORMAT" != "regular_csv" -a \
     "$FILEFORMAT" != "full" -a "$FILEFORMAT" != "full_csv" -a \
     "$FILEFORMAT" != "simple" -a "$FILEFORMAT" != "simple_csv" -a \
     "$FILEFORMAT" != "all" -a \
     "$FILEFORMAT" != "sql" -a "$FILEFORMAT" != "mysqldump" ]; then
    echo "Unsupported file format." >&2
    echo "Supported file formats are 'regular', 'simple', 'full', 'sql', and 'all'." >&2
    echo "" >&2

    exit 1
fi

#
# Checking if the date command line option is set. There is one feed that
# contains no date though.
#
if [ -z "$FEEDS" ]; then
    #
    # The "all feeds" needs a date.
    #
    if [ -z "$DATE" ]; then
        printDateMissingAndExit
    fi
else
    #
    # All the feeds except this one needs to have a date.
    #
    for oneFeed in $feed; do
        if [ "$feed" != "whois_database" -a "$feed" != "whois_database_combined" -a "$feed" != "domain_list_quarterly" ]; then
            if [ -z "$DATE" ]; then
                printDateMissingAndExit
            fi
        fi
    done
fi

#
# If we have an output dir we create it and jump there.
#
if [ "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR" 

    if ! [ -d "$OUTPUT_DIR" ]; then
        echo "Could not create output directory." >&2
        echo "Giving up." >&2
        echo "" >&2
    fi

    pushd "$OUTPUT_DIR" >/dev/null
fi

#
# Downloading the files into the current directory (that is the output directory
# if one has been specified)
#
downloadForDate "$FEEDS" "$TLD" "$DATE"

#
# well, this is not important, we will exit anyway.
#
if [ "$OUTPUT_DIR" ]; then
    popd >/dev/null
fi

exit 0
