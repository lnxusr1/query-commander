# Connections

Database connections can be specified in several different ways in the ```settings.yml``` file.

## Authentication Options

There are two main ways to specific login credentials to the database hosts.  The first is to simply use the end-user's credentials they supply when logging into the interface.  This is the *local* type that is specified in the [Authenticator](authenticator.md) section.

The second option is to specify static account credentials for the connection using *username*/*password* attributes and then use the *roles* lists to specify which end-user groups have access to the connection.  For **LDAP** connections these settings are required and the roles listing translates to user group names.  You'll need to use the netbios style friendly name and not the full distinguished name when specifying entries in the roles list (e.g. use "MyGroup" instead of "cn=MyGroup,ou=groups,dc=example,dc=com").

``` yaml
authenticator:
  type: local  # <-- determines how the end-user authenticates (local, openldap, microsoft)
  ...

connections:
  type: config  # <-- determines where the connections are stored (config, secretsmanager)
  ...
```

!!! reminder
    Authenticator types of anything other than ```local``` require that you specify **username**, **password**, and **roles** attributes on all connections.

## Using the Configuration File

Likely the easiest way to get started is to use the ```settings.yml``` file to specify connections directly.  This method handles everything internally and simply requires you to specify each connection as a list of dictionary items.

### &raquo; Simple Example
Here is an example of using a *local* [**authenticator**](authenticator.md) with a *config* list of **connections**.

``` yaml
authenticator:
  type: local  # <-- determines how the end-user authenticates
  ...

connections:
  type: config  # <-- determines where the connections are stored (config = settings.yml file)
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

### &raquo; Connection Attributes

| Attribute | Req'd | Type | Notes |
| :-------- | :---- | :--- | :----- |
| name      | Yes   | String | Name to display in sidebar for connection |
| type<br>&nbsp; | All<br>&nbsp; | String<br>&nbsp; | Specifies the type of connection as:<br>postgres, mysql, oracle, redshift |
| host      | All   | String | Host or IP address of the server or endpoint |
| port<br>&nbsp; | No<br>&nbsp; | Number<br>&nbsp; | The TCP port (1 - 65535) to initiation the<br>connection |
| database | redshift | String | **Redshift Only**: Name of database for connection |
| service_name | oracle | String | **Oracle Only**: Service Name for connection |
| databases | No | List | List of databases (or schemas) to display if present |
| options | No | Dictionary | Extra arguments to send to constructor |
| username<br>&nbsp; | *Auth<br>&nbsp; | String<br>&nbsp; | Username for connection.  **Req.** if using Authenticator<br> type other than *local*. |
| password<br>&nbsp; | *Auth<br>&nbsp; | String<br>&nbsp; | Password for connection.  **Req.** if using Authenticator<br> type other than *local*. |
| roles<br>&nbsp; | *Auth<br>&nbsp; | List<br>&nbsp; | List of group names with permission to use connection.<br> **Req.** if using Authenticator type other than *local*. |

!!! note 
    If using **local authenticator type** then credentials supplied by the end-user during login will be used for all connections *regardless* of any username/password values specified in the configuration file.

!!! warning
    Make sure your connection **name** values are unique across *all* connections listed or else the application will use the *last* connection segment specified for the given name.

If your connection requires additional options to be specified in the connector you can add those as name/value pairs as shown below:

``` yaml
connections:
  type: config
  items:
    - name: myconn1
      type: postgres
      host: my-db-server.lan
      port: 5432
      databases:
        - mydbname1
        - mydbname2
      options:
        sslmode: require
        application_name: querycommander
```

## Alternative Connection Configurations

### &raquo; OpenLDAP and Microsoft Active Directory
If you are using an authenticator type other than *local* (such as openldap or microsoft) then you will need to include the three additional attributes of **username**, **password**, and **roles** in your connections.  Here's what that would look like if we take the simple example from [above](connections.md#using-the-configuration-file) and expand on it:

``` yaml
authenticator:
  type: microsoft  # <-- determines how the end-user authenticates
  ...

connections:
  type: config  # <-- determines where the connections are stored (config = settings.yml file)
  items:
    - name: myconn1
      type: postgres
      host: my-db-server.lan
      port: 5432
      username: mydbuser
      password: mydbpass
      roles:
        - MyGroupName1
        - MyGroupName2
      options:
        sslmode: require

    - name: myconn2
      type: postgres
      host: localhost
      port: 5432
      username: mydbuser
      password: mydbpass
      roles:
        - MyGroupName1
        - MyGroupName3
      options:
        sslmode: require
```

### &raquo; Storing Connections in AWS Secrets Manager

One additional option to improve the security of your deployment is to store your database connections in a password value.  At present there is built-in support for using AWS Secrets Manager to store the connection details.  To leveral this you would change the **connections** *type* to **secretsmanager**.  You can also *optionally* filter for specific secrets using the filtering options provided by AWS in their [list_secrets](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager/client/list_secrets.html) API.

Here's a quick example of the ```settings.yml``` configuration:

``` yaml
connections:
  type: secretsmanager
  aws_region_name: us-east-1
  aws_access_key: your-access-key-here
  aws_secret_key: your-secret-key-here
  filters:
    - Key: name
      Values:
        - secret-group-name
```

If you want to list all secrets then omit the **filters** attribute in the example above.  Likewise, if you want to use your global [settings](basic.md) for pulling your AWS credentials (or rely on instance-style authentication) then you can omit the aws_* attributes.

Within AWS Secrets Manager the secret must be formated so that Query Commander can read it.  This requires permissions and value updates.

The secret values must be in JSON format and follow the structure below:
``` json
{
  "type":"mysql",
  "host":"localhost",
  "port":"3306",
  "username":"mydbusername",
  "password":"mydbpassword",
  "roles":["MyGroupName1","MySecondGroupName2"]
}
```

The same options listed at the top of this page are available, but they are specified in JSON syntax and stored inside the secret rather than in the settings configuration file.

!!! note
    When using AWS Secrets Manager the Secret Name is substituted for the Connection Name so you do not need to specify a "name" attribute separately in the JSON data.

!!! important
    You can override the **type** attribute of the connections using the Environment variable **CONNECTIONS_TYPE**.  Presently the only practical value for the environment variable is *secretsmanager* as the default is to use the *config* value.

Permissions for AWS Secrets Manager access to the Query Commander runtime must include **ListSecrets** and **GetSecretValue**.  A simple policy example is shown below:

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

| Database                                                | PyPy Module            | Version | 
| :------------------------------------------------------ | :--------------------- | :------ | 
| [PostgreSQL](https://github.com/tlocke/pg8000)                   | pg8000                | 1.31.2+  | 
| [AWS Redshift](https://github.com/tlocke/pg8000)                 | pg8000                | 1.31.2+  | 
| [Oracle](https://oracle.github.io/python-oracledb/)     | oracledb               | 2.3.0+  |
| [MySQL](https://dev.mysql.com/doc/connector-python/en/) | mysql-connector-python | 9.0.0+  |
| [Trino/Presto](https://github.com/trinodb/trino)        | trino | 0.329.0+ |

## Examples

### &raquo; Example For PostgreSQL Connection

``` yaml
connections:
  type: config
  items:
    - name: myconn1
      type: postgres
      host: my-postgresql-server
      port: 5439
      username: mydblogin
      password: mydbpassword
      options:
        sslmode: require
        application_name: querycommander
      roles:
        - MyGroup1
        - MyGroup2
```

### &raquo; Example For Redshift Connection

Note that Redshift requires a database be specified.

``` yaml
connections:
  type: config
  items:
    - name: myconn2
      type: redshift
      host: my-redshift-server.amazonaws.com
      port: 5439
      username: mydblogin
      password: mydbpassword
      database: mydbname
      roles:
        - MyGroup1
        - MyGroup2
```

### &raquo; Example For MySQL &amp; MariaDB Connections

``` yaml
connections:
  type: config
  items:
    - name: myconn3
      type: mysql
      host: my-mysql-server-name
      port: 5439
      username: mydblogin
      password: mydbpassword
      roles:
        - MyGroup1
        - MyGroup2
```

### &raquo; Example For Oracle Connections

Note that oracle requires a service name be specified.

``` yaml
connections:
  type: config
  items:
    - name: myconn4
      type: oracle
      host: my-oracle-server-name
      port: 1521
      service_name: my_db_service_name
      username: mydblogin
      password: mydbpassword
      roles:
        - MyGroup1
        - MyGroup2
```

### &raquo; Example For Trino/Presto Connections

Note that Trino does not require authentication by default.  If you specify a password the tool will use HTTPS protocol and ```trino.auth.BasicAuthentication()```.

**No authentication**

``` yaml
connections:
  type: config
  items:
    - name: myconn4
      type: trino
      host: my-trino-server-name
      port: 8080
      username: admin
      roles:
        - MyGroup1
        - MyGroup2
```

**Basic Authentication**

``` yaml
connections:
  type: config
  items:
    - name: myconn4
      type: trino
      host: my-trino-server-name
      port: 8080
      username: admin
      password: mypassword
      roles:
        - MyGroup1
        - MyGroup2
```

**Basic Authentication + Disable SSL verification**

``` yaml
connections:
  type: config
  items:
    - name: myconn4
      type: trino
      host: my-trino-server-name
      port: 8080
      username: admin
      password: mypassword
      options:
        verify: false
      roles:
        - MyGroup1
        - MyGroup2
```