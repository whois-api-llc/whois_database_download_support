schema_file="$1"
if [ ! -f "$schema_file" ]; then
    echo "invalid schema file $schema_file";
    exit
fi
dump_file="$2"
if [ ! -f "$dump_file" ]; then
    echo "please specify a valid mysqldump file"
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
time=`date +%s`
	echo "loading data from file $dump_file"
	if [ ${dump_file: -3} == ".gz" ]; then

	    zcat "$dump_file" |mysql -u$db_username -p$db_password $db
	else
	
	    mysql -u$db_username -p$db_password $db <$dump_file
	fi

time2=`date +%s`
dur=`expr $time2 - $time`
echo "took $dur seconds"

