import boto3
import os
import json
from aws_lambda_powertools import Logger

logger = Logger()

TARGET_POLICY_NAME = "IAMDeleteRootUserCredentials"
PROFILE_NAME = "sandbox"  # Used only for local testing
DOMAIN = os.environ.get("DOMAIN", "*")
HEADERS = {
    "Access-Control-Allow-Origin": DOMAIN,
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json",
}


def alb_response(status_code, body_dict, status_description=None, headers=None):
    return {
        "statusCode": status_code,
        "statusDescription": status_description or f"{status_code} OK",
        "isBase64Encoded": False,
        "headers": headers or HEADERS,
        "body": json.dumps(body_dict),
    }


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


def delete_root_login_profile_and_mfa(account_id):
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

    # Delete root login profile
    try:
        iam.delete_login_profile()
        logger.info("Root login profile deleted successfully.")
    except iam.exceptions.NoSuchEntityException:
        logger.info("No login profile found for root user.")
    except Exception as e:
        logger.error(f"Error deleting root login profile: {e}")
        raise


def lambda_handler(event, context):
    logger.info(
        "Starting root login profile and MFA device deletion", extra={"event": event}
    )
    path_param = event.get("path", {})
    try:
        account_id = path_param.split("/")[2]
    except (AttributeError, IndexError):
        account_id = None

    if not account_id:
        logger.error("Missing account_id in path parameters")
        return alb_response(
            400,
            {
                "status": "error",
                "account_id": None,
                "message": "Missing account_id in path parameters",
            },
            "400 Bad Request",
        )
    try:
        delete_root_login_profile_and_mfa(account_id)
        return alb_response(
            200,
            {
                "status": "success",
                "account_id": account_id,
                "message": "Root login profile deleted and MFA device(s) deactivated.",
            },
        )
    except Exception as e:
        logger.error(f"Error deleting root login profile or MFA: {e}")
        return alb_response(
            500,
            {
                "status": "error",
                "message": f"Error deleting root login profile or MFA: {str(e)}",
            },
            "500 Internal Server Error",
        )


if __name__ == "__main__":
    os.environ["LOCAL_TEST"] = "true"
    test_event = {
        "path": "/delete-root-login-profile/068167017169",
    }
    lambda_handler(test_event, None)
