# main.tf for AWS Root Access Management module

# Lambda permissions for invocation by the compliance-dashboard IAM role on the remote account
resource "aws_lambda_permission" "compliance_dashboard_unlock_s3_bucket" {
  statement_id  = "AllowExecutionFromComplianceDashboard"
  action        = "lambda:InvokeFunction"
  function_name = module.unlock_s3_bucket_lambda.lambda_function_name
  principal     = "arn:aws:iam::${var.compliance_dashboard_account_id}:role/${var.compliance_dashboard_role_name}"
}

resource "aws_lambda_permission" "compliance_dashboard_unlock_sqs_queue" {
  statement_id  = "AllowExecutionFromComplianceDashboard"
  action        = "lambda:InvokeFunction"
  function_name = module.unlock_sqs_queue_lambda.lambda_function_name
  principal     = "arn:aws:iam::${var.compliance_dashboard_account_id}:role/${var.compliance_dashboard_role_name}"
}

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

  vpc_subnet_ids         = module.vpc.private_subnets
  vpc_security_group_ids = [aws_security_group.vpc_endpoint_sg.id]
  attach_network_policy  = true

  environment_variables = {
    POWERTOOLS_SERVICE_NAME          = "S3UnlockBucketPolicy"
    POWERTOOLS_METRICS_FUNCTION_NAME = "S3UnlockBucketPolicy"
    POWERTOOLS_LOG_LEVEL             = "INFO"
    POWERTOOLS_METRICS_NAMESPACE     = "AWSRootAccessManagement"
    ENVIRONMENT                      = var.environment
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
  tags = var.tags
}

module "unlock_sqs_queue_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.0.1"

  function_name = "unlock_sqs_queue"
  description   = "Unlock SQS queue by deleting its policy"
  handler       = "unlock_sqs_queue.lambda_handler"
  runtime       = "python3.12"
  publish       = true
  timeout       = 30
  source_path   = "./lambda_code/unlock_sqs_queue_lambda"

  layers = [
    "arn:aws:lambda:${data.aws_region.current.region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-x86_64:19"
  ]

  vpc_subnet_ids         = module.vpc.private_subnets
  vpc_security_group_ids = [aws_security_group.vpc_endpoint_sg.id]
  attach_network_policy  = true

  environment_variables = {
    POWERTOOLS_SERVICE_NAME          = "SQSUnlockQueuePolicy"
    POWERTOOLS_METRICS_FUNCTION_NAME = "SQSUnlockQueuePolicy"
    POWERTOOLS_LOG_LEVEL             = "INFO"
    POWERTOOLS_METRICS_NAMESPACE     = "AWSRootAccessManagement"
    ENVIRONMENT                      = var.environment
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
  tags = var.tags
}
