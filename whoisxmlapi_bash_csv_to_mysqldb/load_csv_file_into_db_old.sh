#!/bin/bash

USAGE="USAGE:\n\t$0 db csv_file schema mode"

db="$1"
csv_file="$2"
schema="$3"
mode="$4"

if [[ $# -ne 4 ]]
then
	echo -e "${USAGE}"
	exit 1
fi

if [ -z "$db" ]; then
	echo -e "db is missing\n${USAGE}"
	exit 1
fi
if [ ! -f "$csv_file" ]; then
	echo -e "csv_file $csv_file doesn't exist\n${USAGE}"
	exit 1
fi
if [ ! -f "$schema" ]; then
	echo -e "schema file $schema doesn't exist\n${USAGE}"
	exit 1
fi
csv_file=`readlink -e $csv_file`
schema=`readlink -e $schema`
case ${mode} in
	simple|regular )
		table="whois_record_flat_${mode}"
	;;
	full )
		table="whois_record_flat"
	;;
	* )
		echo "mode must be specified(simple, regular, or full)"
		exit 1
	;;
esac

if [[ -z $(mysql -A --skip-column-names ${db} <<< "SHOW TABLES LIKE \"${table}\";") ]]
then
	mysql ${db} --verbose <${schema}
fi

fields=$(head -n 1 ${csv_file}|sed 's/"//g')
#nfields=$(echo ${fields}|awk -F\, '{print NF}')
#ncolumns=$(mysql -A --skip-column-names ${db} <<< "SHOW COLUMNS FROM ${table};"|wc -l)
#if [[ ${nfields} -ne ${ncolumns} ]]
#then
#	echo "Fatal: number of fileds ${nfields} not equal to nomber of columns ${ncolumns} in table ${table}"
#	exit 1
#fi

mysql ${db} --verbose -e "load data infile \"${csv_file}\" IGNORE into table $table
	fields terminated by ',' enclosed by '\"' LINES TERMINATED BY '\n' IGNORE 1 LINES
	(${fields})"
