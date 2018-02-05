#!/bin/bash
#A simple utility to convert pkcs12 files to certificates to be used
#with the ssl-auth version of whoisdownload.bash


if [[ $1 == "" || $1 == "--help" ]];then
    cat >&2 <<EOF
A script to convert ssl credentials obtained from WhoisXML API Inc.
to use them with whoisdownload.sh.

You have to run it only once. 
See also the attached README.
Usage:

   ./convertkey.sh pack.p12 YourPassword

where 
pack.p12 is your pk12 pack,
YourPassword     is your password. 

Note: treat the generated "client.key" file confidentially.
EOF
    exit 6
fi

if [[ ! -f $1 ]];then
    echo "ERROR: the pack file $1 does not exist" >&2
    exit 1
fi
if [ -z $2 ];then
    echo "ERROR: Your password is needed" >&2
    exit 1
fi


IN_PKCS="$1"
IN_PW="$2"

openssl pkcs12 -clcerts -nokeys -in "$IN_PKCS" -out client.crt -password pass:"$IN_PW" -passin pass:"$IN_PW"
openssl pkcs12 -cacerts -nokeys -in "$IN_PKCS" -out whoisxmlapi.ca -password pass:"$IN_PW" -passin pass:"$IN_PW"
openssl pkcs12 -nocerts -in "$IN_PKCS" -out private.key -password pass:"$IN_PW" -passin pass:"$IN_PW" -passout pass:"$IN_PW"
openssl rsa -in private.key -out "client.key" -passin pass:"$IN_PW"
rm private.key
chmod 400 client.* whoisxmlapi.ca

echo "All done. Now you can use the downloader script in this directory."
