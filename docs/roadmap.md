# Roadmap

The application roadmap will continue to evolve over the next several months as features are imported from prior versions and converted from other languages.  Please be patient and check back after each release for updates.

## &raquo; Road to Version 1.0

!!! important
    All core features are in process of being tested for final validation for the upcoming **v1.0** release.  Bug fixes and related updates will continue to be published on a rapid pace as this milestone approaches.  Post the major release a more modest release schedule will be adopted and shared via this page.

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
    - Branding customizations - **COMPLETE** *v0.7.2*
    - Syntax highlighting - **COMPLETE** *v0.8.0*

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
    - Trino/PrestoSQL connector - **COMPLETE** *v0.9.4*

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
    - AWS (Lambda Layer) - [**Instructions**](installation/aws.md)

## Future Thinking

As no good tool is ever truly complete please find below the scratch-pad of features that will be considered for releases after v1.0.

- Sensitive Data Masking (Column-level masking)
- Record-level filtering
- Integrated Intellisense
- SQL Autocomplete
- Microsoft SQL Server
- IBM DB2 (LUW)
- Result download options for CSV, XML, JSON, etc.

!!! note "Help Build Query Commander's Roadmap"
    **GET INVOLVED:** You can help develop the roadmap and set priority on future enhancements and features.  Join in the [discussion](https://github.com/lnxusr1/query-commander/discussions) on [Github](https://github.com/lnxusr1/query-commander/discussions).
