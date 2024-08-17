# AWS Cloud Installation

*Work in progress*

NOTES:

1. Create the library package

``` bash
pip install \
    --platform manylinux2014_x86_64 \
    --target=package \
    --implementation cp \
    --python-version 3.11 \
    --only-binary=:all: \
    --upgrade \
    querycommander[all]
```

2. **Add ENV Var** in Lambda function for settings.yml
3. **Add settings.yml** to the Lambda function
4. **Update** code to call query commander
5. Adjust VPC routing/firewalls
6. Connect Lambda to VPC

``` python
import sys

sys.path.insert(0, '/opt')
from querycommander import start


def lambda_handler(event, context):
 
    #logging.error(str(event))

    return start.as_lambda(event, context)
```

7. Set up API gateway
8. Set up DynamoDB/S3
9. Test