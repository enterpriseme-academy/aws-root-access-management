variable "alert_email" {
  description = "Email address to receive Lambda failure alerts via SNS. Leave empty to skip email subscription."
  type        = string
  default     = ""
}

variable "lambda_error_alarm_period" {
  description = "Period in seconds for Lambda CloudWatch alarm evaluation windows"
  type        = number
  default     = 60
}

variable "lambda_duration_threshold_ms" {
  description = "Duration threshold in milliseconds that triggers the Lambda duration alarm (default: 25000ms for a 30s function timeout)"
  type        = number
  default     = 25000
}
