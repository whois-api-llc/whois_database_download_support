#!/bin/bash
#
#Sample script to load the downloaded csv into a database
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
unset MYSQL_DATABASE

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
    echo "$MYNAME -- loads data from a csv file downloaded from WhoisXML API feeds"
    echo " into a table in a mysql database."
    echo ""
echo " -h, --help                  Print this help and exit."
echo " -v, --version               Print version information and exit."
echo " --verbose                   Print more messages."
echo " --mysql-user=USERNAME       User name to login to the mysql database (optional)."
echo " --mysql-password=PASSWORD   Password to login to the data source (optional)."
echo " --mysql-database=DATABASE   The name of the mysql database to load data into."
echo " --csv-format=FORMAT         The format of the csv file to be loaded. Must be one of 'regular', 'simple' or 'full'."
echo " --schema-file=SCHEMAFILE    The schema file to be used when loading. These are provided with the script."
echo " --csv-file=CSVFILE          The csv file to be loaded."
    echo ""
    echo "Example:"
    echo "$MYNAME --mysql-user=whoisuser --mysql-password=whoispassword --mysql-database=whoisdatabase --schema-file=loader_schema_simple.sql --csv-file=1.csv --csv-format=simple"
    echo ""
    echo 
    echo ""
    echo "The table into which data are loaded is "
    echo "  whois_record_flat for 'full' csv-s, "
    echo "  whois_record_flat_simple for 'simple' csv-s, and"
    echo "  whois_record_flat_regular for 'regular' csv-s."
    echo ""
    echo "Note: record id-s are auto incremented,"
    echo "      so each record is loaded again when the script is run."
    echo "      This can lead to repetitions."
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
        -l "help,verbose,debug,version,mysql-database:,mysql-user:,mysql-password:,csv-format:,\
csv-file:,schema-file:" \
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
	    VERBOSEARG="--verbose"
            ;;

	--debug)
            shift
            DEBUG="yes"
	    VERBOSEARG="--verbose"
            ;;

        -v|--version)
            shift
            printVersionAndExit
            ;;
        
        --mysql-user)
            shift
            MYSQL_USER=$1
            shift
            ;;

        --mysql-password)
            shift
	    export MYSQL_PWD=$1
            shift
            ;;

	--mysql-database)
            shift
            MYSQL_DATABASE=$1
            shift
            ;;


        --csv-format)
            shift
	    if echo $1 | grep --quiet -e "simple\|regular\|full"; then
		FORMAT=$1	    
	    else
		printError "Supported csv formats are: simple, regular, and full."
	    exit 1
 	    fi

            shift
            ;;
        
        --csv-file)
            shift
            CSV_FILE=$(readlink -e "$1")
            if ! [ -f "$CSV_FILE" ]; then
                printError "The csv file $CSV_FILE is not found."
                exit 111
            fi
            shift
            ;;

	--schema-file)
            shift
            SCHEMA_FILE=$(readlink -e "$1")
            if ! [ -f "$SCHEMA_FILE" ]; then
                printError "The schema file $SCHEMA_FILE is not found."
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

#Set up mysql login credentials if needed
if [ -n "$MYSQL_USER" ]; then
    MYSQL_ARGUMENTS="--user=$MYSQL_USER"
#    if [ -n "$MYSQL_PASSWORD" ];then
#	MYSQL_ARGUMENTS="$MYSQL_ARGUMENTS --password=$MYSQL_PASSWORD"
#    fi;
fi;

printDebug "Mysql arguments: $MYSQL_ARGUMENTS"
printDebug "Mysql password: $MYSQL_PWD"

if [ -z "$MYSQL_DATABASE" ]; then
	printError "Mysql database not specified. See $MYNAME --help"
	exit 1
fi
if [ ! -f "$CSV_FILE" ]; then
	printError "Input csv file not specified or does not exist. See $MYNAME --help"
	exit 1
fi
if [ ! -f "$SCHEMA_FILE" ]; then
	printError "Schema file not specified or does not exist. See $MYNAME --help"
	exit 1
fi
CSV_FILE=`readlink -e $CSV_FILE`
SCHEMA_FILE=`readlink -e $SCHEMA_FILE`
case ${FORMAT} in
	simple|regular )
		table="whois_record_flat_${FORMAT}"
	;;
	full )
		table="whois_record_flat"
	;;
	* )
		echo "FORMAT must be specified(simple, regular, or full)"
		exit 1
	;;
esac

#HERE WE DO THE REAL WORK.
#IF YOU USE THIS SCRIPT JUST TO COLLECT IDEAS, START READING HERE

if [[ -z $(mysql $(eval echo "$MYSQL_ARGUMENTS") -A --skip-column-names ${MYSQL_DATABASE} <<< "SHOW TABLES LIKE \"${table}\";") ]]
then
    printVerbose "Loading schema for table $table."
    mysql $(eval echo "$MYSQL_ARGUMENTS") ${MYSQL_DATABASE} ${VERBOSEARG} <${SCHEMA_FILE}
else
    printVerbose "Not loading schema, $table exists."
fi

#Determining the line terminator of the csv file
line_terminator="\\n"
if file ${CSV_FILE} | grep -q CRLF ; then
    line_terminator="\\r\\n"
    printVerbose "Windows-style CRLF terminated input file detected."
else
    printVerbose "UNIX-style LF terminated input file detected."
fi

fields=$(head -n 1 ${CSV_FILE}|sed 's/"//g')

mysql $(eval echo "$MYSQL_ARGUMENTS") ${MYSQL_DATABASE} ${VERBOSEARG} -e "load data local infile \"${CSV_FILE}\" IGNORE into table $table
	fields terminated by ',' enclosed by '\"' LINES TERMINATED BY '${line_terminator}' IGNORE 1 LINES (${fields})"
