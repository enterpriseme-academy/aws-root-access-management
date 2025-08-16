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
- **API Gateway REST API**:
  - Endpoints:
    - `GET /prod/unlock-s3-bucket/{account_number}/{bucket_name}`: Get S3 bucket policy.
    - `POST /prod/unlock-s3-bucket/{account_number}/{bucket_name}`: Delete S3 bucket policy.
    - `POST /prod/create-root-login-profile/{account_number}`: Create root login profile.
    - `POST /prod/delete-root-login-profile/{account_number}`: Delete root login profile.
  - CORS enabled for all endpoints.
  - API Key required for all GET/POST endpoints.
- **CloudWatch Logging**: All API requests are logged for auditing.

## Usage

### Prerequisites

- AWS CLI configured
- Terraform >= 1.0
- Permissions to create Lambda, API Gateway, IAM roles, CloudWatch logs

### Deploy

1. Clone the repository.
2. Run `terraform init` to initialize.
3. Run `terraform apply` to deploy all resources.

### API Key

After deployment, your API key will be shown as a Terraform output:

```
root_access_api_key_value = xxxxxxxxxxxxxxxxx
```

**Include this key in all API requests:**

- Header: `x-api-key: <your-api-key-value>`

### Example API Calls

**Get S3 Bucket Policy**
```sh
curl -H "x-api-key: <your-api-key-value>" \
  https://<api-id>.execute-api.<region>.amazonaws.com/prod/unlock-s3-bucket/<account_number>/<bucket_name>
```

**Delete S3 Bucket Policy**
```sh
curl -X POST -H "x-api-key: <your-api-key-value>" \
  https://<api-id>.execute-api.<region>.amazonaws.com/prod/unlock-s3-bucket/<account_number>/<bucket_name>
```

**Create Root Login Profile**
```sh
curl -X POST -H "x-api-key: <your-api-key-value>" \
  https://<api-id>.execute-api.<region>.amazonaws.com/prod/create-root-login-profile/<account_number>
```

**Delete Root Login Profile**
```sh
curl -X POST -H "x-api-key: <your-api-key-value>" \
  https://<api-id>.execute-api.<region>.amazonaws.com/prod/delete-root-login-profile/<account_number>
```

### CORS

CORS is enabled for all endpoints. You can call the API from a browser-based static website.

### Logging

API Gateway logs all requests to CloudWatch under `/aws/apigateway/root-access-management-api-access`.

### Static Website

A simple static website is included in `simple-static-website/` for interacting with the API.

## Security

- All sensitive operations require an API key.
- Lambda functions use least-privilege IAM roles.
- CloudWatch logs are enabled for auditing.

## Troubleshooting

- For Lambda errors, check CloudWatch logs for debugging information.

## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.5.7 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 6.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 6.8.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_create_root_login_profile_lambda"></a> [create\_root\_login\_profile\_lambda](#module\_create\_root\_login\_profile\_lambda) | terraform-aws-modules/lambda/aws | 8.0.1 |
| <a name="module_delete_root_login_profile_lambda"></a> [delete\_root\_login\_profile\_lambda](#module\_delete\_root\_login\_profile\_lambda) | terraform-aws-modules/lambda/aws | 8.0.1 |
| <a name="module_unlock_s3_bucket_lambda"></a> [unlock\_s3\_bucket\_lambda](#module\_unlock\_s3\_bucket\_lambda) | terraform-aws-modules/lambda/aws | 8.0.1 |

## Resources

| Name | Type |
|------|------|
| [aws_api_gateway_account.account](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_account) | resource |
| [aws_api_gateway_api_key.root_access_api_key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_api_key) | resource |
| [aws_api_gateway_deployment.root_access_api](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_deployment) | resource |
| [aws_api_gateway_integration.create_root_login_profile](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_integration) | resource |
| [aws_api_gateway_integration.delete_root_login_profile](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_integration) | resource |
| [aws_api_gateway_integration.unlock_s3_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_integration) | resource |
| [aws_api_gateway_integration.unlock_s3_bucket_get](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_integration) | resource |
| [aws_api_gateway_integration.unlock_s3_bucket_options](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_integration) | resource |
| [aws_api_gateway_integration_response.unlock_s3_bucket_options](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_integration_response) | resource |
| [aws_api_gateway_method.create_root_login_profile_options](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_method) | resource |
| [aws_api_gateway_method.create_root_login_profile_post](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_method) | resource |
| [aws_api_gateway_method.delete_root_login_profile_options](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_method) | resource |
| [aws_api_gateway_method.delete_root_login_profile_post](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_method) | resource |
| [aws_api_gateway_method.unlock_s3_bucket_get](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_method) | resource |
| [aws_api_gateway_method.unlock_s3_bucket_options](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_method) | resource |
| [aws_api_gateway_method.unlock_s3_bucket_post](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_method) | resource |
| [aws_api_gateway_method_response.unlock_s3_bucket_options](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_method_response) | resource |
| [aws_api_gateway_resource.create_root_login_profile](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_resource) | resource |
| [aws_api_gateway_resource.create_root_login_profile_account](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_resource) | resource |
| [aws_api_gateway_resource.delete_root_login_profile](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_resource) | resource |
| [aws_api_gateway_resource.delete_root_login_profile_account](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_resource) | resource |
| [aws_api_gateway_resource.unlock_s3_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_resource) | resource |
| [aws_api_gateway_resource.unlock_s3_bucket_account](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_resource) | resource |
| [aws_api_gateway_resource.unlock_s3_bucket_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_resource) | resource |
| [aws_api_gateway_rest_api.root_access_api](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_rest_api) | resource |
| [aws_api_gateway_stage.prod](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_stage) | resource |
| [aws_api_gateway_usage_plan.root_access_usage_plan](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_usage_plan) | resource |
| [aws_api_gateway_usage_plan_key.root_access_usage_plan_key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_usage_plan_key) | resource |
| [aws_cloudwatch_log_group.api_gw_access_logs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_iam_role.apigw_cloudwatch_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy_attachment.apigw_cloudwatch](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_lambda_permission.create_root_login_profile](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_lambda_permission.delete_root_login_profile](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_lambda_permission.unlock_s3_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_stage_name"></a> [stage\_name](#input\_stage\_name) | n/a | `string` | `"prod"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_root_access_api_key_value"></a> [root\_access\_api\_key\_value](#output\_root\_access\_api\_key\_value) | n/a |
