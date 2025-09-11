# main.tf for AWS Root Access Management module
resource "aws_lb" "main" {
  name               = "ram-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = module.vpc.public_subnets
  tags               = var.tags
}

resource "aws_lb_target_group" "unlock_sqs_queue" {
  name        = "unlock-sqs-queue-tg"
  target_type = "lambda"
  tags        = var.tags
}

resource "aws_lb_target_group_attachment" "unlock_sqs_queue" {
  target_group_arn = aws_lb_target_group.unlock_sqs_queue.arn
  target_id        = module.unlock_sqs_queue_lambda.lambda_function_arn
  depends_on       = [aws_lambda_permission.alb_unlock_sqs_queue]
}

resource "aws_lb_target_group" "unlock_s3_bucket" {
  name        = "unlock-s3-bucket-tg"
  target_type = "lambda"
  tags        = var.tags
}

resource "aws_lb_target_group_attachment" "unlock_s3_bucket" {
  target_group_arn = aws_lb_target_group.unlock_s3_bucket.arn
  target_id        = module.unlock_s3_bucket_lambda.lambda_function_arn
  depends_on       = [aws_lambda_permission.alb_unlock_s3_bucket]
}

resource "aws_lb_target_group" "delete_root_login_profile" {
  name        = "delete-root-login-profile-tg"
  target_type = "lambda"
  tags        = var.tags
}

resource "aws_lb_target_group_attachment" "delete_root_login_profile" {
  target_group_arn = aws_lb_target_group.delete_root_login_profile.arn
  target_id        = module.delete_root_login_profile_lambda.lambda_function_arn
  depends_on       = [aws_lambda_permission.alb_delete_root_login_profile]
}

resource "aws_lb_target_group" "create_root_login_profile" {
  name        = "create-root-login-profile-tg"
  target_type = "lambda"
  tags        = var.tags
}

resource "aws_lb_target_group_attachment" "create_root_login_profile" {
  target_group_arn = aws_lb_target_group.create_root_login_profile.arn
  target_id        = module.create_root_login_profile_lambda.lambda_function_arn
  depends_on       = [aws_lambda_permission.alb_create_root_login_profile]
}

# HTTPS listener using ACM module output
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = module.acm.acm_certificate_arn
  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "Not Found"
      status_code  = "404"
    }
  }
}

resource "aws_lb_listener_rule" "unlock_s3_bucket" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.unlock_s3_bucket.arn
  }
  condition {
    path_pattern {
      values = ["/unlock-s3-bucket/*"]
    }
  }
}

resource "aws_lb_listener_rule" "delete_root_login_profile" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 20
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.delete_root_login_profile.arn
  }
  condition {
    path_pattern {
      values = ["/delete-root-login-profile/*"]
    }
  }
}

resource "aws_lb_listener_rule" "create_root_login_profile" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 30
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.create_root_login_profile.arn
  }
  condition {
    path_pattern {
      values = ["/create-root-login-profile/*"]
    }
  }
}

resource "aws_lb_listener_rule" "unlock_sqs_queue" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 40
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.unlock_sqs_queue.arn
  }
  condition {
    path_pattern {
      values = ["/unlock-sqs-queue/*"]
    }
  }
}

# Lambda permissions for ALB invocation
resource "aws_lambda_permission" "alb_unlock_s3_bucket" {
  statement_id  = "AllowExecutionFromALB"
  action        = "lambda:InvokeFunction"
  function_name = module.unlock_s3_bucket_lambda.lambda_function_name
  principal     = "elasticloadbalancing.amazonaws.com"
  source_arn    = aws_lb_target_group.unlock_s3_bucket.arn
}

resource "aws_lambda_permission" "alb_unlock_sqs_queue" {
  statement_id  = "AllowExecutionFromALB"
  action        = "lambda:InvokeFunction"
  function_name = module.unlock_sqs_queue_lambda.lambda_function_name
  principal     = "elasticloadbalancing.amazonaws.com"
  source_arn    = aws_lb_target_group.unlock_sqs_queue.arn
}

resource "aws_lambda_permission" "alb_delete_root_login_profile" {
  statement_id  = "AllowExecutionFromALB"
  action        = "lambda:InvokeFunction"
  function_name = module.delete_root_login_profile_lambda.lambda_function_name
  principal     = "elasticloadbalancing.amazonaws.com"
  source_arn    = aws_lb_target_group.delete_root_login_profile.arn
}

resource "aws_lambda_permission" "alb_create_root_login_profile" {
  statement_id  = "AllowExecutionFromALB"
  action        = "lambda:InvokeFunction"
  function_name = module.create_root_login_profile_lambda.lambda_function_name
  principal     = "elasticloadbalancing.amazonaws.com"
  source_arn    = aws_lb_target_group.create_root_login_profile.arn
}

# ACM certificate for custom domain using module
module "acm" {
  source  = "terraform-aws-modules/acm/aws"
  version = "4.0.0"

  domain_name               = "ram.enterpriseme.academy"
  zone_id                   = "Z05127783I5U2J2XIK6J8"
  validation_method         = "DNS"
  create_route53_records    = true
  subject_alternative_names = []
  wait_for_validation       = true
  tags                      = var.tags
}

# Route 53 record for ALB
resource "aws_route53_record" "ram" {
  zone_id = "Z05127783I5U2J2XIK6J8"
  name    = "ram.enterpriseme.academy"
  type    = "A"
  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
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

  vpc_subnet_ids         = module.vpc.private_subnets
  vpc_security_group_ids = [aws_security_group.vpc_endpoint_sg.id]
  attach_network_policy  = true

  environment_variables = {
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
  tags = var.tags
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
  vpc_subnet_ids         = module.vpc.private_subnets
  vpc_security_group_ids = [aws_security_group.vpc_endpoint_sg.id]
  attach_network_policy  = true

  environment_variables = {
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
