/* 
Sample schema file for Website Contacts and Categories MySQLddatabase 
Categories-only version
v 0.0
(c) WhoisXML API, Inc.
*/

CREATE TABLE category(
category VARCHAR(255) PRIMARY KEY
);

CREATE TABLE domain(
domainID INTEGER PRIMARY KEY AUTO_INCREMENT,
domainName VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
countryCode VARCHAR(2)
);

CREATE TABLE domain_category(
categoryID VARCHAR(255),
domainID INTEGER,
PRIMARY KEY (categoryID, domainID)
);

