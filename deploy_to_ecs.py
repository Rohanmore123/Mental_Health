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

print(f"Using AWS region: {aws_region}")

# Create ECS client
ecs_client = boto3.client(
    'ecs',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

# Create EC2 client
ec2_client = boto3.client(
    'ec2',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

# Create ELB client
elb_client = boto3.client(
    'elbv2',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

# Cluster name
cluster_name = 'prasha-cluster'
service_name = 'prasha-service'
task_definition_family = 'prasha-api'

try:
    # Step 1: Check if cluster exists
    print("Step 1: Checking if cluster exists...")
    try:
        response = ecs_client.describe_clusters(clusters=[cluster_name])
        if response['clusters'] and response['clusters'][0]['status'] == 'ACTIVE':
            print(f"Cluster {cluster_name} already exists")
        else:
            print(f"Creating cluster {cluster_name}...")
            ecs_client.create_cluster(clusterName=cluster_name)
            print(f"Cluster {cluster_name} created successfully")
    except Exception as e:
        print(f"Error checking cluster: {str(e)}")
        print(f"Creating cluster {cluster_name}...")
        ecs_client.create_cluster(clusterName=cluster_name)
        print(f"Cluster {cluster_name} created successfully")
    
    # Step 2: Register task definition
    print("\nStep 2: Registering task definition...")
    with open('task-definition.json', 'r') as f:
        task_definition = json.load(f)
    
    response = ecs_client.register_task_definition(**task_definition)
    task_definition_arn = response['taskDefinition']['taskDefinitionArn']
    print(f"Task definition registered: {task_definition_arn}")
    
    # Step 3: Get default VPC and subnets
    print("\nStep 3: Getting default VPC and subnets...")
    vpc_response = ec2_client.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
    vpc_id = vpc_response['Vpcs'][0]['VpcId']
    print(f"Default VPC: {vpc_id}")
    
    subnet_response = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    subnet_ids = [subnet['SubnetId'] for subnet in subnet_response['Subnets'][:2]]
    print(f"Subnets: {subnet_ids}")
    
    # Step 4: Create security group
    print("\nStep 4: Creating security group...")
    try:
        sg_response = ec2_client.describe_security_groups(
            Filters=[
                {'Name': 'group-name', 'Values': ['prasha-sg']},
                {'Name': 'vpc-id', 'Values': [vpc_id]}
            ]
        )
        if sg_response['SecurityGroups']:
            security_group_id = sg_response['SecurityGroups'][0]['GroupId']
            print(f"Security group already exists: {security_group_id}")
        else:
            raise Exception("Security group not found")
    except Exception as e:
        print(f"Creating new security group...")
        sg_response = ec2_client.create_security_group(
            GroupName='prasha-sg',
            Description='Security group for Prasha API',
            VpcId=vpc_id
        )
        security_group_id = sg_response['GroupId']
        
        # Add inbound rules
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8000,
                    'ToPort': 8000,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )
        print(f"Security group created: {security_group_id}")
    
    # Step 5: Create load balancer
    print("\nStep 5: Creating load balancer...")
    try:
        lb_response = elb_client.describe_load_balancers(Names=['prasha-lb'])
        load_balancer_arn = lb_response['LoadBalancers'][0]['LoadBalancerArn']
        load_balancer_dns = lb_response['LoadBalancers'][0]['DNSName']
        print(f"Load balancer already exists: {load_balancer_arn}")
    except Exception as e:
        print(f"Creating new load balancer...")
        lb_response = elb_client.create_load_balancer(
            Name='prasha-lb',
            Subnets=subnet_ids,
            SecurityGroups=[security_group_id],
            Scheme='internet-facing',
            Type='application',
            IpAddressType='ipv4'
        )
        load_balancer_arn = lb_response['LoadBalancers'][0]['LoadBalancerArn']
        load_balancer_dns = lb_response['LoadBalancers'][0]['DNSName']
        print(f"Load balancer created: {load_balancer_arn}")
    
    # Step 6: Create target group
    print("\nStep 6: Creating target group...")
    try:
        tg_response = elb_client.describe_target_groups(Names=['prasha-tg'])
        target_group_arn = tg_response['TargetGroups'][0]['TargetGroupArn']
        print(f"Target group already exists: {target_group_arn}")
    except Exception as e:
        print(f"Creating new target group...")
        tg_response = elb_client.create_target_group(
            Name='prasha-tg',
            Protocol='HTTP',
            Port=8000,
            VpcId=vpc_id,
            TargetType='ip',
            HealthCheckPath='/health',
            HealthCheckProtocol='HTTP',
            HealthCheckPort='8000',
            HealthCheckEnabled=True,
            HealthCheckIntervalSeconds=30,
            HealthCheckTimeoutSeconds=5,
            HealthyThresholdCount=2,
            UnhealthyThresholdCount=2
        )
        target_group_arn = tg_response['TargetGroups'][0]['TargetGroupArn']
        print(f"Target group created: {target_group_arn}")
    
    # Step 7: Create listener
    print("\nStep 7: Creating listener...")
    try:
        listener_response = elb_client.describe_listeners(LoadBalancerArn=load_balancer_arn)
        if listener_response['Listeners']:
            listener_arn = listener_response['Listeners'][0]['ListenerArn']
            print(f"Listener already exists: {listener_arn}")
        else:
            raise Exception("Listener not found")
    except Exception as e:
        print(f"Creating new listener...")
        listener_response = elb_client.create_listener(
            LoadBalancerArn=load_balancer_arn,
            Protocol='HTTP',
            Port=80,
            DefaultActions=[
                {
                    'Type': 'forward',
                    'TargetGroupArn': target_group_arn
                }
            ]
        )
        listener_arn = listener_response['Listeners'][0]['ListenerArn']
        print(f"Listener created: {listener_arn}")
    
    # Step 8: Create or update service
    print("\nStep 8: Creating or updating service...")
    try:
        service_response = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        if service_response['services'] and service_response['services'][0]['status'] != 'INACTIVE':
            print(f"Service {service_name} already exists, updating...")
            ecs_client.update_service(
                cluster=cluster_name,
                service=service_name,
                taskDefinition=task_definition_arn,
                forceNewDeployment=True
            )
            print(f"Service {service_name} updated successfully")
        else:
            raise Exception("Service not found or inactive")
    except Exception as e:
        print(f"Creating new service...")
        ecs_client.create_service(
            cluster=cluster_name,
            serviceName=service_name,
            taskDefinition=task_definition_arn,
            loadBalancers=[
                {
                    'targetGroupArn': target_group_arn,
                    'containerName': 'prasha-api',
                    'containerPort': 8000
                }
            ],
            desiredCount=1,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': subnet_ids,
                    'securityGroups': [security_group_id],
                    'assignPublicIp': 'ENABLED'
                }
            }
        )
        print(f"Service {service_name} created successfully")
    
    print("\nDeployment complete!")
    print(f"Your application will be available at: http://{load_balancer_dns}")
    print("It may take a few minutes for the service to start and the health checks to pass.")
    
except Exception as e:
    print(f"Error: {str(e)}")
    
    # Print what permissions are required
    print("\nRequired AWS permissions:")
    print("- ecs:CreateCluster")
    print("- ecs:CreateService")
    print("- ecs:RegisterTaskDefinition")
    print("- ecs:UpdateService")
    print("- ecs:DescribeServices")
    print("- ecs:DescribeTasks")
    print("- ecs:DescribeClusters")
    print("- ec2:CreateSecurityGroup")
    print("- ec2:AuthorizeSecurityGroupIngress")
    print("- ec2:DescribeSecurityGroups")
    print("- ec2:DescribeSubnets")
    print("- ec2:DescribeVpcs")
    print("- elasticloadbalancing:CreateLoadBalancer")
    print("- elasticloadbalancing:CreateTargetGroup")
    print("- elasticloadbalancing:CreateListener")
    print("- elasticloadbalancing:DescribeLoadBalancers")
    print("- elasticloadbalancing:DescribeTargetGroups")
    print("- elasticloadbalancing:DescribeListeners")
