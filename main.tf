# main.tf for AWS Root Access Management module
data "aws_region" "current" {}

module "unlock_s3_bucket_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.0.1"

  function_name = "unlock_s3_bucket"
  description   = "Unlock S3 bucket by deleting its policy"
  handler       = "unlock_s3_bucket.lambda_handler"
  runtime       = "python3.12"
  publish       = true
  timeout       = 30
  source_path   = "./lambda_code/unlock_s3_bucket_lambda"

  layers = [
    "arn:aws:lambda:${data.aws_region.current.region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-x86_64:19"
  ]

  environment_variables = {
    SNS_TOPIC_ARN                    = "" # If you use this variable, set its value or remove if not needed
    POWERTOOLS_SERVICE_NAME          = "S3UnlockBucketPolicy"
    POWERTOOLS_METRICS_FUNCTION_NAME = "S3UnlockBucketPolicy"
    POWERTOOLS_LOG_LEVEL             = "INFO"
    POWERTOOLS_METRICS_NAMESPACE     = "AWSRootAccessManagement"
  }
  create_role              = true
  attach_policy_statements = true
  policy_statements = [
    {
      effect = "Allow"
      actions = [
        "sts:AssumeRoot"
      ]
      resources = [
        "*"
      ]
    }
  ]
}

module "delete_root_login_profile_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.0.1"

  function_name = "delete_root_login_profile"
  description   = "Delete root login profile"
  handler       = "delete_root_login_profile.lambda_handler"
  runtime       = "python3.12"
  publish       = true
  timeout       = 30
  source_path   = "./lambda_code/delete_root_login_profile_lambda"

  layers = [
    "arn:aws:lambda:${data.aws_region.current.region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-x86_64:19"
  ]

  environment_variables = {
    SNS_TOPIC_ARN                    = "" # If you use this variable, set its value or remove if not needed
    POWERTOOLS_SERVICE_NAME          = "IAMDeleteRootUserCredentials"
    POWERTOOLS_METRICS_FUNCTION_NAME = "IAMDeleteRootUserCredentials"
    POWERTOOLS_LOG_LEVEL             = "INFO"
    POWERTOOLS_METRICS_NAMESPACE     = "AWSRootAccessManagement"
  }
  create_role              = true
  attach_policy_statements = true
  policy_statements = [
    {
      effect = "Allow"
      actions = [
        "sts:AssumeRoot"
      ]
      resources = [
        "*"
      ]
    }
  ]
}

module "create_root_login_profile_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.0.1"

  function_name = "create_root_login_profile"
  description   = "Create root login profile"
  handler       = "create_root_login_profile.lambda_handler"
  runtime       = "python3.12"
  publish       = true
  timeout       = 30
  source_path   = "./lambda_code/create_root_login_profile_lambda"

  layers = [
    "arn:aws:lambda:${data.aws_region.current.region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-x86_64:19"
  ]

  environment_variables = {
    SNS_TOPIC_ARN                    = "" # If you use this variable, set its value or remove if not needed
    POWERTOOLS_SERVICE_NAME          = "IAMCreateRootUserPassword"
    POWERTOOLS_METRICS_FUNCTION_NAME = "IAMCreateRootUserPassword"
    POWERTOOLS_LOG_LEVEL             = "INFO"
    POWERTOOLS_METRICS_NAMESPACE     = "AWSRootAccessManagement"
  }
  create_role              = true
  attach_policy_statements = true
  policy_statements = [
    {
      effect = "Allow"
      actions = [
        "sts:AssumeRoot"
      ]
      resources = [
        "*"
      ]
    }
  ]
}

resource "aws_api_gateway_rest_api" "root_access_api" {
  name        = "root-access-management-api"
  description = "REST API for AWS Root Access Management"
}

# -----

resource "aws_lambda_permission" "unlock_s3_bucket" {
  statement_id  = "AllowAPIGatewayInvokeUnlockS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.unlock_s3_bucket_lambda.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.root_access_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "delete_root_login_profile" {
  statement_id  = "AllowAPIGatewayInvokeDeleteRootLoginProfile"
  action        = "lambda:InvokeFunction"
  function_name = module.delete_root_login_profile_lambda.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.root_access_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "create_root_login_profile" {
  statement_id  = "AllowAPIGatewayInvokeCreateRootLoginProfile"
  action        = "lambda:InvokeFunction"
  function_name = module.create_root_login_profile_lambda.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.root_access_api.execution_arn}/*/*"
}

# Access logging
resource "aws_cloudwatch_log_group" "api_gw_access_logs" {
  name              = "/aws/apigateway/root-access-management-api-access"
  retention_in_days = 30
}

resource "aws_api_gateway_deployment" "root_access_api" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.root_access_api.body))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "prod" {
  rest_api_id   = aws_api_gateway_rest_api.root_access_api.id
  stage_name    = "prod"
  deployment_id = aws_api_gateway_deployment.root_access_api.id

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gw_access_logs.arn
    format = jsonencode({
      requestId         = "$context.requestId"
      ip                = "$context.identity.sourceIp"
      requestTime       = "$context.requestTime"
      httpMethod        = "$context.httpMethod"
      resourcePath      = "$context.resourcePath"
      status            = "$context.status"
      protocol          = "$context.protocol"
      responseLength    = "$context.responseLength"
      integrationStatus = "$context.integrationStatus"
      errorMessage      = "$context.error.message"
    })
  }
}

variable "stage_name" {
  default = "prod"
  type    = string
}

resource "aws_iam_role" "apigw_cloudwatch_role" {
  name = "APIGatewayCloudWatchLogsRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "apigateway.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}
resource "aws_iam_role_policy_attachment" "apigw_cloudwatch" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
  role       = aws_iam_role.apigw_cloudwatch_role.id
}

resource "aws_api_gateway_account" "account" {
  cloudwatch_role_arn = aws_iam_role.apigw_cloudwatch_role.arn
}

resource "aws_api_gateway_api_key" "root_access_api_key" {
  name        = "RootAccessApiKey"
  description = "API Key for Root Access Management"
  enabled     = true
}

resource "aws_api_gateway_usage_plan" "root_access_usage_plan" {
  name = "RootAccessUsagePlan"
  api_stages {
    api_id = aws_api_gateway_rest_api.root_access_api.id
    stage  = aws_api_gateway_stage.prod.stage_name
  }
}

resource "aws_api_gateway_usage_plan_key" "root_access_usage_plan_key" {
  key_id        = aws_api_gateway_api_key.root_access_api_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.root_access_usage_plan.id
}

output "root_access_api_key_value" {
  value     = aws_api_gateway_api_key.root_access_api_key.value
  sensitive = true
}