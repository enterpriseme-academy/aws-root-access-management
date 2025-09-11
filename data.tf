data "aws_region" "current" {}
data "aws_availability_zones" "available" {}

variable "org" {
  description = "The AWS Organization ID"
  type        = string
}

data "aws_iam_policy_document" "iam_endpoint_policy" {
  statement {
    effect    = "Allow"
    actions   = ["iam:*"]
    resources = ["*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:PrincipalOrgID"
      values   = [var.org]
    }
  }
}

data "aws_iam_policy_document" "lambda_endpoint_policy" {
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = ["*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:PrincipalOrgID"
      values   = [var.org]
    }
  }
}

data "aws_iam_policy_document" "sts_endpoint_policy" {
  statement {
    effect    = "Allow"
    actions   = ["sts:*"]
    resources = ["*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:PrincipalOrgID"
      values   = [var.org]
    }
  }
}
