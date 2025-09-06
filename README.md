# AWS Root Access Management API

This project provides a way for managing AWS root account credentials, S3 bucket policies, and SQS queue policies using Lambda functions behind an Application Load Balancer (ALB).


## Features

- **Unlock S3 Bucket**: Delete or view S3 bucket policy.
- **Unlock SQS Queue**: Delete or view SQS queue policy.
- **Create Root Login Profile**: Create a login profile for the root user.
- **Delete Root Login Profile**: Delete the root login profile and deactivate MFA devices.


## Architecture

- **Lambda Functions**:
  - `unlock_s3_bucket_lambda`: Handles GET (view policy) and POST (delete policy) for S3 buckets.
  - `unlock_sqs_queue_lambda`: Handles GET (view policy) and POST (delete policy) for SQS queues.
  - `create_root_login_profile_lambda`: Creates root login profile.
  - `delete_root_login_profile_lambda`: Deletes root login profile and deactivates MFA.

- **Application Load Balancer (ALB)**:
  - All Lambda functions are exposed via an internet-facing ALB.
  - Custom domain: `ram.enterpriseme.academy` (HTTPS supported).

## Usage

### Prerequisites

- AWS CLI configured
- Terraform >= 1.0
- Permissions to create Lambda, IAM roles, CloudWatch logs

### Deploy

1. Clone the repository.
2. Run `terraform init` to initialize.
3. Run `terraform apply` to deploy all resources.


### Endpoints (via ALB)

You can invoke the Lambda functions using the following endpoints:

- **Unlock S3 Bucket**
  - `GET  /unlock-s3-bucket/{accountNumber}/{bucketName}` — View S3 bucket policy
  - `POST /unlock-s3-bucket/{accountNumber}/{bucketName}` — Delete S3 bucket policy
- **Unlock SQS Queue**
  - `GET  /unlock-sqs-queue/{accountNumber}/{queueName}` — View SQS queue policy
  - `POST /unlock-sqs-queue/{accountNumber}/{queueName}` — Delete SQS queue policy
- **Delete Root Login Profile**
  - `POST /delete-root-login-profile/{accountNumber}`
- **Create Root Login Profile**
  - `POST /create-root-login-profile/{accountNumber}`

All endpoints are available at:

`https://ram.enterpriseme.academy/{path}`

### Static Website

A simple static website is included in `simple-static-website/` for interacting with the ALB endpoints.


## Security

- Lambda functions use least-privilege IAM roles.
- CloudWatch logs are enabled for auditing.


## Troubleshooting

- For Lambda errors, check CloudWatch logs for debugging information.
- If you receive 403 errors from the ALB, ensure Lambda permissions for ALB invocation are set correctly in Terraform.
