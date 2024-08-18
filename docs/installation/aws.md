# AWS Cloud Installation

To use Query Commander with API Gateway + Lambda you must attach the Lambda to a VPC subnet.  Doing so may require additional configuration depending on your environment.

## Intial Setup

### Step 1: Create the Lambda Layer

It is recommending to use pip to set up the libraries on which query commander depends.  This is fairly easy to achieve using the following:

``` bash
# Create a directory for the installation
mkdir ./package  

# Install all the dependencies along with the core query commander
pip install \
    --platform manylinux2014_x86_64 \
    --target=./package \
    --implementation cp \
    --python-version 3.12 \
    --only-binary=:all: \
    --upgrade \
    querycommander[lambda]

cd ./package
zip -r ../package.zip *
```

Now go into AWS and upload the zip file just created as a new layer.  If you already have a layer you can upload the zip file as a new version on the existing layer.  Make sure to select the proper runtime (Python 3.11 and/or Python 3.12 are the recommended runtimes with x86_64 architecture)

### Step 2: Create the Lambda Function

1. Create a new function as "Author from Scratch".
2. Enter a function name of your choice
3. Select a runtime (Python 3.12 is recommended)
4. Select an architecture (x86_64 is recommended)
5. Under "Permissions / change default execution rule" select (or create) an execution role:
    - CloudWatch Required Permissions:
        - logs:CreateLogGroup
        - logs:CreateLogStream
        - logs:PutLogEvents
    - EC2 Network Permissions (required to connect Lambda to a VPC)
        - ec2:CreateNetworkInterface
        - ec2:DescribeNetworkInterfaces
        - ec2:DescribeSubnets
        - ec2:DeleteNetworkInterface
        - ec2:AssignPrivateIpAddresses
        - ec2:UnassignPrivateIpAddresses
    - Add other permissions you plan to use like DynamoDB or S3
6. Under "Advanced" check the box for "Enable VPC"
    - Select the desired VPC
    - Select the subnets to send traffic through (you need at least 2)
    - Select the security group(s)
7. Click **Create Function**

### Step 3: Create Env Variables in Function

1. Open the newly created function and choose *Configuration*
2. Select *Environment variables*
3. Click *Edit* on the Environment Variables list
4. Click *Add environment variable*
5. Enter the values:
    - Key: QRYCOMM_CONFIG_PATH
    - Value: /var/task
6. Click **Save**

### Step 4: Add Layer to Function

1. Open the function and choose *Code*
2. Scroll to the bottom and find the Layers section and click **Add Layer**
3. Select the *Custom Layer* option and then pick the layer created in Step 1
4. Click **Add** to add the layer to the function

### Step 5: Add a settings.yml file to Function

1. Open the function and choose *Code*
2. In the editor add a new file called *settings.yml* alongside the existing lambda_function.py file
3. In the *settings.yml* file specify the [configuration](../configuration/basic.md) as desired.

!!! note
    You can update the settings.yml at any time, but each time you change it you'll need to **Deploy** your function for the changes to take effect.

### Step 6: Create the Python Handler code

In the lambda_function.py file delete all the code and add the following:

``` python
import sys

sys.path.insert(0, '/opt')
from querycommander import start


def lambda_handler(event, context):
 
    #logging.error(str(event))

    return start.as_lambda(event, context)
```

Once complete, save and click **Deploy** to publish the latest version of your function.

### Step 7: Set up API Gateway to call your Lambda function

1. Navigate to the *API Gateway* section in the AWS Console
2. **Build** a new HTTP API
3. Create and configure integrations
    - Click **Add Integration** and select *Lambda* as the integration source
    - Check the *AWS Region* drop down to insure it's accurate
    - Select the Lambda function created in Step 2 above
    - In the *Version* option select **1.0** (The tool does not require AWS to infer responses)
    - Enter a name for your API and click **Next**
4. Configure Routes
    - Method: ANY
    - Resource Path:  /querycommander
    - Integration Target:  *&lt;Lambda Function from Step 2&gt;*
    - Click **Next**
5. Define Stages:  Leave the defaults as-is and click **Next**
6. Review options and click **Create**

## Making Lambda work in your VPC

Lambda can run inside a VPC, but when doing so it doesn't actually execute within the VPC itself.  It executes via a gateway that AWS sets up when you select Lambda to connect to the VPC.  This creates a problem because Lambda cannot send traffic over the VPC endpoint into your network and it traverse back out to the internet through a standard *Internet Gateway*.  So, to make that work you have to use a NAT gateway.  Here's the basic configuration.

1. Make sure your VPC has *at least two* fully private subnets that do not include an *Internet Gateway* in their routing table
2. Attach Lambda to the two fully private subnets
3. Place your NAT gateway in a public subnet (a subnet with a route table that has an *Internet Gateway* in it)
4. Set the default route of your private subnet to route traffic over to the NAT gateway in the public subnet.

Doing this allows Lambda to connect to devices inside your network while still being able to connect to AWS services like DynamoDB and S3.

![API Gateway Network Diagram](../images/aws_api_gtwy_network.png)

!!! note
    Any VPC Service Endpoints you create for AWS services should be in your public subnet and the NAT gateway will honor those and not send your internal AWS traffic over the public Internet.