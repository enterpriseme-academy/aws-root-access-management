import boto3
import os
import botocore
import json

from aws_lambda_powertools import Logger

logger = Logger()

TARGET_POLICY_NAME = "SQSUnlockQueuePolicy"
PROFILE_NAME = "sandbox"  # Used only for local testing

ENVIRONMENT = os.environ.get("ENVIRONMENT", "")


def lambda_response(status_code, body_dict):
    return {
        "statusCode": status_code,
        "body": body_dict,
    }


def get_boto3_session():
    if (
        os.environ.get("AWS_SAM_LOCAL") == "true"
        or os.environ.get("LOCAL_TEST") == "true"
    ):
        return boto3.Session(profile_name=PROFILE_NAME)
    else:
        return boto3.Session()


def handle_dry_run_sqs(account_id, queue_name, action):
    """Simulate SQS queue responses for development dry-run mode."""
    logger.info(
        f"DRY RUN: Simulating SQS queue operation for {queue_name} in account {account_id}"
    )
    queue_exists = "present" in queue_name.lower()

    if action == "GET":
        if queue_exists:
            return lambda_response(
                200,
                {
                    "status": "success",
                    "account_id": account_id,
                    "resource_name": queue_name,
                    "policy": {"dry_run": True},
                },
            )
        else:
            return lambda_response(
                404,
                {
                    "status": "not_found",
                    "account_id": account_id,
                    "message": f"[DRY RUN] No queue policy found for {queue_name} on {account_id}",
                },
            )

    # POST: simulate unlock
    if queue_exists:
        return lambda_response(
            200,
            {
                "status": "unlocked",
                "account_id": account_id,
                "resource_name": queue_name,
                "message": f"[DRY RUN] Queue policy deleted for {queue_name} on {account_id}",
            },
        )
    else:
        return lambda_response(
            404,
            {
                "status": "not_found",
                "account_id": account_id,
                "resource_name": queue_name,
                "message": f"[DRY RUN] Queue {queue_name} not found on {account_id}",
            },
        )


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

    account_id = event.get("account_id")
    queue_name = event.get("queue_name")

    if not account_id:
        logger.error("Missing account_id in event")
        return lambda_response(
            400,
            {
                "status": "error",
                "account_id": None,
                "message": "Missing account_id in path parameters",
            },
        )
    if not queue_name:
        logger.error("Missing queue_name in event")
        return lambda_response(
            400,
            {
                "status": "error",
                "account_id": account_id,
                "message": "Missing queue_name in path parameters",
            },
        )

    action = event.get("action", "POST")

    if ENVIRONMENT == "development":
        return handle_dry_run_sqs(account_id, queue_name, action)

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
            return lambda_response(
                404,
                {
                    "status": "not_found",
                    "account_id": account_id,
                    "message": f"Queue {queue_name} not found for {account_id}",
                },
            )

        if action == "GET":
            # Return the queue policy
            try:
                attrs = sqs.get_queue_attributes(
                    QueueUrl=queue_url, AttributeNames=["Policy"]
                )
                policy_str = attrs.get("Attributes", {}).get("Policy")
                if policy_str:
                    policy_json = json.loads(policy_str)
                    logger.info("Queue policy found", extra={"policy": policy_json})
                    return lambda_response(
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
                    return lambda_response(
                        404,
                        {
                            "status": "not_found",
                            "account_id": account_id,
                            "message": f"No queue policy found for {queue_name} on {account_id}",
                        },
                    )
            except Exception as e:
                logger.error(f"Error reading queue policy: {e}")
                return lambda_response(
                    500,
                    {
                        "status": "error",
                        "message": f"Error reading queue policy: {str(e)}",
                    },
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
                return lambda_response(
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
                return lambda_response(
                    500,
                    {
                        "status": "error",
                        "account_id": account_id,
                        "message": f"Failed to delete queue policy: {str(e)}",
                    },
                )
        else:
            return lambda_response(
                200,
                {
                    "status": "not_locked",
                    "account_id": account_id,
                    "message": f"No queue policy found for {queue_name} on {account_id}",
                },
            )
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        return lambda_response(
            500,
            {
                "status": "error",
                "message": f"Unhandled exception: {str(e)}",
            },
        )


if __name__ == "__main__":
    # Example event for local testing
    os.environ["LOCAL_TEST"] = "true"
    test_event = {"account_id": "068167017169", "queue_name": "test-queue", "action": "GET"}
    lambda_handler(test_event, None)
