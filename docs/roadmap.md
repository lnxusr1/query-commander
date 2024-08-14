# Roadmap

The application roadmap will continue to evolve over the next several months as features are imported from prior versions and converted from other languages.  Please be patient and check back after each release for updates.

## &raquo; Road to Version 1.0

- Features
    - SQL Editor - **COMPLETE**
    - Query Results Viewer - **COMPLETE**
    - Meta Data Viewer - **COMPLETE**
    - Multi-Tab Support - **COMPLETE**
    - Query Results Downloads - **COMPLETE**
    - DB Session Viewer - **COMPLETE**
    - DB Lock Viewer - **COMPLETE**
    - Rate Limits - **COMPLETE**
    - Client-side Results Filtering

- Authenticators
    - Local Database authentication - **COMPLETE**
    - OpenLDAP authentication - **COMPLETE**
    - Active Directory authentication - **COMPLETE**

- Session Managers
    - Local Tokens - **COMPLETE**
    - DynamoDB Tokens - **COMPLETE**
    - Redis Tokens - **COMPLETE**

- Database Connectors
    - PostgreSQL database connector - **COMPLETE**
    - Oracle database connector - **COMPLETE**
    - MySQL/MariaDB database connector - **COMPLETE**
    - AWS Redshift database connector - **COMPLETE**

- Database Connector Managers
    - Static Settings file (*settings.yml*) - **COMPLETE**
    - AWS Secrets Manager - **COMPLETE**

- Profile Managers
    - Local Profiles - **COMPLETE**
    - DynamoDB Profiles - **COMPLETE**
    - <strike>Redis Profiles</strike>

- Installers
    - Shell Script / Executable
    - AWS CloudFormation / CDK

!!! note
    These features are being worked in parallel so as minor releases are published it may look a bit random as to which features on the list are enabled.  That will be directly driven by the time required to complete the integration and perform any reasonable testing.

## Future Thinking

As no good tool is ever truly complete please find below the scratch-pad of features that will be considered for releases after v1.0.

- Integrated Intellisense
- Syntax highlighting
- SQL Autocomplete
- Microsoft SQL Server
- IBM DB2 (LUW)
- S3 object options (in addition to Local, DynamoDB, and Redis)
- Result download options for CSV, XML, JSON, etc.