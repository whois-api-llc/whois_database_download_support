#!/usr/bin/env python2
#This utility extracts a p12 pack obtained from WhoisXML API Inc.
#Into files that can be used with downloader scripts.

import sys
import os
from OpenSSL import crypto as c
from Crypto.PublicKey import RSA
import easygui as g

windowtitle='WhoisXML API SSL pack converter'
infile=g.fileopenbox('Choose the pack.p12 file obtained from WhoisXML API Inc.',
                     windowtitle)
password=g.passwordbox('Enter the password supplied with your pack',
                       windowtitle)

try:
    p12 = c.load_pkcs12(open("matyas-pack.p12", 'rb').read(), password) 
except:
    g.msgbox('Error: invalid pack or password. Exiting.')
    exit(6)
    
try:
    cert=c.dump_certificate(c.FILETYPE_PEM, p12.get_certificate())
    certfile=open('client.crt','w')
    certfile.write(cert)
    certfile.close()

    key=c.dump_privatekey(c.FILETYPE_PEM, p12.get_privatekey())
    rsakey=RSA.importKey(key)
    keyfile=open('client.key','w')
    keyfile.write(rsakey.exportKey())
    keyfile.close()
    os.chmod('client.key', 400)

    cacert=c.dump_certificate(c.FILETYPE_PEM, p12.get_ca_certificates()[0])
    cacertfile=open('whoisxmlapi.ca','w')
    cacertfile.write(cacert)
    cacertfile.close()
except:
    g.msgbox('Error: could not overwrite one of the files.\nEnsure that the following files do not exist or can be overwritten:\n   whoisxmlapi.ca\n   client.crt\n   client.key\n')
    exit(1)
    
g.msgbox('The files needed for authentication:\n   whoisxmlapi.ca\n   client.crt\n   client.key\n have been created.\nNow you can use ssl authentication.\n\nIMPORTANT: keep client.key secret!', windowtitle)
