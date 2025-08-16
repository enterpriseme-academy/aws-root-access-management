import boto3
import os
import json
from aws_lambda_powertools import Logger

logger = Logger()

TARGET_POLICY_NAME = "IAMCreateRootUserPassword"
PROFILE_NAME = "sandbox"  # Used only for local testing


def get_boto3_session():
    if (
        os.environ.get("AWS_SAM_LOCAL") == "true"
        or os.environ.get("LOCAL_TEST") == "true"
    ):
        return boto3.Session(profile_name=PROFILE_NAME)
    else:
        return boto3.Session()


def assume_root(account_id, policy_name, duration_seconds=900):
    session = get_boto3_session()
    sts = session.client("sts")
    policy_arn = f"arn:aws:iam::aws:policy/root-task/{policy_name}"
    logger.info(f"Assuming policy: {policy_name} in account: {account_id}")
    resp = sts.assume_root(
        TargetPrincipal=account_id,
        TaskPolicyArn={"arn": policy_arn},
        DurationSeconds=duration_seconds,
    )
    creds = resp["Credentials"]
    return creds


def create_root_login_profile(account_id):
    creds = assume_root(account_id, TARGET_POLICY_NAME)
    # Use profile only if running locally (not in Lambda)
    if (
        os.environ.get("AWS_SAM_LOCAL") == "true"
        or os.environ.get("LOCAL_TEST") == "true"
    ):
        session = boto3.Session(
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
            profile_name=PROFILE_NAME,
        )
    else:
        session = boto3.Session(
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
        )
    iam = session.client("iam")

    # create root login profile
    try:
        iam.create_login_profile(UserName="root")
        logger.info("Root login profile created successfully.")
    except Exception as e:
        logger.error(f"Error creaing root login profile: {e}")
        raise


def lambda_handler(event, context):
    logger.info("Starting creating root login profile", extra={"event": event})
    account_id = event.get("pathParameters", {}).get("account_number")

    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    }

    if not account_id:
        logger.error("Missing account_number in path parameters")
        return {
            "statusCode": 400,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "status": "error",
                    "message": "Missing account_number in path parameters",
                }
            ),
        }
    try:
        create_root_login_profile(account_id)
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "status": "success",
                    "message": "Root login profile created.",
                }
            ),
        }
    except Exception as e:
        logger.error(f"Error creating root login profile: {e}")
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "status": "error",
                    "message": f"Error creating root login profile: {str(e)}",
                }
            ),
        }


if __name__ == "__main__":
    os.environ["LOCAL_TEST"] = "true"
    test_event = {}
    lambda_handler(test_event, None)
