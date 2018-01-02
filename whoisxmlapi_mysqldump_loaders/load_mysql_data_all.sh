#!/bin/bash
#
#Sample script to load ASCII mysql dumps for a tld
#This loads schema+data from a single backup file
#Recommended for smaller tlds.
#Copyright (c) 2010-2017 Whois API LLC,  http://www.whoisxmlapi.com
#
#Note: IF YOU ARE READING THIS SCRIPT JUST TO COLLECT IDEAS FOR YOUR OWN LOADER,
#      VISIT THE END OF THE FILE WHERE THE REAL WORK IS DONE
#
# Global variables.
#
LANG=C
LC_ALL=C
VERSION="0.0.3"
VERBOSE="yes"
DEBUG="no"
SHOWPROGRESS="no"
MYNAME=$(basename $0)
CATCOMMAND="cat"

#No mysql stuff by default. This is set by mandatory args.
unset MYSQL_USER
unset MYSQL_PASSWORD
unset MYSQL_DATABASE

#Importing generic utilities

source load_mysql_utils.sh

function printHelpAndExit()
{
    echo "Usage: $MYNAME [OPTION]..."
    echo "$MYNAME -- loads data for a given tld"
    echo "from a schema file and separate table files "
    echo " into a table in a mysql database."
    echo ""
echo " -h, --help                  Print this help and exit."
echo " -v, --version               Print version information and exit."
echo " --verbose                   Print more messages."
echo " --show-progress             Display progress bars when loading data from dumps."
echo "                             Recommended, especially for large domains."
echo " --mysql-user=USERNAME       User name to login to the mysql database (optional)."
echo " --mysql-password=PASSWORD   Password to login to the data source (optional)."
echo " --mysql-database=DATABASE   The name of the mysql database to load data into. "
echo "                             This database is created by the script, so should not exist"
echo " --dump-file=DUMPFILE        The file to be loaded. If this is provided,"
echo "                                 the rest of the options are invalid"
echo " --tld=TLD                    load data for this tld"
echo " --dump-files-dir=DIRECTORY   The dump files for the tld-s are in this directory. Only for --tld"
echo " --db-version=STRING          The version to load download. Required for --tld Format: vNN, e.g. v19"
echo ""
    echo "Examples:"
    echo ""
    echo "  -loading sample data downloaded into a directory mysqldump_sample from "
    echo "          http://domainwhoisdatabase.com/whois_database/sample/gtlds/v20/mysqldump_sample/aaa"
    echo ""
    echo "$MYNAME --mysql-database=sample_db_aaa --mysql-user=whoisuser --mysql-password=whoispassword --dump-files-dir=mysqldump_sample --db-version=v20 --tld=aaa --verbose --show-progress"
    echo ""
    echo "      or the same task specifying the file name and path directly:"
    echo ""
    echo "$MYNAME --mysql-database=sample_db_aaa --mysql-user=whoisuser --mysql-password=whoispassword --dump-file=mysqldump_sample/aaa/whoiscrawler_v20_aaa_mysql.sql.gz --verbose --show-progress"
    echo ""
    echo ""
    echo "   -loading production data quietly, downloaded into a directory database_dump/mysqldump/aaa from"
    echo "          http://www.domainwhoisdatabase.com/whois_database/v20/database_dump/mysqldump/aaa"
    echo ""
    echo "$MYNAME --mysql-database=production_db_aaa --mysql-user=whoisuser --mysql-password=whoispassword --dump-files-dir=database_dump/mysqldump --tld=aaa --db-version=v20"
    echo ""
    echo "      or the same task verbosely, specifying the file name and path directly:"
    echo ""
    echo "$MYNAME  --mysql-database=production_db_aaa --mysql-user=whoisuser --mysql-password=whoispassword --dump-file=database_dump/mysqldump/aaa/whoiscrawler_v20_aaa_mysql.sql.gz --verbose --show-progress"

    exit 1
}

