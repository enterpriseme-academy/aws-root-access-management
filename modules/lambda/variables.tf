variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "description" {
  description = "Description of the Lambda function"
  type        = string
  default     = ""
}

variable "handler" {
  description = "Lambda function handler (e.g. filename.method_name)"
  type        = string
}

variable "runtime" {
  description = "Lambda function runtime identifier"
  type        = string
}

variable "publish" {
  description = "Whether to publish creation/change as a new Lambda function version"
  type        = bool
  default     = false
}

variable "timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 3
}

variable "source_path" {
  description = "Path to the directory containing the Lambda source code"
  type        = string
}

variable "layers" {
  description = "List of Lambda layer ARNs to attach to the function"
  type        = list(string)
  default     = []
}

variable "environment_variables" {
  description = "Map of environment variables to set on the Lambda function"
  type        = map(string)
  default     = {}
}

variable "policy_statements" {
  description = "List of IAM policy statements to attach as an inline policy to the Lambda execution role"
  type = list(object({
    effect    = string
    actions   = list(string)
    resources = list(string)
  }))
  default = []
}

variable "tags" {
  description = "Tags to apply to all resources created by this module"
  type        = map(string)
  default     = {}
}
