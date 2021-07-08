#!/bin/bash
#
#Sample script to load binary mysql dumps for a tld
#
#Copyright (c) 2010-2021 Whois API LLC,  http://www.whoisxmlapi.com
#
#Note: IF YOU ARE READING THIS SCRIPT JUST TO COLLECT IDEAS FOR YOUR OWN LOADER,
#      VISIT THE END OF THE FILE WHERE THE REAL WORK IS DONE
#
# Global variables.
#
LANG=C
LC_ALL=C
VERSION="0.0.3"
VERBOSE="no"
DEBUG="no"
MYNAME=$(basename $0)

#No mysql stuff by default. This is set by mandatory args.
unset MYSQL_USER
unset MYSQL_PASSWORD
#Default mysql data directory
MYSQL_DATA_DIR=/var/lib/mysql
#DEFAULT MYSQL START STOP COMMAND
MYSQL_STOP_COMMAND="/etc/init.d/mysql stop"
MYSQL_START_COMMAND="/etc/init.d/mysql start"
#Dry run: do not touch the database
DRY_RUN="No"
#Importing generic utilities

source load_mysql_utils.sh

function printHelpAndExit()
{
    echo "Usage: $MYNAME [OPTION]..."
    echo "$MYNAME -- loads data for given tlds"
    echo "from a binary mysql dump "
    echo " into a table in a mysql database."
    echo ""
echo " -h, --help                  Print this help and exit."
echo " -v, --version               Print version information and exit."
echo " --verbose                   Print more messages. Recommended."
echo " --debug                     Print extensive debug messages"
echo " --dry-run                   Dry run: not touching the db, just verifying and extracting data"
echo " --mysql-user=USERNAME       User name to login to the mysql database (optional)."
echo " --mysql-password=PASSWORD   Password to login to the data source (optional)."
echo " --mysql-data-dir=DIRECTORY   The directory where mysql stores its data. "
echo "                              default: /var/lib/myqsl"
echo "                              You should have write permission on it"
echo " --import-data-dir=DIRECTORY The dump files for the tld-s are in this directory."
echo " --schema-file=SCHEMAFILE    The schema file to be used when loading."
echo "                              Defaults to the file load_binary_whois_dumps.sh"
echo "                              in the same directory where the script is."
echo " --tlds                       Comma-separated list of tlds to load."
echo " --db-version=STRING          The version to load download. Required for --tld Format: vNN, e.g. v19"
echo ""
    echo "Consult the supplied REDAME.txt for a detailed description."
    echo ""
    exit 1
}

ARGS=$(\
    getopt -o hv \
        -l "help,verbose,debug,version,v,dry-run,mysql-user:,mysql-password:,\
mysql-start-command:,mysql-stop-command:,import-data-dir:,schema-file:,tlds:,db-version:" \
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
	    MYSQL_VERB_ARG="--verbose"
            ;;

	--dry-run)
            shift
            DRY_RUN="Yes"
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

	--mysql-start-command)
            shift
	    export MYSQL_START_COMMAND=$1
            shift
            ;;

	--mysql-stop-command)
            shift
	    export MYSQL_STOP_COMMAND=$1
            shift
            ;;

	--mysql-data-dir)
            shift
	    MYSQL_DATA_DIR=$1
            if ! [ -d "$MYSQL_DATA_DIR" ]; then
                printError "The specified mysql data directory does not exist."
                exit 1
            fi
            shift
            ;;
	
	--tlds)
            shift
            TLDS=$1
            shift
            ;;

	--import-data-dir)
            shift
	    IMPORT_DATA_DIR=$1
            if ! [ -d "$IMPORT_DATA_DIR" ]; then
                printError "The specified data directory does not exist."
                exit 1
            fi
            shift
            ;;

        --schema-file)
            shift
	    export SCHEMA_FILE=$1
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
#preliminary checks
#Check if we can write mysql's data directory
if ! [ -w "$MYSQL_DATA_DIR" ] && [ "$DRY_RUN" == "No" ];then
    printError "You cannot write the mysql data directory. Perhaps you should run this script as root."
    exit 1
fi

#We need the database version
if [ -z "$DATABASE_VERSION" ];then
    printError "Please specify --db-version, e.g. --db-version = v20."
    printError "See also the output of "
    printError "$MYNAME --help"
    exit 1
fi

#Set up mysql login credentials if needed

if [ -n "$db_username" ]; then
    MYSQL_ARGUMENTS="--user=$db_username"
fi
if [ -n "$MYSQL_PWD" ]; then
    MYSQL_ARGUMENTS="$MYSQL_ARGUMENTS --password=$MYSQL_PWD"
fi
printDebug "Mysql arguments:   $MYSQL_ARGUMENTS"


if [ $DRY_RUN == "Yes" ];then
    if [ $DEBUG == "yes" -o $VERBOSE == "true" ];then
	mysql_here="echo MySQL would do mysql"
    else
	mysql_here="true"
    fi
