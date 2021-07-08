#!/bin/bash
#
#Sample script to load ASCII mysql dumps for a tld
#This loads the schema first, then load each table’s data separately.
#Recommened for a large database such as .com
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
echo "                               This database is created by the script by default, "
echo "                               so should not exist, or use --no-create-db"
echo " --schema-file=SCHEMAFILE    The schema file to be used when loading. "
echo "                               IMPORTANT: should be schema only, should not contain data."
echo "                               Not to be used with --tld"
echo " --schema-only                 If specified, the table files are not loaded."
echo " --data-only                   If specified, only tables data are loaded into an existing database "
echo "                                   with already loaded schema"
echo " --no-create-db           Does not create the database newly, supposes that it exists already"
echo " --table-files-directory=TABLEFILESDIR  The directory where the dumps of all tables reside."
echo "                               This contains the files with the actual data."
echo "                               Not to be used with --tld"
echo " --tld=TLD                    load data for this tld"
echo " --schema-files-dir=DIRECTORY   The schema files for the tld-s are in this directory. The table files have to be in its subdirectory named 'tables'. Only for --tld"
echo " --db-version=STRING          The version to load download. Required for --tld Format: vNN, e.g. v19"
    echo ""
    echo "Examples:"
    echo ""
    echo "  -loading sample data downloaded into a directory mysqldump_sample from "
    echo "          http://domainwhoisdatabase.com/whois_database/sample/gtlds/v20/mysqldump_sample/aaa"
    echo ""
    echo "$MYNAME --mysql-database=sample_db_aaa --mysql-user=whoisuser --mysql-password=whoispassword --schema-files-dir=mysqldump_sample --db-version=v20 --tld=aaa --verbose --show-progress"
    echo ""
    echo "      or the same task quietly, specifying the file names and paths directly:"
    echo ""
    echo "$MYNAME --schema-file=mysqldump_sample/aaa/whoiscrawler_v20_aaa_mysql_schema.sql.gz --table-files-directory=mysqldump_sample/aaa/tables --mysql-database=sample_db_aaa --mysql-user=whoisuser --mysql-password=whoispassword"
    echo ""
    echo "   -loading production data downloaded into a directory database_dump/mysqldump/aaa from"
    echo "          http://www.domainwhoisdatabase.com/whois_database/v20/database_dump/mysqldump/aaa"
    echo ""
    echo "$MYNAME  --mysql-database=production_db_aaa --mysql-user=whoisuser --mysql-password=whoispassword --schema-files-dir=database_dump/mysqldump --tld=aaa --db-version=v20 --verbose --show-progress"
    echo ""
    echo "      or the same task specifying the file names and paths directly:"
    echo ""
    echo "$MYNAME --schema-file=database_dump/mysqldump/aaa/whoiscrawler_v20_aaa_mysql_schema.sql.gz --table-files-directory=database_dump/mysqldump/aaa/tables --mysql-database=prod_db_aaa --mysql-user=whoisuser --mysql-password=whoispassword --verbose --show-progress"
    exit 1
}

ARGS=$(\
    getopt -o hv \
        -l "help,verbose,debug,show-progress,version,v,mysql-database:,mysql-user:,mysql-password:,table-files-directory:,\
schema-file:,schema-only,data-only,no-create-db,tld:,schema-files-dir:,db-version:" \
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

        --schema-only)
            shift
            SCHEMAONLY="True"
            ;;
	
        --data-only)
            shift
	    DONTCREATEDB="True"
            DATAONLY="True"
            ;;

	--no-create-db)
            shift
            DONTCREATEDB="True"
            ;;

        --table-files-directory)
            shift
	    table_files_dir=$1	    	    
	    if ! [ -d "$table_files_dir" ]; then
                printError "The directory $schema_file in which the table files should reside is not found."
                exit 1
            fi
            shift
            ;;
        
        --schema-file)
            shift
            schema_file=$(readlink -e "$1")
            if ! [ -f "$schema_file" ]; then
                printError "The specified schema file $schema_file is not found."
                exit 1
            fi
	    #IF we have zgrep, we verify if the schema file is really schema-only.
	    if [ -x $(which zgrep) ]; then
		if zgrep -q "Dumping data for table" $schema_file; then
		    printError "The specified schema file $schema_file contains actual data."
		    printError "Please specify a schema-only file"
		    exit 1
		fi
	    fi
            shift
            ;;

	--tld)
            shift
            TLD=$1
            shift
            ;;

	--schema-files-dir)
            shift
	    SCHEMA_FILES_DIR=$1
            if ! [ -d "$SCHEMA_FILES_DIR" ]; then
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

#Set up mysql login credentials if needed
if [ -n "$db_username" ]; then
    MYSQL_ARGUMENTS="--user=$db_username"
fi;

printDebug "Mysql arguments:   $MYSQL_ARGUMENTS"
printDebug "Mysql Password:    $MYSQL_PWD"

