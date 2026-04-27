variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Terraform = "true"
  }
}

variable "environment" {
  description = "Deployment environment (e.g. development, staging, production)"
  type        = string
  default     = ""
}

variable "compliance_dashboard_role_name" {
  description = "Name of the IAM role on the remote account that is allowed to invoke the Lambda functions"
  type        = string
  default     = "compliance-dashboard"
}

variable "compliance_dashboard_account_id" {
  description = "AWS account ID of the remote account whose compliance-dashboard IAM role will invoke the Lambda functions"
  type        = string
}
