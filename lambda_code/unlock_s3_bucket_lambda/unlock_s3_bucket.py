import boto3
import os
import botocore
import json

from aws_lambda_powertools import Logger

logger = Logger()

TARGET_POLICY_NAME = "S3UnlockBucketPolicy"
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


def lambda_handler(event, context):
    logger.info("Starting unlock S3 bucket process", extra={"event": event})

    path_params = event.get("pathParameters", {})
    account_number = path_params.get("account_number")
    bucket_name = path_params.get("bucket_name")

    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    }

    if not account_number:
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
    if not bucket_name:
        logger.error("Missing bucket_name in path parameters")
        return {
            "statusCode": 400,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "status": "error",
                    "message": "Missing bucket_name in path parameters",
                }
            ),
        }

    http_method = event.get("httpMethod", "POST")

    try:
        creds = assume_root(account_number, TARGET_POLICY_NAME)

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
                return {
                    "statusCode": 200,
                    "headers": cors_headers,
                    "body": json.dumps(
                        {
                            "status": "success",
                            "bucket_name": bucket_name,
                            "policy": policy_json,
                        }
                    ),
                }
            except botocore.exceptions.ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                if error_code == "NoSuchBucketPolicy":
                    logger.info("Bucket policy does not exist")
                    return {
                        "statusCode": 404,
                        "headers": cors_headers,
                        "body": json.dumps(
                            {
                                "status": "not_found",
                                "message": f"No bucket policy found for {bucket_name}",
                            }
                        ),
                    }
                else:
                    logger.error(f"Error reading bucket policy: {e}")
                    return {
                        "statusCode": 500,
                        "headers": cors_headers,
                        "body": json.dumps(
                            {
                                "status": "error",
                                "message": f"Error reading bucket policy: {str(e)}",
                            }
                        ),
                    }

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
                return {
                    "statusCode": 200,
                    "headers": cors_headers,
                    "body": json.dumps(
                        {
                            "status": "unlocked",
                            "message": f"Bucket policy deleted for {bucket_name}",
                        }
                    ),
                }
            except Exception as e:
                logger.error(f"Failed to delete bucket policy: {e}")
                return {
                    "statusCode": 500,
                    "headers": cors_headers,
                    "body": json.dumps(
                        {
                            "status": "error",
                            "message": f"Failed to delete bucket policy: {str(e)}",
                        }
                    ),
                }
        else:
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps(
                    {
                        "status": "not_locked",
                        "message": f"No bucket policy found for {bucket_name}",
                    }
                ),
            }
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "status": "error",
                    "message": f"Unhandled exception: {str(e)}",
                }
            ),
        }


if __name__ == "__main__":
    # Example event for local testing
    os.environ["LOCAL_TEST"] = "true"
    test_event = {}
    lambda_handler(test_event, None)
