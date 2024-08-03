# Connections

## Basic Setup

If using local authentication then no credentials are required so the most basic example of connection configurations in the *settings.yml* file is as follows:

``` yaml
connections:
  type: local
  items:
    - name: myconn1
      type: postgres
      host: my-db-server.lan
      port: 5432

    - name: myconn2
      type: postgres
      host: localhost
      port: 5432
```

This example creates two postgres database connections under the names *myconn1* and *myconn2* respectively.

!!! warning
    Make sure your connection **name** values are unique across *all* connections listed or else the application will use the *last* connection segment specified for the given name.

If your connection requires additional options to be specified in the connector you can add those as name/value pairs as shown below:

``` yaml
connections:
  type: local
  items:
    - name: myconn1
      type: postgres
      host: my-db-server.lan
      port: 5432
      options:
        sslmode: require
        application_name: querycommander
```

## Connecting User Groups to Connections

To tie user groups to connections when using authenticators like **LDAP** you must specify an additional "roles" key and list out the group(s) that should have access to the parent connection.  Additionally, username and password values must be set.

``` yaml
connections:
  type: local
  items:
    - name: myconn1
      type: postgres
      host: my-db-server.lan
      port: 5432
      username: mydblogin
      password: mydbpassword
      roles:
        - MyGroupNameHere
        - MySecondGroupNameHere

    - name: myconn2
      type: postgres
      host: localhost
      port: 5432
      username: mydblogin
      password: mydbpassword
      roles:
        - MyGroupNameHere
        - MyThirdGroupNameHere
```

## Using AWS Secrets Manager

You can link to AWS Secrets Manager with the following:

``` yaml
connections:
  type: secretsmanager
  prefix: secret-group-name
```

Additional options of *aws_access_key*, *aws_secret_key*, *aws_profile_name*, and *aws_region_name* are available for specifying here or they will default to values set in the global [settings](options.md).

The *prefix* can be specified to limit which secrets are referenced.  If specified then only secrets that match the prefix in their name will be pulled.

An example JSON entry in Secrets Manager is as follows:

``` json
{
  "name":"myconn2",
  "type":"mysql",
  "host":"localhost",
  "port":"3306",
  "username":"mydbusername",
  "password":"mydbpassword",
  "roles":["MyGroupNameHere","MySecondGroupNameHere"]
}
```
Settings and options follow the same pattern as stored in the settings.yml file, however they must be written in JSON when storing in AWS Secrets Manager.

Permissions for AWS Secrets Manager must include ListSecrets and GetSecretValue.  A simple example is shown below:

``` json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:ListSecrets"
            ],
            "Resource": "*"
        }
    ]
}
```

## Connectors

The libraries used in the built-in connectors are listed below:

| Database       | Connector              | Link                                               |
| :------------- | :--------------------- | :------------------------------------------------- |
| PostgreSQL     | psycopg 3.x            | [https://www.psycopg.org](https://www.psycopg.org) |
| AWS Redshift   | psycopg 3.x            | [https://www.psycopg.org](https://www.psycopg.org) |
| Oracle         | python-oracledb        | [https://oracle.github.io/python-oracledb/](https://oracle.github.io/python-oracledb/) |
| MySQL          | mysql-connector-python | [https://dev.mysql.com/doc/connector-python/en/](https://dev.mysql.com/doc/connector-python/en/) |

### Postgres / AWS Redshift

``` shell
pip install psycopg
```

``` yaml
type: postgres
```

### MySQL/MariaDB

``` shell
pip install mysql-connector-python
```

``` yaml
type: mysql
```
