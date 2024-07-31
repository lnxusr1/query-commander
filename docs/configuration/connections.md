# Connections

## Basic Setup

If using local authentication no credentials are required so the most basic example of connection configurations in the *settings.yml* file is as follows:

``` yaml
connections:
  myconn1:
    type: postgres
    host: my-db-server.lan
    port: 5432
  myconn2:
    type: postgres
    host: localhost
    port: 5432
```

This example sets up two postgres databases under the names *myconn1* and *myconn2* respectively.

If your connection requires additional options to be specified in the connector you can add those as name/value pairs as shown below:

``` yaml
connections:
  myconn1:
    type: postgres
    host: my-db-server.lan
    port: 5432
    options:
      sslmode: require
      application_name: querycommander
```

## Connectors

The libraries used in the built-in connectors are listed below:

| Database       | Connector              | Link                                               |
| :------------- | :--------------------- | :------------------------------------------------- |
| PostgreSQL     | psycopg 3.x            | [https://www.psycopg.org](https://www.psycopg.org) |
| AWS Redshift   | psycopg 3.x            | [https://www.psycopg.org](https://www.psycopg.org) |
| Oracle         | python-oracledb        | [https://oracle.github.io/python-oracledb/](https://oracle.github.io/python-oracledb/) |
| MySQL          | mysql-connector-python | [https://dev.mysql.com/doc/connector-python/en/](https://dev.mysql.com/doc/connector-python/en/) |