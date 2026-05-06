locals {
  # ---------------------------------------------------------------------------
  # DevOps dashboard – Lambda health metrics and error log queries
  # ---------------------------------------------------------------------------
  devops_dashboard_body = jsonencode({
    widgets = [
      # Row 1 — Invocations (left) | Errors (right)
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Lambda Invocations"
          region  = data.aws_region.current.region
          view    = "timeSeries"
          stacked = false
          period  = 300
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", module.unlock_s3_bucket_lambda.lambda_function_name, { stat = "Sum", label = "unlock_s3_bucket" }],
            ["AWS/Lambda", "Invocations", "FunctionName", module.unlock_sqs_queue_lambda.lambda_function_name, { stat = "Sum", label = "unlock_sqs_queue" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Lambda Errors"
          region  = data.aws_region.current.region
          view    = "timeSeries"
          stacked = false
          period  = 300
          metrics = [
            ["AWS/Lambda", "Errors", "FunctionName", module.unlock_s3_bucket_lambda.lambda_function_name, { stat = "Sum", color = "#d62728", label = "unlock_s3_bucket" }],
            ["AWS/Lambda", "Errors", "FunctionName", module.unlock_sqs_queue_lambda.lambda_function_name, { stat = "Sum", color = "#ff7f0e", label = "unlock_sqs_queue" }]
          ]
        }
      },
      # Row 2 — Duration (left) | Throttles (right)
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "Lambda Duration (ms)"
          region  = data.aws_region.current.region
          view    = "timeSeries"
          stacked = false
          period  = 300
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", module.unlock_s3_bucket_lambda.lambda_function_name, { stat = "Maximum", label = "unlock_s3_bucket max" }],
            ["AWS/Lambda", "Duration", "FunctionName", module.unlock_s3_bucket_lambda.lambda_function_name, { stat = "Average", label = "unlock_s3_bucket avg" }],
            ["AWS/Lambda", "Duration", "FunctionName", module.unlock_sqs_queue_lambda.lambda_function_name, { stat = "Maximum", label = "unlock_sqs_queue max" }],
            ["AWS/Lambda", "Duration", "FunctionName", module.unlock_sqs_queue_lambda.lambda_function_name, { stat = "Average", label = "unlock_sqs_queue avg" }]
          ]
          annotations = {
            horizontal = [
              {
                label = "Timeout threshold"
                value = var.lambda_duration_threshold_ms
                color = "#ff0000"
              }
            ]
          }
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "Lambda Throttles"
          region  = data.aws_region.current.region
          view    = "timeSeries"
          stacked = false
          period  = 300
          metrics = [
            ["AWS/Lambda", "Throttles", "FunctionName", module.unlock_s3_bucket_lambda.lambda_function_name, { stat = "Sum", label = "unlock_s3_bucket" }],
            ["AWS/Lambda", "Throttles", "FunctionName", module.unlock_sqs_queue_lambda.lambda_function_name, { stat = "Sum", label = "unlock_sqs_queue" }]
          ]
        }
      },
      # Row 3 — Concurrent executions (left) | Alarm status (right)
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title   = "Lambda Concurrent Executions"
          region  = data.aws_region.current.region
          view    = "timeSeries"
          stacked = false
          period  = 300
          metrics = [
            ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", module.unlock_s3_bucket_lambda.lambda_function_name, { stat = "Maximum", label = "unlock_s3_bucket" }],
            ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", module.unlock_sqs_queue_lambda.lambda_function_name, { stat = "Maximum", label = "unlock_sqs_queue" }]
          ]
        }
      },
      {
        type   = "alarm"
        x      = 12
        y      = 12
        width  = 12
        height = 6
        properties = {
          title = "Alarm Status"
          alarms = [
            aws_cloudwatch_metric_alarm.unlock_s3_bucket_errors.arn,
            aws_cloudwatch_metric_alarm.unlock_s3_bucket_throttles.arn,
            aws_cloudwatch_metric_alarm.unlock_s3_bucket_duration.arn,
            aws_cloudwatch_metric_alarm.unlock_sqs_queue_errors.arn,
            aws_cloudwatch_metric_alarm.unlock_sqs_queue_throttles.arn,
            aws_cloudwatch_metric_alarm.unlock_sqs_queue_duration.arn
          ]
        }
      },
      # Row 4 — Recent errors from both log groups
      {
        type   = "log"
        x      = 0
        y      = 18
        width  = 12
        height = 9
        properties = {
          title         = "Recent S3 Unlock Lambda Errors"
          region        = data.aws_region.current.region
          view          = "table"
          logGroupNames = [module.unlock_s3_bucket_lambda.cloudwatch_log_group_name]
          query         = "fields @timestamp, level, message, account_id, bucket_name\n| filter level = \"ERROR\"\n| sort @timestamp desc\n| limit 50"
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 18
        width  = 12
        height = 9
        properties = {
          title         = "Recent SQS Unlock Lambda Errors"
          region        = data.aws_region.current.region
          view          = "table"
          logGroupNames = [module.unlock_sqs_queue_lambda.cloudwatch_log_group_name]
          query         = "fields @timestamp, level, message, account_id, queue_name\n| filter level = \"ERROR\"\n| sort @timestamp desc\n| limit 50"
        }
      }
    ]
  })

  # ---------------------------------------------------------------------------
  # Product Owner dashboard – business-level unlock statistics
  # Adjust the dashboard time range to control the reporting period.
  # ---------------------------------------------------------------------------
  product_owner_dashboard_body = jsonencode({
    widgets = [
      # Title
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 3
        properties = {
          markdown = "# AWS Root Access Management – Unlock Statistics\nThis dashboard shows **S3 bucket** and **SQS queue** unlock activity performed via root-access management, broken down by AWS account and time. Use the time-range selector (top-right) to change the reporting window (e.g. last 30 days for monthly figures)."
        }
      },
      # Row 1 — Daily totals (S3 left | SQS right)
      {
        type   = "metric"
        x      = 0
        y      = 3
        width  = 12
        height = 6
        properties = {
          title   = "S3 Buckets Unlocked per Day (all accounts)"
          region  = data.aws_region.current.region
          view    = "timeSeries"
          stacked = false
          period  = 86400
          metrics = [
            [{ expression = "SUM(SEARCH('{AWSRootAccessManagement,AccountId} S3BucketUnlocked', 'Sum', 86400))", id = "total_s3", label = "S3 Buckets Unlocked", period = 86400 }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 3
        width  = 12
        height = 6
        properties = {
          title   = "SQS Queues Unlocked per Day (all accounts)"
          region  = data.aws_region.current.region
          view    = "timeSeries"
          stacked = false
          period  = 86400
          metrics = [
            [{ expression = "SUM(SEARCH('{AWSRootAccessManagement,AccountId} SQSQueueUnlocked', 'Sum', 86400))", id = "total_sqs", label = "SQS Queues Unlocked", period = 86400 }]
          ]
        }
      },
      # Row 2 — Per-account totals (S3 left | SQS right)
      {
        type   = "log"
        x      = 0
        y      = 9
        width  = 12
        height = 9
        properties = {
          title         = "S3 Buckets Unlocked per Account"
          region        = data.aws_region.current.region
          view          = "table"
          logGroupNames = [module.unlock_s3_bucket_lambda.cloudwatch_log_group_name]
          query         = "fields account_id, bucket_name\n| filter message = \"Bucket policy deleted successfully\"\n| stats count(*) as buckets_unlocked by account_id\n| sort by buckets_unlocked desc"
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 9
        width  = 12
        height = 9
        properties = {
          title         = "SQS Queues Unlocked per Account"
          region        = data.aws_region.current.region
          view          = "table"
          logGroupNames = [module.unlock_sqs_queue_lambda.cloudwatch_log_group_name]
          query         = "fields account_id, queue_name\n| filter message = \"Queue policy deleted successfully\"\n| stats count(*) as queues_unlocked by account_id\n| sort by queues_unlocked desc"
        }
      },
      # Row 3 — Per-account per-month breakdown (S3 left | SQS right)
      {
        type   = "log"
        x      = 0
        y      = 18
        width  = 12
        height = 9
        properties = {
          title         = "S3 Buckets Unlocked per Account per Month"
          region        = data.aws_region.current.region
          view          = "table"
          logGroupNames = [module.unlock_s3_bucket_lambda.cloudwatch_log_group_name]
          query         = "fields account_id, bucket_name, datefloor(@timestamp, 1mo) as month\n| filter message = \"Bucket policy deleted successfully\"\n| stats count(*) as buckets_unlocked by account_id, month\n| sort by month desc, buckets_unlocked desc"
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 18
        width  = 12
        height = 9
        properties = {
          title         = "SQS Queues Unlocked per Account per Month"
          region        = data.aws_region.current.region
          view          = "table"
          logGroupNames = [module.unlock_sqs_queue_lambda.cloudwatch_log_group_name]
          query         = "fields account_id, queue_name, datefloor(@timestamp, 1mo) as month\n| filter message = \"Queue policy deleted successfully\"\n| stats count(*) as queues_unlocked by account_id, month\n| sort by month desc, queues_unlocked desc"
        }
      }
    ]
  })
}

resource "aws_cloudwatch_dashboard" "devops" {
  dashboard_name = "DevOps-Lambda-Monitoring"
  dashboard_body = local.devops_dashboard_body
}

resource "aws_cloudwatch_dashboard" "product_owner" {
  dashboard_name = "ProductOwner-Unlock-Statistics"
  dashboard_body = local.product_owner_dashboard_body
}
