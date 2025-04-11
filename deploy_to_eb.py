import boto3
import json
import time
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get AWS credentials from environment variables
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION')
aws_account_id = '658304244296'  # Your AWS account ID

print(f"Using AWS region: {aws_region}")

# Create Elastic Beanstalk client
eb_client = boto3.client(
    'elasticbeanstalk',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

# Create S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

# Application and environment names
application_name = 'prasha-api'
environment_name = 'prasha-api-env'
version_label = f'prasha-api-{int(time.time())}'

try:
    # Step 1: Check if application exists
    print("Step 1: Checking if application exists...")
    try:
        response = eb_client.describe_applications(ApplicationNames=[application_name])
        if response['Applications']:
            print(f"Application {application_name} already exists")
        else:
            raise Exception("Application not found")
    except Exception as e:
        print(f"Creating application {application_name}...")
        eb_client.create_application(
            ApplicationName=application_name,
            Description='Prasha Care API'
        )
        print(f"Application {application_name} created successfully")

    # Step 2: Create S3 bucket for application versions
    print("\nStep 2: Creating S3 bucket for application versions...")
    bucket_name = f"elasticbeanstalk-{aws_region}-{aws_account_id}"
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"S3 bucket {bucket_name} already exists")
    except Exception as e:
        print(f"Creating S3 bucket {bucket_name}...")
        if aws_region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': aws_region}
            )
        print(f"S3 bucket {bucket_name} created successfully")

    # Step 3: Upload Dockerrun.aws.json to S3
    print("\nStep 3: Uploading Dockerrun.aws.json to S3...")
    s3_key = f"{application_name}/{version_label}/Dockerrun.aws.json"
    s3_client.upload_file(
        'Dockerrun.aws.json',
        bucket_name,
        s3_key
    )
    print(f"Dockerrun.aws.json uploaded to s3://{bucket_name}/{s3_key}")

    # Step 4: Create application version
    print("\nStep 4: Creating application version...")
    eb_client.create_application_version(
        ApplicationName=application_name,
        VersionLabel=version_label,
        Description='Prasha Care API',
        SourceBundle={
            'S3Bucket': bucket_name,
            'S3Key': s3_key
        },
        AutoCreateApplication=False,
        Process=True
    )
    print(f"Application version {version_label} created successfully")

    # Step 5: Check if environment exists
    print("\nStep 5: Checking if environment exists...")
    try:
        response = eb_client.describe_environments(
            ApplicationName=application_name,
            EnvironmentNames=[environment_name]
        )
        if response['Environments']:
            print(f"Environment {environment_name} already exists, updating...")
            eb_client.update_environment(
                ApplicationName=application_name,
                EnvironmentName=environment_name,
                VersionLabel=version_label
            )
            print(f"Environment {environment_name} updated successfully")

            # Get environment URL
            environment_cname = response['Environments'][0]['CNAME']
            print(f"Environment URL: http://{environment_cname}")
        else:
            raise Exception("Environment not found")
    except Exception as e:
        print(f"Creating environment {environment_name}...")
        response = eb_client.create_environment(
            ApplicationName=application_name,
            EnvironmentName=environment_name,
            SolutionStackName='64bit Amazon Linux 2 v3.4.9 running Docker',
            VersionLabel=version_label,
            OptionSettings=[
                {
                    'Namespace': 'aws:autoscaling:launchconfiguration',
                    'OptionName': 'IamInstanceProfile',
                    'Value': 'aws-elasticbeanstalk-ec2-role'
                },
                {
                    'Namespace': 'aws:elasticbeanstalk:application:environment',
                    'OptionName': 'AWS_DB_USERNAME',
                    'Value': os.getenv('AWS_DB_USERNAME', 'postgres')
                },
                {
                    'Namespace': 'aws:elasticbeanstalk:application:environment',
                    'OptionName': 'AWS_DB_PASSWORD',
                    'Value': os.getenv('AWS_DB_PASSWORD', 'Prashaind2025')
                },
                {
                    'Namespace': 'aws:elasticbeanstalk:application:environment',
                    'OptionName': 'AWS_DB_HOST',
                    'Value': os.getenv('AWS_DB_HOST', 'mental-health-db.c0j84sqwazto.us-east-1.rds.amazonaws.com')
                },
                {
                    'Namespace': 'aws:elasticbeanstalk:application:environment',
                    'OptionName': 'AWS_DB_NAME',
                    'Value': os.getenv('AWS_DB_NAME', 'Prasha_care')
                },
                {
                    'Namespace': 'aws:elasticbeanstalk:application:environment',
                    'OptionName': 'SECRET_KEY',
                    'Value': os.getenv('SECRET_KEY', '09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7')
                },
                {
                    'Namespace': 'aws:elasticbeanstalk:application:environment',
                    'OptionName': 'ACCESS_TOKEN_EXPIRE_MINUTES',
                    'Value': os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30')
                }
            ]
        )

        # Get environment URL
        environment_cname = response['CNAME']
        print(f"Environment {environment_name} created successfully")
        print(f"Environment URL: http://{environment_cname}")

    print("\nDeployment complete!")
    print("Your application will be available at the Environment URL.")
    print("It may take a few minutes for the environment to be ready.")

except Exception as e:
    print(f"Error: {str(e)}")

    # Print what permissions are required
    print("\nRequired AWS permissions:")
    print("- elasticbeanstalk:CreateApplication")
    print("- elasticbeanstalk:CreateEnvironment")
    print("- elasticbeanstalk:DescribeApplications")
    print("- elasticbeanstalk:DescribeEnvironments")
    print("- elasticbeanstalk:UpdateEnvironment")
    print("- elasticbeanstalk:CreateApplicationVersion")
    print("- s3:CreateBucket")
    print("- s3:PutObject")
    print("- s3:GetObject")
    print("- s3:ListBucket")
