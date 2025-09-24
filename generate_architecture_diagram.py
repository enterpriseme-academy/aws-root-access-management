#!/usr/bin/env python3.13
"""
AWS Root Access Management - Architecture Diagram Generator
Creates network architecture diagrams using the Python diagrams library.
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.network import (
    ALB,
    Route53,
    VPC,
    PrivateSubnet,
    PublicSubnet,
    InternetGateway,
    Endpoint,  # VPC Endpoints
)
from diagrams.aws.security import CertificateManager, IAM
from diagrams.aws.storage import S3
from diagrams.aws.integration import SQS
from diagrams.aws.management import Organizations, CloudwatchLogs
from diagrams.aws.general import Users, General
from diagrams.onprem.client import Users as ClientUsers


def create_network_diagram():
    """Create the main network architecture diagram."""

    with Diagram(
        "AWS Root Access Management - Network Architecture",
        filename="aws_root_access_network_architecture",
        show=False,
        direction="TB",
        graph_attr={"fontsize": "14", "bgcolor": "white", "size": "20,16!"},
    ):

        # External users
        users = ClientUsers("External Clients\n(Browser/CLI)")

        # DNS Layer
        with Cluster("DNS Resolution"):
            route53 = Route53("Route 53\nHosted Zone")
            dns_record = Route53("ram.enterpriseme.academy\nA Record")

        # Main VPC
        with Cluster("Management Account VPC (us-east-1)"):

            # Public Subnets
            with Cluster("Public Subnets (Multi-AZ)"):
                alb = ALB("Application Load Balancer\nram.enterpriseme.academy")
                acm = CertificateManager("ACM Certificate\n*.enterpriseme.academy")

            # Private Subnets
            with Cluster("Private Subnets (Multi-AZ)"):
                lambda_s3 = Lambda("unlock_s3_bucket\nLambda")
                lambda_sqs = Lambda("unlock_sqs_queue\nLambda")
                lambda_create = Lambda("create_root_login_profile\nLambda")
                lambda_delete = Lambda("delete_root_login_profile\nLambda")

                lambdas = [lambda_s3, lambda_sqs, lambda_create, lambda_delete]

            # VPC Endpoints
            with Cluster("VPC Endpoints\n(Private AWS API Access)"):
                vpce_iam = Endpoint("IAM\n(Global)")
                vpce_sts = Endpoint("STS")
                vpce_s3_gw = Endpoint("S3\n(Gateway)")
                vpce_sqs = Endpoint("SQS")
                vpce_logs = Endpoint("CloudWatch\nLogs")

        # Member Accounts
        with Cluster("Multi-Region Member Accounts"):
            with Cluster("Account A"):
                s3_a = S3("S3 Buckets")
                sqs_a = SQS("SQS Queues")
                root_a = IAM("Root Principal")

            with Cluster("Account N"):
                s3_n = S3("S3 Buckets")
                sqs_n = SQS("SQS Queues")
                root_n = IAM("Root Principal")

        # Governance
        with Cluster("AWS Organizations"):
            scp = Organizations("Service Control Policy\nDeny Long-term Root Creds")

        # Traffic flows
        users >> Edge(label="HTTPS", style="bold") >> route53
        route53 >> dns_record >> alb
        acm >> Edge(style="dotted", label="TLS Cert") >> alb

        # ALB to Lambda routing
        alb >> Edge(label="/unlock-s3-bucket/*") >> lambda_s3
        alb >> Edge(label="/unlock-sqs-queue/*") >> lambda_sqs
        alb >> Edge(label="/create-root-login-profile/*") >> lambda_create
        alb >> Edge(label="/delete-root-login-profile/*") >> lambda_delete

        # Lambda to VPC Endpoints
        for lam in lambdas:
            lam >> Edge(label="sts:AssumeRoot", style="dashed") >> vpce_sts
            lam >> Edge(label="Logs", color="gray") >> vpce_logs

        lambda_s3 >> Edge(label="S3 API") >> vpce_s3_gw
        lambda_sqs >> Edge(label="SQS API") >> vpce_sqs
        lambda_create >> Edge(label="IAM API") >> vpce_iam
        lambda_delete >> Edge(label="IAM API") >> vpce_iam

        # Cross-account access
        (
            vpce_sts
            >> Edge(label="Temp Root Sessions", style="dashed", color="red")
            >> [root_a, root_n]
        )

        # Resource access
        root_a >> [s3_a, sqs_a]
        root_n >> [s3_n, sqs_n]

        # Governance
        (
            scp
            >> Edge(label="Policy Enforcement", style="dotted", color="orange")
            >> [root_a, root_n]
        )


if __name__ == "__main__":
    print("Generating AWS Root Access Management architecture diagrams...")

    create_network_diagram()
    print(
        "✅ Network architecture diagram created: aws_root_access_network_architecture.png"
    )

    print("\n🎉 Diagram generated successfully!")
    print("File created in current directory:")
    print("- aws_root_access_network_architecture.png")