else
    mysql_here="mysql $MYSQL_ARGUMENTS $MYSQL_VERB_ARG"
fi
printDebug "Mysql: $mysql_here"

#Check for the schema file

if [ -z $SCHEMA_FILE ];then
    SCHEMA_FILE="whoiscrawler_mysql_schema.sql"
fi;

if ! [ -f $SCHEMA_FILE ];then
    printError "The scema file $SCHEMA_FILE is not found"
    exit 1
else
    printVerbose "Schema file: $SCHEMA_FILE"
fi

#Parse the list of tlds
TLDS=$(echo $TLDS | sed -e s/,/\ /g | sed -e "s/\\./_/g")
printDebug "TLDS: $TLDS"

FILELIST="contact.ibd registry_data.ibd whois_record.ibd domain_names_whoisdatacollector.ibd"

for TLD in $TLDS;do
    printVerbose "Checking data for tld: $TLD"
    TLDDOT=$(echo $TLD | tr _ .)
    if [ -f $IMPORT_DATA_DIR/$TLDDOT.7z ];then
       printVerbose "Compressed data found for domain $TLD, uncompressing"
       wd=$(pwd)
       cd $IMPORT_DATA_DIR
       p7zip -d $TLDDOT.7z
       cd $wd
    fi
    #For gtlds and cctlds we have different naming conventions
    if [ -d "$IMPORT_DATA_DIR"/whoiscrawler_"$DATABASE_VERSION"_"$TLD" ];then
	TLDDIR="$IMPORT_DATA_DIR"/whoiscrawler_"$DATABASE_VERSION"_"$TLD"
    else
	TLDDIR="$IMPORT_DATA_DIR"/domains_whoiscrawler_"$DATABASE_VERSION"_"$TLD"
    fi
    printDebug "TLD subdirectory:" $TLDDIR
    
    printVerbose "Checking files in $TLDDIR"
    for FILE in $FILELIST;do
	printDebug "Checking $TLDDIR/$FILE"
	if ! [ -f "$TLDDIR/$FILE" ];then
	    printError "File $TLDDIR/$FILE is missing."
	    exit 1
	fi
    done
    printVerbose "Files for $TLD are found, OK."
done

#At this point we have all the files and all the information to load the database
#so we can do the
#REAL JOB:
TABLES="contact domain_names_whoisdatacollector registry_data whois_record"
G_START_TIME=$(date +%s)

for TLD in $TLDS;do
    printVerbose "Loading data for tld: $TLD"
    #For gtlds and cctlds we have different naming conventions
    if [ -d "$IMPORT_DATA_DIR"/whoiscrawler_"$DATABASE_VERSION"_"$TLD" ];then
	TLDDIR="$IMPORT_DATA_DIR"/whoiscrawler_"$DATABASE_VERSION"_"$TLD"
	DB=whoiscrawler_"$DATABASE_VERSION"_"$TLD"
    else
	TLDDIR="$IMPORT_DATA_DIR"/domains_whoiscrawler_"$DATABASE_VERSION"_"$TLD"
	DB=domains_whoiscrawler_"$DATABASE_VERSION"_"$TLD"
    fi
    printVerbose "Creating database $DB."
    $mysql_here -e "CREATE DATABASE $DB"
    printVerbose "Loading schema."
    $mysql_here "$DB" < "$SCHEMA_FILE"

    printVerbose "importing tablespaces"
    G_START_TIME=$(date +%s)
    for table in $TABLES; do
	START_TIME=$(date +%s)
	q="set FOREIGN_KEY_CHECKS=0;ALTER TABLE $DB.$table DISCARD TABLESPACE;"
	printDebug "$q"
	$mysql_here -e "$q"
	file="$table.ibd"
	printVerbose "Copying table file $file from $TLDDIR to $MYSQL_DATA_DIR/$DB"
	if [ $DRY_RUN == "No" ];then
	    printVerbose "Stopping MySQL server before copying."
	    $MYSQL_STOP_COMMAND
	    cp  "$TLDDIR/$file" "$MYSQL_DATA_DIR/$DB/."
	    chown -R mysql:mysql "$MYSQL_DATA_DIR/$DB"
	    printVerbose "Starting MySQL again."
	    $MYSQL_START_COMMAND
	fi
	printVerbose "Importing tablesapce"
	q="ALTER TABLE $DB.$table IMPORT TABLESPACE"
	printDebug "$q"
	$mysql_here -e "$q"
		
	END_TIME=$(date +%s)
	DUR=$((END_TIME-START_TIME))
	printVerbose "Import of the table $table for the tld $TLD took $DUR seconds"
    done
done

G_END_TIME=$(date +%s)
GDUR=$((G_END_TIME-G_START_TIME))
printVerbose "$MYNAME has finished in $GDUR seconds."

