# Roadmap

## What's next for Query Commander?

The roadmap is evolving!  Ideas currently on the list are included below.  If you'd like to submit a request or help guide Query Commander's roadmap then please join the [discussion](https://github.com/lnxusr1/query-commander/discussions):

- Visual Business Intelligence Reporting
    - Would have a centrally hosted interface for users to build/view reports
    - Would leverage Query Commander's SQL interface to post/retrieve results<br />
      *(Bypassing direct JDBC connections like Tableau)*
- Additional Connectors
    - Microsoft SQL Server
    - IBM DB2 (LUW/zOS)
- Sensitive Data Masking (Column-level masking)
    - This is available in some databases natively
    - The goal would be to uplift the API to expand this functionality to all databases
    - Requires heavy SQL parsing to reverse engineer the statements to determine root columns
    - Requires more storage for configuration of what rules to apply
    - Limits what SQL statements are accepted if feature is enabled
- Record-level filtering (Think "row-level security")
    - This is available at the database level for some databases.
    - The goal would be to filter rows in the API to uplift databases that don't natively support it.
    - Requires semi-detailed SQL parsing (table level) to be able to replace tables with subqueries.
    - Limits what SQL statements are accepted if feature is enabled
- Integrated Intellisense/Autocomplete
- Result download options for CSV, XLSX, XML, JSON, etc.

!!! note "Help Build Query Commander's Roadmap"
    **GET INVOLVED:** You can help develop the roadmap and set priority on future enhancements and features.  Join in the [discussion](https://github.com/lnxusr1/query-commander/discussions) on [Github](https://github.com/lnxusr1/query-commander/discussions).


## &raquo; Version 1.0 Major Features

Query Commander v1.0.0 was officially released on November 16, 2024 after many months of development and testing.  It supports CGI and AWS Lambda runtime environments leveraing Python versions up through 3.12.

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

