# Configurations in ```settings.yml```

The configuraiton for Query Commander is managed by values specified in the ```settings.yml``` file.

This file can be located in any folder with the Environment Variable ```QRYCOMM_CONFIG_PATH```

``` shell
#!/bin/sh

export QRYCOMM_CONFIG_PATH="/path/to/config/folder"
```

## Sections

The settings file is broken up into sections as follows:

| Section | Description |
| :------ | :---------- |
| [**settings**](options.md) | Stores general settings and defaults for other sections |
| [**authenticator**](authenticator.md) | Authentication and Authorization options |
| [**profiler**](profiler.md) | User Profile storage (Local, DynamoDB) |
| [**tokenizer**](tokenizer.md) | Session token storage (Local, DynamoDB, Redis) |
| [**connections**](connections.md) | Connection list definition and connector options |

## Simple Example

Below is a simple example of a self-contained installation:

``` yaml
settings:
  records_per_request: 200

authenticator:
  type: local

profiler:
  type: local
  path: /tmp/profiles

tokenizer:
  type: local
  timeout: 20 
  safe_password: abc123456abcdef
  path: /tmp/tokens

connections:
  type: config
  items:
    - name: myconn1
      type: postgres
      host: my-db-server.lan
      port: 5432
```

## AWS Example

Below is an example for leveraging Active Directory and AWS options for the services:

``` yaml
settings:
  records_per_request: 200
  aws_region_name: us-east-1
  aws_access_key: your-access-key-here
  aws_secret_key: your-secret-key-here

authenticator:
    type: ldap
    host: your-microsoft-domain-server
    extra_args:
        version: 3
    options:
        use_ssl: true
        login_is_role: false
        base_dn: dc=example,dc=com
        user_search_filter: (&(objectClass=user)(aAMAccountName={USERNAME}))

profiler:
  type: dynamodb
  table: profiles

tokenizer:
  type: dynamodb
  timeout: 20
  safe_password: abc123456abcdef
  table: session_tokens

connections:
  type: secretsmanager
  filters:
    - Key: name
      Values:
        - secret-group-name
```