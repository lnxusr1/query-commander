# Optional Configurations

The following is a list of optional values you can specify in the *settings.yml* file.

| Setting             | Default | Description                                                  |
| :------------------ | :------ | :----------------------------------------------------------- |
| log_level           | "info"  | Standard python logging levels (debug, info, error, etc.)    |
| records_per_request | 200     | Number of records returned in a single page request.         |
| profiles            | enable  | Enables/disables user profiles                               |
| application_name    | *None*  | Override for branding application name                       |
| codemirror          | enable  | Enables/disables the codemirror editor (uses plain textarea) |
| img_login_bg        | *None*  | Login page main backgroung image                             |
| img_logo            | *None*  | Image URL for main logo on login screen                      |
| img_logo_sm         | *None*  | Image URL for smaller logo (on app screen)                   |
| img_favicon         | *None*  | Browser "favicon" image                                      |
| aws_access_key      | *None*  | AWS Access Key for Key-based authentication to AWS services. |
| aws_secret_key      | *None*  | AWS Secret Key for Key-based authentication to AWS services. | 
| aws_profile_name    | *None*  | Name for Profile-based authentication to AWS services.       |
| aws_region_name     | *None*  | AWS Region Name                                              |
| web_socket          | *None*  | WSS:// path to Web Socket API (AWS Lambda runtime only)      |
| rate_limit          | *None*  | Record return rate limits (see **Rate Limits** section below) |
| cdns                | *None*  | CDNs used to customize location client libraries             |

## Example

``` yaml
settings:
  records_per_request: 200
  aws_region_name: us-east-1
```

## Rate Limits

As an enhanced security feature it is possible to limit the maximum number of rows returned over a period of time.  To set these values use the *settings* section as follows:

``` yaml
settings:
  rate_limit:
    records: 20000
    period: 10 # minutes
```

The example above will limit the maximum rows that can be downloaded to 20,000 records in any 10 minute timeframe.  This limit is regardless of the number of queries executed.

## CDNs

The CDNs used to pull the client libraries are configurable, but by default will pull from the public CDNs.

| CDN         | Description                                                | Version |
| :---------- | :--------------------------------------------------------- | :------ |
| jquery      | The [jQuery](https://www.jquery.com) JavaScript framework  | 6.5+    |
| fontawesome | The [FontAwesome](https://fontawesome.com/) icon library   | 3.7+    |
| codemirror  | The [CodeMirror](https://codemirror.net/) editor library   | 5.65+   |

### Default CDN Configuration

Examples of configuration is shown below with the default values for each.  To change just include in the settings file and modify as desired.  Any attributes other than the required *url* will be placed in the html as name=value pairs.

``` yaml
settings:
  cdns:
    fontawesome:
      url: https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css
      integrity: sha512-DTOQO9RWCH3ppGqcWaEA1BIZOC6xxalwEsw9c2QQeAIftl+Vegovlnee1c9QX4TctnWMn13TZye+giMm8e2LwA==
      crossorigin: anonymous
      referrerpolicy: no-referrer
    jquery:
      url: https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js
      integrity: sha512-v2CJ7UaYy4JwqLDIrZUI/4hqeoQieOmAZNXBeQyjo21dadnwR+8ZaIJVT8EE2iyI61OV8e6M8PP2/4hpQINQ/g==
      crossorigin: anonymous 
      referrerpolicy: no-referrer
    codemirror_css:
      url: https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/codemirror.min.css
      integrity: sha512-uf06llspW44/LZpHzHT6qBOIVODjWtv4MxCricRxkzvopAlSWnTf6hpZTFxuuZcuNE9CBQhqE0Seu1CoRk84nQ==
      crossorigin: anonymous 
      referrerpolicy: no-referrer
    codemirror_js:
      url: https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/codemirror.min.js
      integrity: sha512-8RnEqURPUc5aqFEN04aQEiPlSAdE0jlFS/9iGgUyNtwFnSKCXhmB6ZTNl7LnDtDWKabJIASzXrzD0K+LYexU9g==
      crossorigin: anonymous 
      referrerpolicy: no-referrer
    codemirror_sql:
      url: https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/mode/sql/sql.min.js
      integrity: sha512-JOURLWZEM9blfKvYn1pKWvUZJeFwrkn77cQLJOS6M/7MVIRdPacZGNm2ij5xtDV/fpuhorOswIiJF3x/woe5fw== 
      crossorigin: anonymous 
      referrerpolicy: no-referrer
```