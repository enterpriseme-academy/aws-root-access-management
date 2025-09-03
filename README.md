# AWS Root Access Management API

This project provides a secure REST API for managing AWS root account credentials and S3 bucket policies using Lambda functions, API Gateway, and Terraform.

## Features

- **Unlock S3 Bucket**: Delete or view S3 bucket policy.
- **Create Root Login Profile**: Create a login profile for the root user.
- **Delete Root Login Profile**: Delete the root login profile and deactivate MFA devices.
- **API Key Protection**: All sensitive endpoints require an API key.
- **CORS Support**: Fully configured for browser-based access.
- **Access Logging**: API Gateway logs requests to CloudWatch.

## Architecture

- **Lambda Functions**:
  - `unlock_s3_bucket_lambda`: Handles GET (view policy) and POST (delete policy) for S3 buckets.
  - `create_root_login_profile_lambda`: Creates root login profile.
  - `delete_root_login_profile_lambda`: Deletes root login profile and deactivates MFA.

## Usage

### Prerequisites

- AWS CLI configured
- Terraform >= 1.0
- Permissions to create Lambda, IAM roles, CloudWatch logs

### Deploy

1. Clone the repository.
2. Run `terraform init` to initialize.
3. Run `terraform apply` to deploy all resources.

### Static Website

A simple static website is included in `simple-static-website/` for interacting with the API.

## Security

- All sensitive operations require an API key.
- Lambda functions use least-privilege IAM roles.
- CloudWatch logs are enabled for auditing.

## Troubleshooting

- For Lambda errors, check CloudWatch logs for debugging information.
