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
