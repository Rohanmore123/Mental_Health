import boto3
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get AWS credentials from environment variables
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION')

print(f"Using AWS region: {aws_region}")

# Create IAM client
iam_client = boto3.client(
    'iam',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

# Role name
role_name = 'ecsTaskExecutionRole'

# Trust policy for ECS
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

try:
    # Check if role exists
    try:
        iam_client.get_role(RoleName=role_name)
        print(f"Role {role_name} already exists")
    except iam_client.exceptions.NoSuchEntityException:
        # Create role if it doesn't exist
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for ECS task execution'
        )
        print(f"Role {role_name} created successfully")
        
        # Attach AmazonECSTaskExecutionRolePolicy
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy'
        )
        print(f"AmazonECSTaskExecutionRolePolicy attached to role {role_name}")
        
        # Attach AmazonECR-FullAccess
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/AmazonECR-FullAccess'
        )
        print(f"AmazonECR-FullAccess attached to role {role_name}")
    
    # Get role ARN
    role_response = iam_client.get_role(RoleName=role_name)
    role_arn = role_response['Role']['Arn']
    print(f"Role ARN: {role_arn}")
    
    print("\nECS task execution role setup complete!")
    print("You can now use this role ARN in your GitHub Actions workflow.")
    
except Exception as e:
    print(f"Error: {str(e)}")
    
    # Print what permissions are required
    print("\nRequired AWS permissions for IAM role creation:")
    print("- iam:CreateRole")
    print("- iam:GetRole")
    print("- iam:AttachRolePolicy")
    
    print("\nYou can use the IAMFullAccess policy for full access to IAM.")
