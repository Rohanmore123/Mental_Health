# Setting Up GitHub Secrets

This document explains how to set up the required secrets for the CI/CD pipeline.

## Required Secrets

The following secrets need to be added to your GitHub repository:

1. `SECRET_KEY`: Your application's secret key for JWT token generation
2. `DOCKERHUB_USERNAME`: Your Docker Hub username
3. `DOCKERHUB_TOKEN`: Your Docker Hub access token (not your password)

## Steps to Add Secrets

1. Go to your GitHub repository
2. Click on "Settings" tab
3. In the left sidebar, click on "Secrets and variables" > "Actions"
4. Click on "New repository secret"
5. Add each of the required secrets:

### SECRET_KEY

- Name: `SECRET_KEY`
- Value: Your application's secret key (e.g., `09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7`)

### DOCKERHUB_USERNAME

- Name: `DOCKERHUB_USERNAME`
- Value: Your Docker Hub username

### DOCKERHUB_TOKEN

- Name: `DOCKERHUB_TOKEN`
- Value: Your Docker Hub access token

## Creating a Docker Hub Access Token

1. Log in to [Docker Hub](https://hub.docker.com/)
2. Click on your username in the top-right corner and select "Account Settings"
3. Click on "Security" in the left sidebar
4. Click on "New Access Token"
5. Give your token a name (e.g., "GitHub Actions")
6. Select the appropriate permissions (at minimum, "Read & Write")
7. Click "Generate"
8. Copy the token immediately (you won't be able to see it again)
9. Add this token as the `DOCKERHUB_TOKEN` secret in GitHub

## Deployment Secrets

If you're deploying to a server via SSH, you'll also need to add:

- `HOST`: Your server's hostname or IP address
- `USERNAME`: SSH username
- `SSH_KEY`: Your private SSH key

## Verifying Secrets

After adding all secrets, they should appear in your repository's secrets list (the actual values will be hidden).

Remember that these secrets are only accessible within GitHub Actions workflows and cannot be viewed or modified after creation. If you need to update a secret, you'll need to create a new one with the same name.
