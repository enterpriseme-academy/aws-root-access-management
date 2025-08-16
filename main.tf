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

resource "aws_api_gateway_resource" "unlock_s3_bucket" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  parent_id   = aws_api_gateway_rest_api.root_access_api.root_resource_id
  path_part   = "unlock-s3-bucket"
}

resource "aws_api_gateway_resource" "unlock_s3_bucket_account" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  parent_id   = aws_api_gateway_resource.unlock_s3_bucket.id
  path_part   = "{account_number}"
}

resource "aws_api_gateway_resource" "unlock_s3_bucket_bucket" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  parent_id   = aws_api_gateway_resource.unlock_s3_bucket_account.id
  path_part   = "{bucket_name}"
}

resource "aws_api_gateway_resource" "delete_root_login_profile" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  parent_id   = aws_api_gateway_rest_api.root_access_api.root_resource_id
  path_part   = "delete-root-login-profile"
}

resource "aws_api_gateway_resource" "delete_root_login_profile_account" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  parent_id   = aws_api_gateway_resource.delete_root_login_profile.id
  path_part   = "{account_number}"
}

resource "aws_api_gateway_resource" "create_root_login_profile" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  parent_id   = aws_api_gateway_rest_api.root_access_api.root_resource_id
  path_part   = "create-root-login-profile"
}

resource "aws_api_gateway_resource" "create_root_login_profile_account" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  parent_id   = aws_api_gateway_resource.create_root_login_profile.id
  path_part   = "{account_number}"
}

# Methods
resource "aws_api_gateway_method" "unlock_s3_bucket_post" {
  rest_api_id      = aws_api_gateway_rest_api.root_access_api.id
  resource_id      = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
  request_parameters = {
    "method.request.path.account_number" = true
    "method.request.path.bucket_name"    = true
  }
}

resource "aws_api_gateway_method" "delete_root_login_profile_post" {
  rest_api_id      = aws_api_gateway_rest_api.root_access_api.id
  resource_id      = aws_api_gateway_resource.delete_root_login_profile_account.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
  request_parameters = {
    "method.request.path.account_number" = true
  }
}

resource "aws_api_gateway_method" "create_root_login_profile_post" {
  rest_api_id      = aws_api_gateway_rest_api.root_access_api.id
  resource_id      = aws_api_gateway_resource.create_root_login_profile_account.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
  request_parameters = {
    "method.request.path.account_number" = true
  }
}

resource "aws_api_gateway_method" "unlock_s3_bucket_get" {
  rest_api_id      = aws_api_gateway_rest_api.root_access_api.id
  resource_id      = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
  request_parameters = {
    "method.request.path.account_number" = true
    "method.request.path.bucket_name"    = true
  }
}

resource "aws_api_gateway_method" "unlock_s3_bucket_options" {
  rest_api_id   = aws_api_gateway_rest_api.root_access_api.id
  resource_id   = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "delete_root_login_profile_options" {
  rest_api_id   = aws_api_gateway_rest_api.root_access_api.id
  resource_id   = aws_api_gateway_resource.delete_root_login_profile_account.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "create_root_login_profile_options" {
  rest_api_id   = aws_api_gateway_rest_api.root_access_api.id
  resource_id   = aws_api_gateway_resource.create_root_login_profile_account.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "delete_root_login_profile" {
  rest_api_id             = aws_api_gateway_rest_api.root_access_api.id
  resource_id             = aws_api_gateway_resource.delete_root_login_profile_account.id
  http_method             = aws_api_gateway_method.delete_root_login_profile_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.delete_root_login_profile_lambda.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration" "create_root_login_profile" {
  rest_api_id             = aws_api_gateway_rest_api.root_access_api.id
  resource_id             = aws_api_gateway_resource.create_root_login_profile_account.id
  http_method             = aws_api_gateway_method.create_root_login_profile_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.create_root_login_profile_lambda.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration" "unlock_s3_bucket" {
  rest_api_id             = aws_api_gateway_rest_api.root_access_api.id
  resource_id             = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method             = aws_api_gateway_method.unlock_s3_bucket_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.unlock_s3_bucket_lambda.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration" "unlock_s3_bucket_get" {
  rest_api_id             = aws_api_gateway_rest_api.root_access_api.id
  resource_id             = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method             = aws_api_gateway_method.unlock_s3_bucket_get.http_method
  integration_http_method = "POST" # Lambda proxy integration always uses POST
  type                    = "AWS_PROXY"
  uri                     = module.unlock_s3_bucket_lambda.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration" "unlock_s3_bucket_options" {
  rest_api_id             = aws_api_gateway_rest_api.root_access_api.id
  resource_id             = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method             = aws_api_gateway_method.unlock_s3_bucket_options.http_method
  type                    = "MOCK"
  integration_http_method = "OPTIONS"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "unlock_s3_bucket_options" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  resource_id = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method = aws_api_gateway_method.unlock_s3_bucket_options.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Headers" = true
  }
}

resource "aws_api_gateway_integration_response" "unlock_s3_bucket_options" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  resource_id = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method = aws_api_gateway_method.unlock_s3_bucket_options.http_method
  status_code = aws_api_gateway_method_response.unlock_s3_bucket_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
  }

  response_templates = {
    "application/json" = ""
  }
  depends_on = [aws_api_gateway_integration.unlock_s3_bucket_options]
}

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