ARGS=$(\
    getopt -o hv \
        -l "help,verbose,debug,show-progress,version,v,mysql-database:,mysql-user:,mysql-password:,\
dump-file:,tld:,dump-files-dir:,db-version:" \
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

	--debug)
            shift
            DEBUG="yes"
	    VERBOSEARG="--verbose"
            ;;

	--show-progress)
            shift
	    if which pv > /dev/null;then
		CATCOMMAND="pv"
	    else
		printError "The show-progress argument needs pv to be installed (e.g. apt-get install pv)"
                exit 1
	    fi
            ;;
	
        -v|--version)
            shift
            printVersionAndExit
            ;;
        
        --mysql-user)
            shift
            db_username=$1
            shift
            ;;

        --mysql-password)
            shift
	    export MYSQL_PWD=$1
            shift
            ;;

	--mysql-database)
            shift
            db=$1
            shift
            ;;

        --dump-file)
            shift
            dump_file=$(readlink -e "$1")
            if ! [ -f "$dump_file" ]; then
                printError "The specified mysql file $dump_file is not found."
                exit 1
            fi
            shift
            ;;

	--tld)
            shift
            TLD=$1
            shift
            ;;

	--dump-files-dir)
            shift
	    DUMP_FILES_DIR=$1
            if ! [ -d "$DUMP_FILES_DIR" ]; then
                printError "The specified dump file directory does not exist."
                exit 1
            fi
            shift
            ;;

	--db-version)
	    shift
	    #format check
	    if echo $1 | grep --quiet -e "v[0-9]*"; then
		DATABASE_VERSION=$1
	    else
		printError "Invalid db-version specification. It should be like v19 or v6"
		exit 1
	    fi
            shift
            ;;

        --)
            shift
            break
            ;;

        *) 
            ;;
    esac
done

#some verification before doing the real job

if [ -n "$dump_file" ] && [ -n "$TLD"  -o  -n "$DUMP_FILES_DIR" -o -n "$DATABASE_VERSION" ]; then
    printError "Conflicting arguments. Please use either --dump-file or --tld + --dump-files-dir + --db-version."
    exit 1
fi

#Set up mysql login credentials if needed
if [ -n "$db_username" ]; then
    MYSQL_ARGUMENTS="--user=$db_username"
fi

printDebug "Mysql arguments:   $MYSQL_ARGUMENTS"
printDebug "Mysql Password:    $MYSQL_PWD"

if [ -z "$db" ]; then
	printError "Mysql database not specified. See $MYNAME --help"
	exit 1
fi

#If the tld is specified, we find out the dumpfile name.
if [ -z $dump_file ]; then
    dump_file="$DUMP_FILES_DIR"/"$TLD"/whoiscrawler_"$TLD"_mysql.sql.gz
    if [ ! -f "$dump_file" ]; then
	dump_file="$DUMP_FILES_DIR"/"$TLD"/whoiscrawler_"$DATABASE_VERSION"_"$TLD"_mysql.sql.gz
    fi
    #Quarterly feeds case
    if [ ! -f "$dump_file" ]; then
	TLDUNDERSCORE=$(echo $TLD | sed -e "s/\./_/g")
	dump_file="$DUMP_FILES_DIR"/"$TLD"/domains_whoiscrawler_"$DATABASE_VERSION"_"$TLDUNDERSCORE"_mysql.sql.gz
    fi
fi

printVerbose "Dump file: $dump_file"

if [ ! -f "$dump_file" ]; then
    printError "Database dump to be loaded is not specified or it does not exist."
    printError "See $MYNAME --help"
    exit 1
fi

#THE REAL WORK STARTS HERE
printVerbose "Creating database $db"
mysql ${MYSQL_ARGUMENTS} ${VERBOSEARG} -e "create database $db"
time=`date +%s`
	echo "loading data from file $dump_file"
	if [ ${dump_file: -3} == ".gz" ]; then

	    $CATCOMMAND "$dump_file" | gunzip -c |mysql ${MYSQL_ARGUMENTS} $db
	else
	
	    $CATCOMMAND $dump_file | mysql ${MYSQL_ARGUMENTS} 
	fi

time2=`date +%s`
dur=`expr $time2 - $time`
echo "took $dur seconds."

