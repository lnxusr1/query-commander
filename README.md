# Query Commander &middot; [![GitHub license](https://img.shields.io/github/license/lnxusr1/query-commander)](https://github.com/lnxusr1/query-commander/blob/master/LICENSE) ![Python Versions](https://img.shields.io/pypi/pyversions/yt2mp3.svg) ![Read the Docs](https://img.shields.io/readthedocs/query-commander) ![GitHub release (latest by date)](https://img.shields.io/github/v/release/lnxusr1/query-commander)

Introducing **Query Commander**, the *opensource* browser-based SQL tool designed for secure and efficient database management. 

![Basic Screenshot](https://github.com/lnxusr1/query-commander/blob/main/docs/images/screen_basic.png?raw=true)

## Features:

1. **Database Connectivity**
    - Support for multiple server connections and heterogeneous targets
    - Support for multiple database types:<br>
      *(Oracle, PostgreSQL, Redshift, MySQL, Trino/PrestoSQL, etc.)*

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
    - Syntax highlighting

6. **Enhanced Security**
    - Support for End-to-End Encryption
    - Multiple authentication options (Database login-based, LDAP/Active Directory)
    - Optional time-based rate limits for queries executed and/or total records retrieved by user
    - Advanced permissions management with "Persona proxies" and group-based authorization
    - Ideal for cloud-hosted and remote database server access
    - Support for AWS Secret Manager for secure credential storage and database server info

7. **Modern Hosting Options**
    - Traditional installation with CGI executions
    - Optional **Serverless** installation (AWS API Gateway, Lambda, S3, DynamoDB, and Secrets Manager)

## Installation

**&raquo; Check out** the [**Apache 2.x**](https://docs.querycommander.com/en/stable/installation/apache/) and [**AWS Lambda**](https://docs.querycommander.com/en/stable/installation/aws/) installation options.

#### General Installation

For local installations the easiest way to get started is to use pip as shown below:

``` shell
pip install querycommander
```

The above installs the basic software and only includes AWS integrations by default.  To install specific connectors or components use one or more of the following commands:

``` shell
# Database Connectors
pip install querycommander[postgres]
pip install querycommander[mysql]
pip install querycommander[oracle]
pip install querycommander[redshift]
pip install querycommander[trino]

# Other connectors
pip install querycommander[redis] # For Redis session token storage
pip install querycommander[ldap]  # For LDAP authentication

# Install everything in one command
pip install querycommander[all]
```

## Learn More

[Read the Documentation](https://docs.querycommander.com)
