/* 
Sample schema file for Website Contacts and Categories MySQLddatabase 
v 0.0
(c) WhoisXML API, Inc.
*/

CREATE TABLE category(
category VARCHAR(255) PRIMARY KEY
);

CREATE TABLE domain(
domainID INTEGER PRIMARY KEY AUTO_INCREMENT,
domainName VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
countryCode VARCHAR(2),
meta_title LONGBLOB,
meta_description LONGBLOB,
socialLinks_facebook TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
socialLinks_googlePlus TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
socialLinks_instagram TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
socialLinks_twitter TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
socialLinks_linkedIn TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
);

CREATE TABLE domain_category(
categoryID VARCHAR(255),
domainID INTEGER,
PRIMARY KEY (categoryID, domainID)
);

CREATE TABLE email(
emailID INTEGER PRIMARY KEY AUTO_INCREMENT,
domainID INTEGER,
description LONGBLOB,
email TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
CONSTRAINT FK_email_domain FOREIGN KEY(domainID) REFERENCES domain(domainID)
);

CREATE TABLE phone(
phoneID INTEGER PRIMARY KEY AUTO_INCREMENT, 
domainID INTEGER, 
description LONGBLOB,
phoneNumber TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
callHours LONGBLOB,
CONSTRAINT FK_phone_domain FOREIGN KEY(domainID) REFERENCES domain(domainID)
);

CREATE TABLE postalAddress(
postalAddressID INTEGER PRIMARY KEY AUTO_INCREMENT,
domainID INTEGER, 
postalAddress LONGBLOB,
CONSTRAINT FK_postalAddress_domain FOREIGN KEY(domainID) REFERENCES domain(domainID)
);

CREATE TABLE companyName(
companyNameID INTEGER PRIMARY KEY AUTO_INCREMENT,
domainID INTEGER, 
companyName LONGBLOB,
CONSTRAINT FK_company_domain FOREIGN KEY(domainID) REFERENCES domain(domainID)
);
