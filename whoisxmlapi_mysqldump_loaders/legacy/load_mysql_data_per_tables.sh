schema_file="$1"
if [ ! -f "$schema_file" ]; then
    echo "invalid schema file $schema_file";
    exit
fi
table_files_dir="$2"
if [ ! -d "$table_files_dir" ]; then
    echo "please specify a valid directory where all table files reside in"
    exit
fi
db="$3"
if [ -z "$db" ]; then
    echo "db is missing"
    exit
fi
db_username="$4"
if [ -z "$db_username" ]; then
    echo "db username is missing"
    exit
fi
db_password="$5"
if [ -z "$db_password" ]; then 
    echo "db_password is missing"
    exit
fi
./load_mysql_schema.sh $schema_file $db $db_username $db_password

tables="whois_record registry_data contact domain_names_whoisdatacollector"

mysql -u$db_username -p$db_password $db -e "alter table whois_record drop index domain_name_index;alter table whois_record drop index domain_name;"
mysql -u$db_username -p$db_password $db -e "alter table registry_data drop index domain_name_index;alter table registry_data drop index domain_name;"

table_files_dir=$table_files_dir/*

for file in $table_files_dir; do
 
    time=`date +%s`
    if [ -f "$file" ]; then
        time=`date +%s`

        echo "loading data from file $file"
        if [ ${file: -3} == ".gz" ]; then
	    { echo "SET autocommit = 0;" 
	 	zcat "$file"
	 	echo "commit;" ; } | mysql -u$db_username -p$db_password --force $db
	elif [ ${file: -4} == ".sql" ]; then
            { echo "SET autocommit = 0;"
                cat "$file"
                echo "commit;" ; } | mysql -u$db_username -p$db_password --force $db    
	fi

    fi    
    
    time2=`date +%s`
    dur=`expr $time2 - $time`
    echo " loading $table from file $file took $dur seconds"

done
time=`date +%s`
mysql --force -u$db_username -p$db_password $db -e "alter table whois_record add index domain_name_index(domain_name)"
mysql --force -u$db_username -p$db_password $db -e "alter table registry_data add index domain_name_index(domain_name)"
 time2=`date +%s`
    dur=`expr $time2 - $time`
    echo " add indices took $dur seconds"

