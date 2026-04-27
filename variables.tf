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
