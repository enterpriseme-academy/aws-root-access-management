import boto3
import os
import botocore
import json

from aws_lambda_powertools import Logger

logger = Logger()

TARGET_POLICY_NAME = "S3UnlockBucketPolicy"
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


def lambda_handler(event, context):
    logger.info("Starting unlock S3 bucket process", extra={"event": event})

    path_param = event.get("path", {})
    try:
        account_id = path_param.split("/")[2]
    except (AttributeError, IndexError):
        account_id = None
    try:
        bucket_name = path_param.split("/")[3]
    except (AttributeError, IndexError):
        bucket_name = None

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
    if not bucket_name:
        logger.error("Missing bucket_name in path parameters")
        return alb_response(
            400,
            {
                "status": "error",
                "account_id": account_id,
                "message": "Missing bucket_name in path parameters",
            },
            "400 Bad Request",
        )

    http_method = event.get("httpMethod", "POST")

    try:
        creds = assume_root(account_id, TARGET_POLICY_NAME)

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

        s3 = session.client("s3")

        if http_method == "GET":
            # Return the bucket policy
            try:
                response = s3.get_bucket_policy(Bucket=bucket_name)
                policy_json = json.loads(response["Policy"])
                logger.info("Bucket policy found", extra={"policy": policy_json})
                return alb_response(
                    200,
                    {
                        "status": "success",
                        "account_id": account_id,
                        "resource_name": bucket_name,
                        "policy": policy_json,
                    },
                )
            except botocore.exceptions.ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                if error_code == "NoSuchBucketPolicy":
                    logger.info("Bucket policy does not exist")
                    return alb_response(
                        404,
                        {
                            "status": "not_found",
                            "message": f"No bucket policy found for {bucket_name} on {account_id}",
                        },
                        "404 Not Found",
                    )
                else:
                    logger.error(f"Error reading bucket policy: {e}")
                    return alb_response(
                        500,
                        {
                            "status": "error",
                            "message": f"Error reading bucket policy: {str(e)}",
                        },
                        "500 Internal Server Error",
                    )

        # POST method: unlock (delete) the bucket policy
        # Check if bucket policy exists
        try:
            response = s3.get_bucket_policy(Bucket=bucket_name)
            logger.info("Bucket policy found", extra={"policy": response["Policy"]})
            bucket_policy_exist = True
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchBucketPolicy":
                logger.info("Bucket policy does not exist")
                bucket_policy_exist = False
            else:
                logger.error(f"Error checking bucket policy: {e}")
                raise

        if bucket_policy_exist:
            try:
                s3.delete_bucket_policy(Bucket=bucket_name)
                logger.info("Bucket policy deleted successfully")
                return alb_response(
                    200,
                    {
                        "status": "unlocked",
                        "account_id": account_id,
                        "resource_name": bucket_name,
                        "message": f"Bucket policy deleted for {bucket_name} on {account_id}",
                    },
                )
            except Exception as e:
                logger.error(f"Failed to delete bucket policy: {e}")
                return alb_response(
                    500,
                    {
                        "status": "error",
                        "message": f"Failed to delete bucket policy: {str(e)}",
                    },
                    "500 Internal Server Error",
                )
        else:
            return alb_response(
                200,
                {
                    "status": "not_locked",
                    "account_id": account_id,
                    "resource_name": bucket_name,
                    "message": f"No bucket policy found for {bucket_name} on {account_id}",
                },
            )
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        return alb_response(
            500,
            {
                "status": "error",
                "message": f"Unhandled exception: {str(e)}",
            },
            "500 Internal Server Error",
        )


if __name__ == "__main__":
    # Example event for local testing
    os.environ["LOCAL_TEST"] = "true"
    test_event = {"path": "/unlock-s3-bucket/068167017169/068167017169-test-bucket"}
    lambda_handler(test_event, None)
