# Optional Configurations

The following is a list of optional values you can specify in the *settings.yml* file.

| Setting             | Default | Description                                                  |
| :------------------ | :------ | :----------------------------------------------------------- |
| records_per_request | 200     | Number of records returned in a single page request.         |
| aws_access_key      | *None*  | AWS Access Key for Key-based authentication to AWS services. |
| aws_secret_key      | *None*  | AWS Secret Key for Key-based authentication to AWS services. | 
| aws_profile_name    | *None*  | Name for Profile-based authentication to AWS services.       |
| aws_region_name     | *None*  | AWS Region Name                                              |
| rate_limit          | *None*  | Record return rate limits (see **Rate Limits** section below) |

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