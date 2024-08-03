# Optional Configurations

The following is a list of optional values you can specify in the *settings.yml* file.

| Setting             | Default | Description                                                  |
| :------------------ | :------ | :----------------------------------------------------------- |
| records_per_request | 200     | Number of records returned in a single page request.         |
| aws_access_key      | *None*  | AWS Access Key for Key-based authentication to AWS services. |
| aws_secret_key      | *None*  | AWS Secret Key for Key-based authentication to AWS services. | 
| aws_profile_name    | *None*  | Name for Profile-based authentication to AWS services.       |
| aws_region_name     | *None*  | AWS Region Name                                              |

## Example

``` yaml
settings:
  records_per_request: 200
  aws_region_name: us-east-1
```