#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR" || exit 1

DB=$1
RESTORE_DIR=$2
DB_DATA_DIR=${3:-/var/lib/mysql}
SCHEMA_FILE=${4:-$DIR/whoiscrawler_mysql_schema.sql}

TABLES="contact domain_names_whoisdatacollector registry_data whois_record  whois_record_ids_whoisdatacollector"

if [ -z "$DB" ]; then
    echo "db is missing"
    exit
fi

if [ ! -d "$RESTORE_DIR" ]; then
    echo "restore_dir $RESTORE_DIR must be valid, we will copy data from this directory to your database data directory"
    exit
fi

if [ ! -d "$DB_DATA_DIR" ]; then
    echo "db_data_dir $DB_DATA_DIR must be valid, this should probably be /var/lib/mysql/ we will copy data from restore_dir to this directory/db_name"
    exit
fi

if [ ! -f "$SCHEMA_FILE" ]; then
    echo "schema_file $SCHEMA_FILE is missing"
    exit
fi


echo "creating database $DB"
mysql  -e "create database $DB"
mysql "$DB" < "$SCHEMA_FILE"


if [ ! -d "$DB_DATA_DIR/$DB" ]; then
    echo "$DB_DATA_DIR/$DB doesn't exist!"
    exit
fi


echo "importing tablespaces"
G_START_TIME=$(date +%s)

for table in $TABLES; do
    START_TIME=$(date +%s)
    q="set FOREIGN_KEY_CHECKS=0;ALTER TABLE $DB.$table DISCARD TABLESPACE;"
    echo "$q"
    mysql  -e "$q"

    file="$table.ibd"
    echo "copy table file $file from $RESTORE_DIR/$DB to $DB_DATA_DIR/$DB"
    cp  "$RESTORE_DIR/$DB/$file" "$DB_DATA_DIR/$DB/"

    chown -R mysql:mysql "$DB_DATA_DIR/$DB"

    q="ALTER TABLE $DB.$table IMPORT TABLESPACE"
    echo "$q"
    mysql -e "$q"

    END_TIME=$(date +%s)
    DUR=$((END_TIME-START_TIME))
    echo "import table $table took $DUR seconds"
done

G_END_TIME=$(date +%s)
GDUR=$((G_END_TIME-G_START_TIME))
echo "import tables took $GDUR seconds"

