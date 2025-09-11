module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.19.0"

  name = "vpc"
  cidr = "10.0.0.0/16"

  azs                = slice(data.aws_availability_zones.available.names, 0, 2)
  private_subnets    = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets     = ["10.0.101.0/24", "10.0.102.0/24"]
  enable_nat_gateway = false
  enable_vpn_gateway = false
  tags               = var.tags
}

resource "aws_security_group" "alb_sg" {
  name        = "alb-sg"
  description = "Security group for the ALB"
  vpc_id      = module.vpc.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "ingress_443" {
  security_group_id = aws_security_group.alb_sg.id
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

# VPC Endpoint for IAM and Lambda invoke
module "vpc_endpoint" {
  source  = "terraform-aws-modules/vpc/aws//modules/vpc-endpoints"
  version = "5.19.0"

  vpc_id                     = module.vpc.vpc_id
  create_security_group      = true
  security_group_name_prefix = "vpc-endpoints-"
  security_group_description = "VPC endpoint security group"
  security_group_rules = {
    ingress_https = {
      description = "HTTPS from VPC"
      cidr_blocks = [module.vpc.vpc_cidr_block]
    }
  }
  endpoints = {
    lambda = {
      service             = "lambda"
      private_dns_enabled = true
      subnet_ids          = module.vpc.private_subnets
      policy              = data.aws_iam_policy_document.lambda_endpoint_policy.json
    }
    sts = {
      service             = "sts"
      private_dns_enabled = true
      subnet_ids          = module.vpc.private_subnets
      policy              = data.aws_iam_policy_document.sts_endpoint_policy.json
    }
  }
  tags = var.tags
}

resource "aws_security_group" "vpc_endpoint_sg" {
  name        = "vpc-endpoint-sg"
  description = "Security group for the VPC endpoint"
  vpc_id      = module.vpc.vpc_id
  tags        = var.tags
}

resource "aws_vpc_security_group_ingress_rule" "https" {
  security_group_id = aws_security_group.vpc_endpoint_sg.id
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = module.vpc.vpc_cidr_block
}

resource "aws_vpc_security_group_egress_rule" "https" {
  security_group_id = aws_security_group.vpc_endpoint_sg.id
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = module.vpc.vpc_cidr_block
}

resource "aws_vpc_endpoint" "iam" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.iam"
  vpc_endpoint_type   = "Interface"
  policy              = data.aws_iam_policy_document.iam_endpoint_policy.json
  security_group_ids  = [aws_security_group.vpc_endpoint_sg.id]
  subnet_ids          = module.vpc.private_subnets
  private_dns_enabled = true
  tags = merge(
    var.tags,
    {
      Name = "vpc-endpoint-iam"
    }
  )
}
