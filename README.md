# AWS Root Access Management API

This project provides an API for performing specific, tightly‑scoped privileged root tasks (using short‑term `sts:AssumeRoot` sessions) and for recovering access to locked Amazon S3 buckets or Amazon SQS queues whose resource policies block all principals. The functionality is exposed through AWS Lambda functions integrated with an internet‑facing Application Load Balancer (ALB).


## Features

- **Unlock S3 Bucket**: View (GET) or delete (POST) a bucket policy that unintentionally denies all access.
- **Unlock SQS Queue**: View (GET) or delete (POST) an SQS queue policy that unintentionally denies all access.
- **Enable Root Password Creation**: Initiate the privileged task that (re)creates a root user password (maps to AWS IAM privileged task policy `IAMCreateRootUserPassword`).
- **Delete Root Credentials**: Remove root user password / access keys and deactivate MFA devices (maps to privileged task policy `IAMDeleteRootUserCredentials`).


## Architecture

All Lambda functions are deployed inside a dedicated VPC, in private subnets, to prevent direct inbound access and to force traffic through controlled integration points. An internet‑facing ALB provides HTTPS endpoints that invoke Lambda target groups (Lambda as ALB targets) without exposing the functions directly.

### Multi‑Region Considerations
Unlock operations may need to target S3 buckets or SQS queues residing in multiple AWS Regions. The current baseline deploys Lambda functions only in the primary Region (us‑east‑1). Cross‑Region operations are performed via `sts:AssumeRoot` into member accounts and region‑specific service API calls. (If ultra‑low latency or Region isolation is required, you can extend by deploying a regional copy of this stack per Region behind a global DNS / latency policy.)

### VPC Endpoints (Current)
Interface or gateway VPC endpoints eliminate the need for public internet egress for core AWS API calls:

- Lambda (`com.amazonaws.us-east-1.lambda`)
- IAM (global) (`com.amazonaws.iam`)
- STS (`com.amazonaws.us-east-1.sts`)
- SQS (`com.amazonaws.us-east-1.sqs`)
- S3 (Gateway) (`com.amazonaws.us-east-1.s3`)
- CloudWatch Logs (`com.amazonaws.us-east-1.logs`) – for log delivery without public routing.

### Supported (Target) Regions
- N. Virginia – us-east-1 (primary stack with Lambda functions)
- Ohio – us-east-2
- Ireland – eu-west-1
- London – eu-west-2
- Singapore – ap-southeast-1
- Jakarta – ap-southeast-3
- Mumbai – ap-south-1
- Hong Kong – ap-east-1
- Zurich – eu-central-2

### Components
**Lambda Functions**
- `unlock_s3_bucket_lambda`: GET (view policy), POST (delete policy)
- `unlock_sqs_queue_lambda`: GET (view policy), POST (delete policy)
- `create_root_login_profile_lambda`: Initiates privileged task to create/reset root password.
- `delete_root_login_profile_lambda`: Deletes root password/keys & deactivates MFA.

**Application Load Balancer**
- ALB terminating TLS (ACM certificate for `ram.enterpriseme.academy`).
- Listener rules route based on path prefixes to Lambda target groups.

### Security Notes
- Privileged actions are constrained to short‑lived `sts:AssumeRoot` sessions; no long‑term root credentials are created or stored.
- Implement AWS WAF (not yet included) on the ALB if exposed broadly to external users.
- Consider adding an IP allow list or authentication (e.g., signed headers, JWT at an API Gateway front) if usage should be restricted. ALB today provides unauthenticated public endpoints.
- Service Control Policy enforces no long‑term root credential usage in member accounts while allowing privileged tasks (referenced below).
- Ensure least‑privilege execution roles restrict actions only to required privileged task policies plus logging.

### Future Enhancements (Optional)
- Replace ALB + Lambda integration with Amazon API Gateway for built‑in auth, usage plans, throttling, and native Lambda proxy integration.
- Multi‑account deployment automation (e.g., via StackSets or delegated CI) for regional copies.
- Structured audit logging & tracing (Powertools + X-Ray) with correlation IDs.

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
- **Delete Root Credentials**
  - `POST /delete-root-login-profile/{accountNumber}`
- **Create/Reset Root Password**
  - `POST /create-root-login-profile/{accountNumber}`

All endpoints are available at:

`https://ram.enterpriseme.academy/{path}`

### Static Website

A simple static website is included in `simple-static-website/` for interacting with the ALB endpoints.


## Security

- Lambda functions use least‑privilege IAM roles (recommend auditing with IAM Access Analyzer & CloudTrail).
- CloudWatch logs are enabled for auditing (add Logs VPC endpoint for stricter egress control).
- Dedicated Service Control Policy denies use of long‑term root credentials while allowing `AssumeRoot` privileged sessions. See AWS docs on the `aws:CalledVia` / `aws:PrincipalArn` conditions and assumed-root session keys. [Reference](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-assumedroot)
- Consider adding: WAF ACL, centralized alerting on privileged task invocations, and guardrail SCPs that scope which accounts can be targeted.




## Troubleshooting

- For Lambda errors, check CloudWatch logs for debugging information.
- If you receive 403 errors from the ALB, ensure Lambda permissions for ALB invocation are set correctly in Terraform.
