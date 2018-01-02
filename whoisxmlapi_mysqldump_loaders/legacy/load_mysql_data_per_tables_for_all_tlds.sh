src_root_dir="$1"
version="$2"
db_username="$3"
db_password="$4"

if [ ! -d "$src_root_dir" ]; then
    echo "src_root_dir $src_root_dir is not valid"
    exit
fi
if [ -z "$version" ]; then
    echo "version is missing"
    exit
fi

tlds="pro coop asia us biz mobi info org net com"
for tld in $tlds; do
    ./load_mysql_data_per_tables_for_tld.sh $src_root_dir $tld $version $db_username $db_password
done
