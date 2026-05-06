# Observability – Lambda Monitoring, Alerting & Dashboards

This document describes the observability stack that monitors the `unlock_s3_bucket` and
`unlock_sqs_queue` Lambda functions. It covers:

- The **SNS alert topic** and which alarms publish to it
- The **DevOps dashboard** and how to interpret each widget
- The **Product Owner dashboard** and how to read the unlock statistics

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [SNS Alert Topic](#sns-alert-topic)
3. [CloudWatch Alarms](#cloudwatch-alarms)
4. [DevOps Dashboard – `DevOps-Lambda-Monitoring`](#devops-dashboard)
5. [Product Owner Dashboard – `ProductOwner-Unlock-Statistics`](#product-owner-dashboard)
6. [Custom Metrics (Log Metric Filters)](#custom-metrics)
7. [Configuration Variables](#configuration-variables)
8. [Runbook – Responding to Alerts](#runbook)

---

## Architecture Overview

```
Lambda executions
      │
      ├─ CloudWatch Metrics (AWS/Lambda namespace)
      │        └─ 6 CloudWatch Alarms
      │                 └──► SNS Topic: aws-root-access-lambda-alerts
      │                               └──► Email subscription (optional)
      │
      └─ CloudWatch Logs (/aws/lambda/<function>)
               ├─ Log Metric Filters → custom namespace AWSRootAccessManagement
               │         └─ Powers the Product Owner metric charts
               └─ Log Insights queries
                         └─ Powers per-account / per-month tables in both dashboards
```

---

## SNS Alert Topic

| Property | Value |
|---|---|
| **Topic name** | `aws-root-access-lambda-alerts` |
| **Purpose** | Centralised destination for all Lambda health alerts. Every alarm (ALARM state **and** OK recovery) publishes a notification here so the on-call team is aware of both the onset and resolution of any issue. |
| **Email subscription** | Created automatically when the `alert_email` Terraform variable is set. After `terraform apply`, confirm the subscription from the inbox of the configured address. |

> **Why both ALARM and OK actions?**  
> Receiving the OK notification closes the investigation loop without requiring manual CloudWatch checks.

---

## CloudWatch Alarms

All six alarms publish to the SNS topic above. Every failed Lambda execution must be investigated.

### `unlock_s3_bucket` alarms

| Alarm name | Metric | Condition | Meaning |
|---|---|---|---|
| `unlock_s3_bucket-errors` | `AWS/Lambda / Errors` | `Sum >= 1` in one period | The Lambda threw an unhandled exception or returned a non-zero error. Check CloudWatch Logs for the traceback. |
| `unlock_s3_bucket-throttles` | `AWS/Lambda / Throttles` | `Sum >= 1` in one period | Invocations are being rejected due to concurrency limits. Check if the compliance-dashboard is sending a burst of requests. |
| `unlock_s3_bucket-duration` | `AWS/Lambda / Duration` | `Maximum >= 25 000 ms` (configurable) | Execution time is approaching the 30-second timeout. Likely a slow `sts:AssumeRoot` or S3 API call; investigate network connectivity or AWS service health. |

### `unlock_sqs_queue` alarms

| Alarm name | Metric | Condition | Meaning |
|---|---|---|---|
| `unlock_sqs_queue-errors` | `AWS/Lambda / Errors` | `Sum >= 1` in one period | The Lambda threw an unhandled exception. Check CloudWatch Logs. |
| `unlock_sqs_queue-throttles` | `AWS/Lambda / Throttles` | `Sum >= 1` in one period | Concurrency limit reached. |
| `unlock_sqs_queue-duration` | `AWS/Lambda / Duration` | `Maximum >= 25 000 ms` (configurable) | Execution approaching timeout. |

> **Evaluation period** defaults to 60 seconds. Adjust with the `lambda_error_alarm_period` variable.

---

## DevOps Dashboard

**Name:** `DevOps-Lambda-Monitoring`  
**Audience:** DevOps / SRE engineers  
**Purpose:** Real-time health monitoring of both Lambda functions. Use this dashboard during on-call shifts and post-incident reviews.

Navigate to **CloudWatch → Dashboards → DevOps-Lambda-Monitoring**.

### Row 1 – Invocations & Errors

| Widget | What to look for |
|---|---|
| **Lambda Invocations** | Baseline call volume for both functions. Sudden spikes may indicate a compliance-dashboard retry storm. |
| **Lambda Errors** | Any non-zero value requires immediate investigation. Corresponds directly to the `errors` alarms above. |

### Row 2 – Duration & Throttles

| Widget | What to look for |
|---|---|
| **Lambda Duration (ms)** | Shows both `Average` and `Maximum` per function. The red horizontal annotation line marks the duration alarm threshold (default 25 000 ms). Values approaching the line indicate risk of timeout. |
| **Lambda Throttles** | Any non-zero value means invocations were rejected. Investigate concurrency limits or request rate. |

### Row 3 – Concurrency & Alarm Status

| Widget | What to look for |
|---|---|
| **Lambda Concurrent Executions** | Shows peak concurrent executions. Useful when diagnosing throttle events or planning reserved concurrency. |
| **Alarm Status** | Live traffic-light view of all six alarms. Green = OK, Red = ALARM. This is the fastest way to confirm all systems are healthy at a glance. |

### Row 4 – Error Log Tables

| Widget | What to look for |
|---|---|
| **Recent S3 Unlock Lambda Errors** | Log Insights table of the last 50 ERROR-level log entries for `unlock_s3_bucket`, showing timestamp, message, `account_id`, and `bucket_name`. Use to pinpoint which account/bucket triggered the failure. |
| **Recent SQS Unlock Lambda Errors** | Same for `unlock_sqs_queue`, showing `account_id` and `queue_name`. |

> **Tip:** Change the dashboard time-range (top-right selector) to narrow log results to the incident window.

---

## Product Owner Dashboard

**Name:** `ProductOwner-Unlock-Statistics`  
**Audience:** Product Owners, engineering managers  
**Purpose:** Business-level reporting on how many S3 buckets and SQS queues have been unlocked, broken down by AWS account and calendar month.

Navigate to **CloudWatch → Dashboards → ProductOwner-Unlock-Statistics**.

> **Tip:** Use the time-range selector (top-right) to change the reporting window, e.g. select **Last 30 days** for a monthly view or **Custom** to compare specific months.

### Description widget (Row 1)

A plain-text introduction to the dashboard. No interaction needed.

### Row 2 – Daily Totals (all accounts)

| Widget | How to read it |
|---|---|
| **S3 Buckets Unlocked per Day (all accounts)** | Time-series chart. Each data point represents the total number of S3 bucket policies deleted across **all** AWS accounts on that day. A flat zero line means no unlock activity occurred. A spike indicates elevated remediation activity. |
| **SQS Queues Unlocked per Day (all accounts)** | Same for SQS queues. |

These charts use the custom `AWSRootAccessManagement / S3BucketUnlocked` and `SQSQueueUnlocked` metrics and aggregate all `AccountId` dimension values using `SUM(SEARCH(...))`.

### Row 3 – Per-Account Totals

| Widget | How to read it |
|---|---|
| **S3 Buckets Unlocked per Account** | Table with columns `account_id` and `buckets_unlocked`, sorted descending. Shows which AWS accounts required the most S3 bucket unlocking within the selected time range. |
| **SQS Queues Unlocked per Account** | Same for SQS queues. |

These are Log Insights queries against the Lambda CloudWatch log groups, counting entries where the success message was logged.

### Row 4 – Per-Account per Month

| Widget | How to read it |
|---|---|
| **S3 Buckets Unlocked per Account per Month** | Table with columns `account_id`, `month`, and `buckets_unlocked`, sorted by most-recent month first. Use this to track month-over-month remediation trends per account. |
| **SQS Queues Unlocked per Account per Month** | Same for SQS queues. |

> **Log retention note:** The Lambda log groups retain logs for 14 days by default (`log_retention_days` variable in the Lambda module). Queries for older months will return no data once logs have expired. Increase `log_retention_days` if longer historical reporting is required.

---

## Custom Metrics

Two CloudWatch Log Metric Filters translate structured log entries into metrics in the
`AWSRootAccessManagement` namespace:

| Metric name | Log group | Filter pattern | Dimension |
|---|---|---|---|
| `S3BucketUnlocked` | `/aws/lambda/unlock_s3_bucket` | `{ $.message = "Bucket policy deleted successfully" }` | `AccountId` (extracted from `$.account_id` in the log JSON) |
| `SQSQueueUnlocked` | `/aws/lambda/unlock_sqs_queue` | `{ $.message = "Queue policy deleted successfully" }` | `AccountId` (extracted from `$.account_id` in the log JSON) |

Both Lambda functions emit a structured JSON log line containing `account_id` and the resource
name whenever a policy is successfully deleted. This field is required for the `AccountId`
dimension to be populated.

---

## Configuration Variables

Defined in `monitoring_variables.tf`:

| Variable | Default | Description |
|---|---|---|
| `alert_email` | `""` (no subscription) | Email address that receives SNS notifications. Set this to the on-call distribution list or PagerDuty email integration address. |
| `lambda_error_alarm_period` | `60` | Alarm evaluation window in seconds. Reduce to detect errors faster; increase to reduce noise from transient failures. |
| `lambda_duration_threshold_ms` | `25000` | Duration (ms) that triggers the duration alarm. Default is 25 s against a 30 s function timeout, giving a 5-second headroom. Adjust if the function timeout is changed. |

Example `terraform.tfvars`:

```hcl
alert_email                  = "oncall@example.com"
lambda_error_alarm_period    = 60
lambda_duration_threshold_ms = 25000
```

---

## Runbook

### Alert received: `unlock_*-errors`

1. Open **DevOps-Lambda-Monitoring** dashboard.
2. Set the time range to cover the alert window.
3. Check the **Recent … Lambda Errors** table (row 4) for the matching function.
4. Note the `account_id` and resource name from the log entry.
5. Open the CloudWatch Log Group (`/aws/lambda/<function_name>`) and filter for `level = ERROR` around the timestamp.
6. Review the full stack trace and `message` field.
7. Common causes:
   - `sts:AssumeRoot` failure → verify trust policy and root access management configuration in the target account.
   - S3/SQS API error → verify the bucket/queue exists and IAM permissions are correct.
   - Input validation error (400) → investigate the caller sending a malformed event.

### Alert received: `unlock_*-throttles`

1. Check **Lambda Concurrent Executions** widget to see the peak.
2. Investigate whether the compliance-dashboard is sending a retry burst.
3. Consider adding reserved concurrency or increasing limits via AWS Support.

### Alert received: `unlock_*-duration`

1. Check **Lambda Duration** widget; review the `Maximum` line trend.
2. Check AWS Service Health Dashboard for STS, S3, or SQS service events in the deployed region.
3. If no AWS service issue, review function logic for inefficiencies (e.g. unnecessary `get_bucket_policy` call before `delete_bucket_policy`).

### No data in Product Owner dashboard

- Ensure the dashboard time range covers a period when Lambda executions occurred.
- Confirm that log retention (`log_retention_days`) is long enough to cover the selected range.
- Verify that the Lambda functions are deployed and have been invoked at least once.
