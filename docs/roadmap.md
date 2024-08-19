# Roadmap

The application roadmap will continue to evolve over the next several months as features are imported from prior versions and converted from other languages.  Please be patient and check back after each release for updates.

## &raquo; Road to Version 1.0

!!! important
    As of 2024-08-18 all core features for Version 1.0 are **complete**.  Remaining activities will be to throughly test, tune, and validate all services in all available configurations.  Releases will be posted as groups of fixes/enhancements are completed.

- Features
    - SQL Editor - **COMPLETE** *v0.0.1*
    - Query Results Viewer - **COMPLETE** *v0.0.1*
    - Meta Data Viewer - **COMPLETE** *v0.0.1*
    - Multi-Tab Support - **COMPLETE** *v0.5.4*
    - Query Results Downloads - **COMPLETE** *v0.0.1*
    - DB Session Viewer - **COMPLETE** *v0.4.3*
    - DB Lock Viewer - **COMPLETE** *v0.4.3*
    - Rate Limits - **COMPLETE** *v0.4.2*
    - Client-side Results Filtering - **COMPLETE** *v0.5.4*

- [Authenticators](configuration/authenticator.md)
    - Local Database authentication - **COMPLETE** *v0.0.1*
    - OpenLDAP authentication - **COMPLETE** *v0.0.1*
    - Active Directory authentication - **COMPLETE** *v0.0.3*

- [Session Managers](configuration/tokenizer.md)
    - Local Tokens - **COMPLETE** *v0.0.1*
    - DynamoDB Tokens - **COMPLETE** *v0.0.2*
    - Redis Tokens - **COMPLETE** *v0.0.3*

- [Database Connectors](configuration/connections.md)
    - PostgreSQL database connector - **COMPLETE** *v0.0.1*
    - Oracle database connector - **COMPLETE** *v0.2.0*
    - MySQL/MariaDB database connector - **COMPLETE** *v0.0.3*
    - AWS Redshift database connector - **COMPLETE** *v0.3.0*

- [Database Connector Managers](configuration/connections.md)
    - Static Settings file (*settings.yml*) - **COMPLETE** *v0.0.1*
    - AWS Secrets Manager - **COMPLETE** *v0.1.0*

- [Profile Managers](configuration/profiler.md)
    - Local Profiles - **COMPLETE** *v0.4.0*
    - DynamoDB Profiles - **COMPLETE** *v0.4.0*
    - <strike>Redis Profiles</strike>
    - S3 Profiles - **COMPLETE** *v0.5.3*

- Installers
    - CGI Configuration (Apache/httpd) - [**Instructions**](installation/apache.md)
    - AWS CloudFormation / CDK - [**Instructions**](installation/aws.md)

!!! note
    These features are being worked in parallel so as minor releases are published it may look a bit random as to which features on the list are enabled.  That will be directly driven by the time required to complete the integration and perform any reasonable testing.

## Future Thinking

As no good tool is ever truly complete please find below the scratch-pad of features that will be considered for releases after v1.0.

- Integrated Intellisense
- Syntax highlighting
- SQL Autocomplete
- Microsoft SQL Server
- IBM DB2 (LUW)
- <strike>S3 object options (in addition to Local, DynamoDB, and Redis)</strike> - *ADDED in 0.5.3*
- Result download options for CSV, XML, JSON, etc.