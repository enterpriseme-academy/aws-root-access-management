# SNS topic for Lambda failure alerts
resource "aws_sns_topic" "lambda_alerts" {
  name = "aws-root-access-lambda-alerts"
  tags = var.tags
}

resource "aws_sns_topic_subscription" "lambda_alerts_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.lambda_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# --- CloudWatch alarms: unlock_s3_bucket ---

resource "aws_cloudwatch_metric_alarm" "unlock_s3_bucket_errors" {
  alarm_name          = "unlock_s3_bucket-errors"
  alarm_description   = "Lambda function unlock_s3_bucket has errors - investigate immediately"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = var.lambda_error_alarm_period
  statistic           = "Sum"
  threshold           = 1
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = module.unlock_s3_bucket_lambda.lambda_function_name
  }

  alarm_actions = [aws_sns_topic.lambda_alerts.arn]
  ok_actions    = [aws_sns_topic.lambda_alerts.arn]
  tags          = var.tags
}

resource "aws_cloudwatch_metric_alarm" "unlock_s3_bucket_throttles" {
  alarm_name          = "unlock_s3_bucket-throttles"
  alarm_description   = "Lambda function unlock_s3_bucket is being throttled"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = var.lambda_error_alarm_period
  statistic           = "Sum"
  threshold           = 1
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = module.unlock_s3_bucket_lambda.lambda_function_name
  }

  alarm_actions = [aws_sns_topic.lambda_alerts.arn]
  ok_actions    = [aws_sns_topic.lambda_alerts.arn]
  tags          = var.tags
}

resource "aws_cloudwatch_metric_alarm" "unlock_s3_bucket_duration" {
  alarm_name          = "unlock_s3_bucket-duration"
  alarm_description   = "Lambda function unlock_s3_bucket duration is approaching timeout"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = var.lambda_error_alarm_period
  statistic           = "Maximum"
  threshold           = var.lambda_duration_threshold_ms
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = module.unlock_s3_bucket_lambda.lambda_function_name
  }

  alarm_actions = [aws_sns_topic.lambda_alerts.arn]
  ok_actions    = [aws_sns_topic.lambda_alerts.arn]
  tags          = var.tags
}

# --- CloudWatch alarms: unlock_sqs_queue ---

resource "aws_cloudwatch_metric_alarm" "unlock_sqs_queue_errors" {
  alarm_name          = "unlock_sqs_queue-errors"
  alarm_description   = "Lambda function unlock_sqs_queue has errors - investigate immediately"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = var.lambda_error_alarm_period
  statistic           = "Sum"
  threshold           = 1
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = module.unlock_sqs_queue_lambda.lambda_function_name
  }

  alarm_actions = [aws_sns_topic.lambda_alerts.arn]
  ok_actions    = [aws_sns_topic.lambda_alerts.arn]
  tags          = var.tags
}

resource "aws_cloudwatch_metric_alarm" "unlock_sqs_queue_throttles" {
  alarm_name          = "unlock_sqs_queue-throttles"
  alarm_description   = "Lambda function unlock_sqs_queue is being throttled"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = var.lambda_error_alarm_period
  statistic           = "Sum"
  threshold           = 1
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = module.unlock_sqs_queue_lambda.lambda_function_name
  }

  alarm_actions = [aws_sns_topic.lambda_alerts.arn]
  ok_actions    = [aws_sns_topic.lambda_alerts.arn]
  tags          = var.tags
}

resource "aws_cloudwatch_metric_alarm" "unlock_sqs_queue_duration" {
  alarm_name          = "unlock_sqs_queue-duration"
  alarm_description   = "Lambda function unlock_sqs_queue duration is approaching timeout"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = var.lambda_error_alarm_period
  statistic           = "Maximum"
  threshold           = var.lambda_duration_threshold_ms
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = module.unlock_sqs_queue_lambda.lambda_function_name
  }

  alarm_actions = [aws_sns_topic.lambda_alerts.arn]
  ok_actions    = [aws_sns_topic.lambda_alerts.arn]
  tags          = var.tags
}

# --- CloudWatch Log Metric Filters ---
# Emit a custom metric every time a bucket or queue policy is successfully deleted.
# The AccountId dimension enables per-account breakdowns in the Product Owner dashboard.
# Both Lambda functions log the account_id field at the top level of their structured
# JSON log entry when a policy is successfully deleted (see lambda_code/*/), which is
# required for the dimension extraction below to produce a value.

resource "aws_cloudwatch_log_metric_filter" "s3_bucket_unlocked" {
  name           = "s3-bucket-unlocked"
  pattern        = "{ $.message = \"Bucket policy deleted successfully\" }"
  log_group_name = module.unlock_s3_bucket_lambda.cloudwatch_log_group_name

  metric_transformation {
    name          = "S3BucketUnlocked"
    namespace     = "AWSRootAccessManagement"
    value         = "1"
    default_value = "0"
    dimensions = {
      AccountId = "$.account_id"
    }
  }
}

resource "aws_cloudwatch_log_metric_filter" "sqs_queue_unlocked" {
  name           = "sqs-queue-unlocked"
  pattern        = "{ $.message = \"Queue policy deleted successfully\" }"
  log_group_name = module.unlock_sqs_queue_lambda.cloudwatch_log_group_name

  metric_transformation {
    name          = "SQSQueueUnlocked"
    namespace     = "AWSRootAccessManagement"
    value         = "1"
    default_value = "0"
    dimensions = {
      AccountId = "$.account_id"
    }
  }
}
