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

## Environment Variable Overrides

The following environment variables can be used to override [settings](./options.md) at the paths indicated in the table below.

| ENV VAR                    | Setting                                  |
| :------------------------- | :--------------------------------------- |
| QRYCOMM_CONFIG_PATH        | Sets the path to the *setting.yml* containing folder |
| LOG_LEVEL                  | settings/log_level                       |
| APP_NAME                   | settings/application_name                |
| IMG_LOGIN_BG               | settings/img_login_bg                    |
| IMG_LOGO                   | settings/img_logo                        |
| IMG_LOGO_SM                | settings/img_logo_sm                     |
| IMG_FAVICON                | settings/img_favicon                     |
| RECORD_PER_REQUEST         | settings/records_per_request             |
| PROFILES                   | settings/profiles                        |
| RATE_LIMIT_RECORDS         | settings/rate_limit.records              |
| RATE_LIMIT_PERIOD          | settings/rate_limit.period               |
| JQUERY_URL                 | settings/cdns/jquery/url                 |
| FONTAWESOME_URL            | settings/cdns/fontawesome/url            |
| FONTAWESOME_INTEGRITY      | settings/cdns/fontawesome/integrity      |
| FONTAWESOME_CROSSORIGIN    | settings/cdns/fontawesome/crossorigin    |
| FONTAWESOME_REFERRERPOLICY | settings/cdns/fontawesome/referrerpolicy |
| CODEMIRROR                 | settings/codemirror                      |
| CODEMIRROR_CSS_URL         | settings/cdns/codemirror_css/url         |
| CODEMIRROR_CSS_INTEGRITY      | settings/cdns/codemirror_css/integrity      |
| CODEMIRROR_CSS_CROSSORIGIN    | settings/cdns/codemirror_css/crossorigin    |
| CODEMIRROR_CSS_REFERRERPOLICY | settings/cdns/codemirror_css/referrerpolicy |
| CODEMIRROR_JS_URL          | settings/cdns/codemirror_js/url          |
| CODEMIRROR_JS_INTEGRITY      | settings/cdns/codemirror_js/integrity      |
| CODEMIRROR_JS_CROSSORIGIN    | settings/cdns/codemirror_js/crossorigin    |
| CODEMIRROR_JS_REFERRERPOLICY | settings/cdns/codemirror_js/referrerpolicy |
| CODEMIRROR_SQL_URL         | settings/cdns/codemirror_sql/url         |
| CODEMIRROR_SQL_INTEGRITY      | settings/cdns/codemirror_sql/integrity      |
| CODEMIRROR_SQL_CROSSORIGIN    | settings/cdns/codemirror_sql/crossorigin    |
| CODEMIRROR_SQL_REFERRERPOLICY | settings/cdns/codemirror_sql/referrerpolicy |
| AWS_REGION_NAME            | settings/aws_region_name                 |
| AWS_PROFILE_NAME           | settings/aws_profile_name                |
| AWS_ACCESS_KEY             | settings/aws_access_key                  |
| AWS_SECRET_KEY             | settings/aws_secret_key                  |
| TOKENIZER_TYPE             | tokenizer/type                           |
| TOKENIZER_TIMEOUT          | tokenizer/timeout                        |
| TOKENIZER_SAFE_PASSWORD    | tokenizer/safe_password                  |
| TOKENIZER_PATH             | tokenizer/path                           |
| TOKENIZER_HOST             | tokenizer/host                           |
| TOKENIZER_PORT             | tokenizer/port                           |
| TOKENIZER_SSL              | tokenizer/options/ssl                    |
| TOKENIZER_TABLE            | tokenizer/table                          |
| CONNECTIONS_TYPE           | connections/type                         |
