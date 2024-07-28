# Query Commander &middot; [![GitHub license](https://img.shields.io/github/license/lnxusr1/query-commander)](https://github.com/lnxusr1/query-commander/blob/master/LICENSE) ![Python Versions](https://img.shields.io/pypi/pyversions/yt2mp3.svg) ![Read the Docs](https://img.shields.io/readthedocs/query-commander) ![GitHub release (latest by date)](https://img.shields.io/github/v/release/lnxusr1/query-commander)

Introducing **Query Commander**, the revolutionary *opensource* browser-based SQL tool designed for secure and efficient database management. 

![Basic Screenshot](images/screen_basic.png)

## Features:

1. **Database Connectivity**
    - Support for multiple database types (Oracle, PostgreSQL, Redshift, MySQL, etc.)
    - Support for multiple server connections and heterogeneous targets

3. **Database Management**
    - Viewing of database objects
    - Browse Schemas
    - Data export capabilities
    - Explain Plain visualization

4. **Metadata Access**
    - View table structures, constraints, indexes, relationships, roles, and permissions
    - Generate ddl for views, materialized views, procedures, functions, and much more

5. **User Interface**
    - Intuitive, familiar, and user-friendly interface
    - Browser-based multi-tab and multi-window interface
    - SQL Editor: Custom SQL Execution and results display

6. **Enhanced Security**
    - Support for End-to-End Encryption
    - Multiple authentication options (Database login-based, LDAP/Active Directory)
    - Optional time-based rate limits for queries executed and/or total records retrieved by user
    - Advanced permissions management with "Persona proxies" and group-based authorization
    - Ideal for cloud-hosted and remote database server access
    - Support for AWS Secret Manager for secure credential storage and database server info

7. **Modern Hosting Options**
    - Traditional installation with CGI executions
    - Optional **Serverless** installation

!!! note "Serverless Hosting"
    Serverless hosting in AWS leverages the combination of **S3** file storage for static objects, **API Gateway** + **Lambda** for backend processing, and **DynamoDB** for secure token storage.

!!! danger "SECURITY: SOX and HIPAA Compliance"
    By enabling LDAP (Active Director or OpenLDAP) authentication Query Commander can leverage "Persona proxies" which allow for tying role-based access in the database to users authenticated via LDAP.  
    
    Persona proxies eliminate the need for users to be individually created/maintained inside the database.  This feature could produce significant time savings for user management and access pruning depnending on the size of your user-base.



