schema_file="$1"
if [ ! -f "$schema_file" ]; then
    echo "invalid schema file $schema_file";
    exit
fi
db="$2"
if [ -z "$db" ]; then
    echo "db is missing"
    exit
fi
db_username="$3"
if [ -z "$db_username" ]; then
    echo "db username is missing"
    exit
fi
db_password="$4"
if [ -z "$db_password" ]; then 
    echo "db_password is missing"
    exit
fi
mysql -u$db_username -p$db_password -e "create database $db"
if [ ${schema_file: -3} == ".gz" ]; then
   
    gunzip<$schema_file | mysql -u$db_username -p$db_password $db
else
    mysql -u$db_username -p$db_password $db <$schema_file
fi
