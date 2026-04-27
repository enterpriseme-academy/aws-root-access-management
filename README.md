# AWS Root Access Management

This project provides functionality for performing specific, tightly‑scoped privileged root tasks (using short‑term `sts:AssumeRoot` sessions) and for recovering access to locked Amazon S3 buckets or Amazon SQS queues whose resource policies block all principals. The functionality is exposed through AWS Lambda functions that are invoked directly by an IAM role on a remote account.


## Features

- **Unlock S3 Bucket**: View (GET) or delete (POST) a bucket policy that unintentionally denies all access.
- **Unlock SQS Queue**: View (GET) or delete (POST) an SQS queue policy that unintentionally denies all access.


## Architecture

All Lambda functions are deployed inside a dedicated VPC, in private subnets, to prevent direct inbound access and to force traffic through controlled integration points. The Lambda functions are invoked directly by the `compliance-dashboard` IAM role on a designated remote account via cross-account Lambda invocation permissions.

### Multi‑Region Considerations
Unlock operations may need to target S3 buckets or SQS queues residing in multiple AWS Regions. The current baseline deploys Lambda functions only in the primary Region (us‑east‑1). Cross‑Region operations are performed via `sts:AssumeRoot` into member accounts and region‑specific service API calls. (If ultra‑low latency or Region isolation is required, you can extend by deploying a regional copy of this stack per Region.)

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

**Cross-Account Invocation**
- Lambda functions grant `lambda:InvokeFunction` permission to the `compliance-dashboard` IAM role on the configured remote account.
- The invoking role and remote account ID are both configurable via Terraform variables (`compliance_dashboard_role_name`, `compliance_dashboard_account_id`).

### Security Notes
- Privileged actions are constrained to short‑lived `sts:AssumeRoot` sessions; no long‑term root credentials are created or stored.
- Lambda functions are only invocable by the designated `compliance-dashboard` role on the specified remote account.
- Service Control Policy enforces no long‑term root credential usage in member accounts while allowing privileged tasks (referenced below).
- Ensure least‑privilege execution roles restrict actions only to required privileged task policies plus logging.

### Future Enhancements (Optional)
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

### Invoking the Lambda Functions

The Lambda functions accept a JSON event payload and are invoked directly via the AWS SDK or CLI from the `compliance-dashboard` role on the remote account.

- **Unlock S3 Bucket**
  - `{"account_id": "<accountNumber>", "bucket_name": "<bucketName>", "action": "GET"}` — View S3 bucket policy
  - `{"account_id": "<accountNumber>", "bucket_name": "<bucketName>", "action": "POST"}` — Delete S3 bucket policy
- **Unlock SQS Queue**
  - `{"account_id": "<accountNumber>", "queue_name": "<queueName>", "action": "GET"}` — View SQS queue policy
  - `{"account_id": "<accountNumber>", "queue_name": "<queueName>", "action": "POST"}` — Delete SQS queue policy


## Security

- Lambda functions use least‑privilege IAM roles (recommend auditing with IAM Access Analyzer & CloudTrail).
- CloudWatch logs are enabled for auditing (add Logs VPC endpoint for stricter egress control).
- Dedicated Service Control Policy denies use of long‑term root credentials while allowing `AssumeRoot` privileged sessions. See AWS docs on the `aws:CalledVia` / `aws:PrincipalArn` conditions and assumed-root session keys. [Reference](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-assumedroot)
- Consider adding: centralized alerting on privileged task invocations, and guardrail SCPs that scope which accounts can be targeted.



## Troubleshooting

- For Lambda errors, check CloudWatch logs for debugging information.
- If you receive access denied errors when invoking the Lambda, ensure the `compliance_dashboard_account_id` and `compliance_dashboard_role_name` variables are set correctly in Terraform.
