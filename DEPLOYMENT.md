# Deployment Guide for Prasha Care

This document outlines the deployment process for the Prasha Care application.

## CI/CD Pipeline

The application uses GitHub Actions for continuous integration and deployment:

1. When code is pushed to the `main` branch, the CI/CD pipeline automatically:
   - Builds a Docker image
   - Pushes the image to AWS ECR
   - Deploys the application to AWS Fargate

## AWS Resources

The application uses the following AWS resources:

- **ECR (Elastic Container Registry)**: Stores the Docker images
  - Repository: `prasha-api`
  - URI: `658304244296.dkr.ecr.us-east-1.amazonaws.com/prasha-api`

- **RDS (Relational Database Service)**: Hosts the PostgreSQL database
  - Endpoint: `mental-health-db.c0j84sqwazto.us-east-1.rds.amazonaws.com`
  - Database: `Prasha_care`
  - Username: `postgres`

## AWS Fargate Deployment

The application is deployed to AWS Fargate, which is a serverless compute engine for containers. The deployment process is as follows:

1. The Docker image is built and pushed to AWS ECR
2. A task definition is created with the latest image
3. The ECS service is updated with the new task definition
4. The application is accessible through an Application Load Balancer

## Manual Deployment

If you need to manually deploy the application:

1. Pull the latest image from ECR:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 658304244296.dkr.ecr.us-east-1.amazonaws.com
   docker pull 658304244296.dkr.ecr.us-east-1.amazonaws.com/prasha-api:latest
   ```

2. Run the container locally:
   ```bash
   docker run -d -p 8000:8000 \
     -e AWS_DB_USERNAME=postgres \
     -e AWS_DB_PASSWORD=Prashaind2025 \
     -e AWS_DB_HOST=mental-health-db.c0j84sqwazto.us-east-1.rds.amazonaws.com \
     -e AWS_DB_NAME=Prasha_care \
     -e SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7 \
     -e ACCESS_TOKEN_EXPIRE_MINUTES=30 \
     658304244296.dkr.ecr.us-east-1.amazonaws.com/prasha-api:latest
   ```

3. Deploy to AWS Fargate manually:
   ```bash
   # Register a new task definition
   aws ecs register-task-definition --cli-input-json file://task-definition.json

   # Update the service with the new task definition
   aws ecs update-service --cluster prasha-cluster --service prasha-service --task-definition prasha-api --force-new-deployment
   ```

## GitHub Secrets

The following secrets need to be configured in GitHub:

- `AWS_ACCESS_KEY_ID`: AWS access key with ECR and ECS permissions
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region (us-east-1)

## AWS IAM Permissions

The IAM user needs the following permissions:

- ECR permissions:
  - ecr:CreateRepository
  - ecr:GetAuthorizationToken
  - ecr:BatchCheckLayerAvailability
  - ecr:GetDownloadUrlForLayer
  - ecr:BatchGetImage
  - ecr:InitiateLayerUpload
  - ecr:UploadLayerPart
  - ecr:CompleteLayerUpload
  - ecr:PutImage

- ECS permissions:
  - ecs:CreateCluster
  - ecs:CreateService
  - ecs:RegisterTaskDefinition
  - ecs:UpdateService
  - ecs:DescribeServices
  - ecs:DescribeTasks
  - ecs:DescribeClusters

- EC2 permissions:
  - ec2:CreateSecurityGroup
  - ec2:AuthorizeSecurityGroupIngress
  - ec2:DescribeSecurityGroups
  - ec2:DescribeSubnets
  - ec2:DescribeVpcs

- ELB permissions:
  - elasticloadbalancing:CreateLoadBalancer
  - elasticloadbalancing:CreateTargetGroup
  - elasticloadbalancing:CreateListener
  - elasticloadbalancing:DescribeLoadBalancers
  - elasticloadbalancing:DescribeTargetGroups

## Troubleshooting

If you encounter issues with the deployment:

1. Check the GitHub Actions logs for any errors
2. Verify that the AWS credentials are correct
3. Ensure the IAM user has the necessary permissions
4. Check the AWS ECR repository to ensure the image was pushed correctly
