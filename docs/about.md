# About

**Query Commander** is a browser-based SQL query tool designed to enable *Universal Database Access*.

## Mission

The mission of Query Commander is to provide a cloud-friendly SQL query tool that allows end-users to securely connect to databases and execute queries, while streamlining user provisioning and access management.

### Cloud-Friendly

Query Commander is designed to be able to execute in a serverless environment leveraging AWS components including **S3**, **API Gateway**, **Lambda**, **DynamoDB**, and **Secrets Manager**.  This serverless architecture allows for a centrally installed and managed software platform while eliminating the need for traditional server management, reducing infrastructure costs and maintenance efforts. It can be deployed through an automated AWS CloudFormation Template (CFT).

### Simplified User Access & Management

Query Commander simplifies user management and access through its *optional* use of LDAP authentication and database role proxies, referred to as "Personas." By authenticating users against **Active Directory**, Query Commander leverages existing corporate identity management, ensuring secure and centralized user validation. Upon authentication, the user's groups are retrieved from the LDAP directory and mapped to specific database service accounts or "Personas," each representing different access levels and roles within the database. This method eliminates the need for individual user logins and role assignments within the database, streamlining access control. It allows DevOps teams to manage a standardized set of personas rather than numerous unique user accounts, significantly reducing the risk of incorrect access levels.

### Security Focused

In today's technology landscape, social engineering often exposes individual user credentials, allowing malicious users to stealthily access company systems. These compromises present unique challenges to security teams worldwide. While no solution can prevent all attack vectors, Query Commander aims to empower security departments by slowing the pace of active data attacks using SQL query tools. This provides company security experts with valuable time to limit the scope of the attack.

## Author

Query Commander was originally developed by lnxusr1 in 2002 as a locally installed application.  It was designed to be a universal database query tool as there were few options available to developers at the time.  As the years passed new tools were introduced to the market that filled this gap and Query Commander was eventually deprecated.  Over the years new gaps emerged in the tools available to developers and so in 2023 the original tool was reimagined into a browser-based query tool specifically to address two areas:  (1) the lack of open source browser-based SQL tools that support the PostgreSQL database platform and (2) the poorly designed or outright lack of authentication and authorization mechanisms built into database engines that can leverage Microsoft's Active Directory platform.