if [ -n "$table_files_dir" -o -n "$schema_file" ] && [ -n "$TLD"  -o  -n "$SCHEMA_FILES_DIR" -o -n "$DATABASE_VERSION" ]; then
    printError "Conflicting arguments. Please use either --table-files-directory + --schema-file or --tld + --schema-files-dir + --db-version."
    exit 1
fi

if [ -z "$db" ]; then
	printError "Mysql database not specified. See $MYNAME --help"
	exit 1
fi

#If the tld is specified, we find out the schemafile name and the tables dir.
if [ -z "$schema_file" ]; then
    schema_file="$SCHEMA_FILES_DIR"/"$TLD"/whoiscrawler_"$TLD"_mysql_schema.sql.gz
    if [ ! -f "$schema_file" ]; then
	schema_file="$SCHEMA_FILES_DIR"/"$TLD"/whoiscrawler_"$DATABASE_VERSION"_"$TLD"_mysql_schema.sql.gz
    fi
    #Quarterly feeds case
    if [ ! -f "$schema_file" ]; then
	TLDUNDERSCORE=$(echo "$TLD" | sed -e "s/\./_/g")
	schema_file="$SCHEMA_FILES_DIR"/"$TLD"/domains_whoiscrawler_"$DATABASE_VERSION"_"$TLDUNDERSCORE"_mysql_schema.sql.gz
    fi
    if [ -z "$SCHEMAONLY" ]; then
	table_files_dir="$SCHEMA_FILES_DIR"/"$TLD"/tables
    fi
fi

printVerbose "Schema file: $schema_file"
printVerbose "Tables dir: $table_files_dir"

if [ ! -f "$schema_file" ]; then
    printError "Schema file not specified or does not exist. See $MYNAME --help"
    exit 1
fi
if [ -z $SCHEMAONLY ] && [ ! -d "$table_files_dir" ]; then
    printError "The directory in which the table files should reside is not specified or does not exist."
    printError "See $MYNAME --help"
    exit 1
fi

#THE REAL WORK STARTS HERE
if [ -z "$DONTCREATEDB" ]; then
    printVerbose "Creating database $db"
    mysql ${MYSQL_ARGUMENTS} ${VERBOSEARG} -e "create database $db"
    printVerbose "Loading mysql schema"
else
    printVerbose "Not creating database, --no-create-db was specified."
fi

if [ -z "$DATAONLY" ]; then
    if [ ${schema_file: -3} == ".gz" ]; then
   
	$CATCOMMAND $schema_file | gunzip -c | mysql ${MYSQL_ARGUMENTS} ${VERBOSEARG} $db
    else
	$CATCOMMAND $schema_file mysql ${MYSQL_ARGUMENTS} ${VERBOSEARG} $db 
    fi
    printVerbose "Mysql schema loaded."
fi

if [ -n "$SCHEMAONLY" ]; then
    printVerbose "Schema-only loading, so we are ready."
    exit 0
fi

tables="whois_record registry_data contact domain_names_whoisdatacollector"

printVerbose "Trying to drop some unnecessary indices to load faster."
printVerbose "    They may not exists so mysql errors are normal here"
mysql ${MYSQL_ARGUMENTS} ${VERBOSEARG} $db -e "alter table whois_record drop index domain_name_index;alter table whois_record drop index domain_name;" >/dev/null 2>&1
mysql ${MYSQL_ARGUMENTS} ${VERBOSEARG} $db -e "alter table registry_data drop index domain_name_index;alter table registry_data drop index domain_name;">/dev/null 2>&1
printVerbose "Unnecessary indices, if any, have been dropped."
table_files_dir=$table_files_dir/*.sql.gz

printVerbose "Loading data from table files" 
for file in $table_files_dir; do
 
    time=`date +%s`
    if [ -f "$file" ]; then
        time=`date +%s`

        printVerbose "loading data from file $file"
	#No verbose mysql here as the echoed output can be huge.
        if [ ${file: -3} == ".gz" ]; then
	    { echo "SET autocommit = 0;" 
	 	$CATCOMMAND "$file" | gunzip -c
	 	echo "commit;" ; } | mysql ${MYSQL_ARGUMENTS} --force $db
	elif [ ${file: -4} == ".sql" ]; then
            { echo "SET autocommit = 0;"
                $CATCOMMAND "$file"
                echo "commit;" ; } | mysql ${MYSQL_ARGUMENTS} --force $db    
	fi

    fi    
    
    time2=`date +%s`
    dur=`expr $time2 - $time`
    printVerbose " loading $table from file $file took $dur seconds"

done
printVerbose "Creating new indices"
time=`date +%s`
mysql ${MYSQL_ARGUMENTS} ${VERBOSEARG} $db -e "alter table whois_record add index domain_name_index(domain_name)"
mysql ${MYSQL_ARGUMENTS} ${VERBOSEARG} $db -e "alter table registry_data add index domain_name_index(domain_name)"
 time2=`date +%s`
    dur=`expr $time2 - $time`
    printVerbose " adding indices took $dur seconds."

