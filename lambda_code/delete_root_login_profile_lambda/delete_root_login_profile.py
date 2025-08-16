import boto3
import os
import json
from aws_lambda_powertools import Logger

logger = Logger()

TARGET_POLICY_NAME = "IAMDeleteRootUserCredentials"
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

    # # List MFA devices for root user
    # try:
    #     response = iam.list_mfa_devices(UserName="root")
    #     mfa_devices = response.get("MFADevices", [])
    #     if not mfa_devices:
    #         logger.info("No MFA devices found for root user.")
    #     else:
    #         for device in mfa_devices:
    #             serial_number = device["SerialNumber"]
    #             iam.deactivate_mfa_device(UserName="root", SerialNumber=serial_number)
    #             logger.info(f"MFA device {serial_number} deactivated for root user.")
    # except Exception as e:
    #     logger.error(f"Error deactivating MFA device: {e}")
    #     raise


def lambda_handler(event, context):
    logger.info(
        "Starting root login profile and MFA device deletion", extra={"event": event}
    )
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
        delete_root_login_profile_and_mfa(account_id)
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "status": "success",
                    "message": "Root login profile deleted and MFA device(s) deactivated.",
                }
            ),
        }
    except Exception as e:
        logger.error(f"Error deleting root login profile or MFA: {e}")
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "status": "error",
                    "message": f"Error deleting root login profile or MFA: {str(e)}",
                }
            ),
        }


if __name__ == "__main__":
    os.environ["LOCAL_TEST"] = "true"
    test_event = {
        "pathParameters": {"account_number": "068167017169"},
    }
    lambda_handler(test_event, None)
