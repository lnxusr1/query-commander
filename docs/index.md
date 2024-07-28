# Query Commander &middot; [![GitHub license](https://img.shields.io/github/license/lnxusr1/query-commander)](https://github.com/lnxusr1/query-commander/blob/master/LICENSE) ![Python Versions](https://img.shields.io/pypi/pyversions/yt2mp3.svg) ![Read the Docs](https://img.shields.io/readthedocs/query-commander) ![GitHub release (latest by date)](https://img.shields.io/github/v/release/lnxusr1/query-commander)

Introducing __Query Commander__, the revolutionary browser-based SQL tool designed for secure and efficient database management. 

## Features:

1. __Database Connectivity:__  
    * Support for multiple database types (Oracle, MySQL, PostgreSQL, and more).
    * Supports multiple server connections and heterogeneous targets

3. __Database Management:__  
    * Viewing of database objects (tables, views, procedures, functions, triggers, etc.), 
    * Schema browsing
    * Data export capabilities
    * Explain plain visualization.

4. __Metadata Access:__ 
    * View table structures, constraints, indexes, relationships, roles, and permissions.
    * Generate ddl for views, materialized views, procedures, functions, and much more.

5. __User Interface:__ 
    * Intuitive, familiar, and user-friendly interface.  
    * Browser-based multi-tab and multi-window interface
    * SQL Editor: Custom SQL Execution and results display

6. __Enhanced Security:__
    * Multiple authentication options (configuration-based, database login-based, LDAP/Active Directory)
    * Advanced permissions management with "Persona proxies" and group-based authorization
    * Ideal for cloud-hosted and remote database server access

7. __Modern Hosting Options:__
    * Traditional installation with CGI executions
    * Optional __Serverless__ installation

!!! note "Serverless Hosting"
    Serverless hosting in AWS leverages the combination of __S3__ file storage for static objects, __API Gateway__ + __Lambda__ for backend processing, and __DynamoDB__ for secure token storage.

!!! danger "SECURITY: SOX and HIPAA Compliance"
    By enabling LDAP (Active Director or OpenLDAP) authentication Query Commander can leverage "Persona proxies" which allow for tying role-based access in the database to users authenticated via LDAP.  
    
    Persona proxies eliminate the need for users to be individually created/maintained inside the database.  This feature could produce significant time savings for user management and access pruning depnending on the size of your user-base.



## Not your ordinary SQL Tool...

1. __Browser-Based Solution:__ No local software installation required, allowing multiple users to benefit from a one-time setup.
2. __Robust Authentication and Authorization:__ Leverages Active Directory for username/password validation and group-based authorization. Users are authenticated against Active Directory, and their groups are mapped to database service accounts representing different access levels. This ensures secure, proven access mechanisms and simplifies management for DevOps teams.

By relying on established access protocols within Active Directory and database engines, Query Commander eliminates the need for a separate, complex codebase. This approach also reduces the risk of incorrect access assignments, which is crucial for compliance with regulations like SOX and HIPAA. Query Commander streamlines database access management, making it an indispensable tool for any organization.



## INSTALL

## How do I get support?

## Who build it and why?

