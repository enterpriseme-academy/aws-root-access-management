import boto3
import os
import botocore
import json

from aws_lambda_powertools import Logger

logger = Logger()

TARGET_POLICY_NAME = "SQSUnlockQueuePolicy"
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
    logger.info("Starting unlock SQS queue process", extra={"event": event})

    path_param = event.get("path", {})
    try:
        account_id = path_param.split("/")[2]
    except (AttributeError, IndexError):
        account_id = None
    try:
        queue_name = path_param.split("/")[3]
    except (AttributeError, IndexError):
        queue_name = None

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
    if not queue_name:
        logger.error("Missing queue_name in path parameters")
        return alb_response(
            400,
            {
                "status": "error",
                "account_id": account_id,
                "message": "Missing queue_name in path parameters",
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

        sqs = session.client("sqs")

        # Get the queue URL
        try:
            queue_url = sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
        except Exception as e:
            logger.error(f"Failed to get SQS queue URL: {e}")
            return alb_response(
                404,
                {
                    "status": "not_found",
                    "account_id": account_id,
                    "message": f"Queue {queue_name} not found for {account_id}",
                },
                "404 Not Found",
            )

        if http_method == "GET":
            # Return the queue policy
            try:
                attrs = sqs.get_queue_attributes(
                    QueueUrl=queue_url, AttributeNames=["Policy"]
                )
                policy_str = attrs.get("Attributes", {}).get("Policy")
                if policy_str:
                    policy_json = json.loads(policy_str)
                    logger.info("Queue policy found", extra={"policy": policy_json})
                    return alb_response(
                        200,
                        {
                            "status": "success",
                            "account_id": account_id,
                            "resource_name": queue_name,
                            "policy": policy_json,
                        },
                    )
                else:
                    logger.info("Queue policy does not exist")
                    return alb_response(
                        404,
                        {
                            "status": "not_found",
                            "account_id": account_id,
                            "message": f"No queue policy found for {queue_name} on {account_id}",
                        },
                        "404 Not Found",
                    )
            except Exception as e:
                logger.error(f"Error reading queue policy: {e}")
                return alb_response(
                    500,
                    {
                        "status": "error",
                        "message": f"Error reading queue policy: {str(e)}",
                    },
                    "500 Internal Server Error",
                )

        # POST method: unlock (delete) the queue policy
        # Check if queue policy exists
        try:
            attrs = sqs.get_queue_attributes(
                QueueUrl=queue_url, AttributeNames=["Policy"]
            )
            policy_str = attrs.get("Attributes", {}).get("Policy")
            queue_policy_exist = bool(policy_str)
        except Exception as e:
            logger.error(f"Error checking queue policy: {e}")
            raise

        if queue_policy_exist:
            try:
                sqs.set_queue_attributes(QueueUrl=queue_url, Attributes={"Policy": ""})
                logger.info("Queue policy deleted successfully")
                return alb_response(
                    200,
                    {
                        "status": "unlocked",
                        "account_id": account_id,
                        "resource_name": queue_name,
                        "message": f"Queue policy deleted for {queue_name} on {account_id}",
                    },
                )
            except Exception as e:
                logger.error(f"Failed to delete queue policy: {e}")
                return alb_response(
                    500,
                    {
                        "status": "error",
                        "account_id": account_id,
                        "message": f"Failed to delete queue policy: {str(e)}",
                    },
                    "500 Internal Server Error",
                )
        else:
            return alb_response(
                200,
                {
                    "status": "not_locked",
                    "account_id": account_id,
                    "message": f"No queue policy found for {queue_name} on {account_id}",
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
    test_event = {"path": "/unlock-sqs-queue/068167017169/test-queue"}
    lambda_handler(test_event, None)
