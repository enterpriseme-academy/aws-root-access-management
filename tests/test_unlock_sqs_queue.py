"""
Unit tests for lambda_code/unlock_sqs_queue_lambda/unlock_sqs_queue.py.

Test classes
------------
* ``TestAlbResponseSQS``       – helper function ``alb_response``
* ``TestGetBoto3SessionSQS``   – helper function ``get_boto3_session``
* ``TestHandleDryRunSQS``      – dry-run simulation ``handle_dry_run_sqs``
* ``TestAssumeRootSQS``        – STS root-assumption helper ``assume_root``
* ``TestLambdaHandlerSQS``     – main ``lambda_handler`` entry point
"""

import json
import os

import pytest
from unittest.mock import MagicMock, patch

import unlock_sqs_queue as sqs_lambda
from tests.conftest import (
    ACCOUNT_ID,
    FAKE_CREDENTIALS,
    QUEUE_NAME,
    QUEUE_URL,
    SAMPLE_SQS_POLICY,
)


# ===========================================================================
# TestAlbResponseSQS
# ===========================================================================


class TestAlbResponseSQS:
    """Unit tests for the ``alb_response`` helper in the SQS unlock Lambda."""

    def test_status_code_is_propagated(self):
        response = sqs_lambda.alb_response(200, {"status": "ok"})
        assert response["statusCode"] == 200

    def test_default_status_description_uses_status_code(self):
        response = sqs_lambda.alb_response(201, {})
        assert response["statusDescription"] == "201 OK"

    def test_custom_status_description_is_used(self):
        response = sqs_lambda.alb_response(404, {}, "404 Not Found")
        assert response["statusDescription"] == "404 Not Found"

    def test_body_is_json_serialised(self):
        body = {"key": "value", "nested": {"n": 1}}
        response = sqs_lambda.alb_response(200, body)
        assert json.loads(response["body"]) == body

    def test_is_base64_encoded_is_false(self):
        response = sqs_lambda.alb_response(200, {})
        assert response["isBase64Encoded"] is False

    def test_default_headers_are_applied(self):
        response = sqs_lambda.alb_response(200, {})
        assert "Content-Type" in response["headers"]

    def test_custom_headers_override_default(self):
        custom = {"X-Custom-Header": "test-value"}
        response = sqs_lambda.alb_response(200, {}, headers=custom)
        assert response["headers"] == custom


# ===========================================================================
# TestGetBoto3SessionSQS
# ===========================================================================


class TestGetBoto3SessionSQS:
    """Unit tests for ``get_boto3_session`` in the SQS unlock Lambda."""

    def test_returns_profile_session_when_local_test_is_set(self, monkeypatch):
        monkeypatch.setenv("LOCAL_TEST", "true")
        monkeypatch.delenv("AWS_SAM_LOCAL", raising=False)
        with patch("unlock_sqs_queue.boto3.Session") as mock_session:
            sqs_lambda.get_boto3_session()
            mock_session.assert_called_once_with(profile_name=sqs_lambda.PROFILE_NAME)

    def test_returns_profile_session_when_sam_local_is_set(self, monkeypatch):
        monkeypatch.setenv("AWS_SAM_LOCAL", "true")
        monkeypatch.delenv("LOCAL_TEST", raising=False)
        with patch("unlock_sqs_queue.boto3.Session") as mock_session:
            sqs_lambda.get_boto3_session()
            mock_session.assert_called_once_with(profile_name=sqs_lambda.PROFILE_NAME)

    def test_returns_plain_session_in_production(self, monkeypatch):
        monkeypatch.delenv("LOCAL_TEST", raising=False)
        monkeypatch.delenv("AWS_SAM_LOCAL", raising=False)
        with patch("unlock_sqs_queue.boto3.Session") as mock_session:
            sqs_lambda.get_boto3_session()
            mock_session.assert_called_once_with()


# ===========================================================================
# TestHandleDryRunSQS
# ===========================================================================


class TestHandleDryRunSQS:
    """Unit tests for the ``handle_dry_run_sqs`` simulation helper."""

    def test_get_present_queue_returns_200(self):
        response = sqs_lambda.handle_dry_run_sqs(ACCOUNT_ID, "present-queue", "GET")
        assert response["statusCode"] == 200
        assert json.loads(response["body"])["status"] == "success"

    def test_get_absent_queue_returns_404(self):
        response = sqs_lambda.handle_dry_run_sqs(ACCOUNT_ID, "absent-queue", "GET")
        assert response["statusCode"] == 404
        assert json.loads(response["body"])["status"] == "not_found"

    def test_post_present_queue_returns_unlocked(self):
        response = sqs_lambda.handle_dry_run_sqs(ACCOUNT_ID, "present-queue", "POST")
        assert response["statusCode"] == 200
        assert json.loads(response["body"])["status"] == "unlocked"

    def test_post_absent_queue_returns_404(self):
        response = sqs_lambda.handle_dry_run_sqs(ACCOUNT_ID, "absent-queue", "POST")
        assert response["statusCode"] == 404
        assert json.loads(response["body"])["status"] == "not_found"

    def test_dry_run_response_includes_account_id(self):
        response = sqs_lambda.handle_dry_run_sqs(ACCOUNT_ID, "absent-queue", "POST")
        body = json.loads(response["body"])
        assert body["account_id"] == ACCOUNT_ID

    def test_dry_run_response_includes_resource_name(self):
        response = sqs_lambda.handle_dry_run_sqs(ACCOUNT_ID, "present-queue", "GET")
        body = json.loads(response["body"])
        assert body["resource_name"] == "present-queue"


# ===========================================================================
# TestAssumeRootSQS
# ===========================================================================


class TestAssumeRootSQS:
    """Unit tests for the ``assume_root`` helper in the SQS unlock Lambda."""

    def test_returns_credentials_on_success(
        self, patch_sqs_boto3_session, mock_sts_client
    ):
        creds = sqs_lambda.assume_root(ACCOUNT_ID, "SQSUnlockQueuePolicy")
        assert creds == FAKE_CREDENTIALS

    def test_calls_sts_assume_root_once(
        self, patch_sqs_boto3_session, mock_sts_client
    ):
        sqs_lambda.assume_root(ACCOUNT_ID, "SQSUnlockQueuePolicy")
        mock_sts_client.assume_root.assert_called_once()

    def test_uses_correct_policy_arn(self, patch_sqs_boto3_session, mock_sts_client):
        sqs_lambda.assume_root(ACCOUNT_ID, "SQSUnlockQueuePolicy")
        call_kwargs = mock_sts_client.assume_root.call_args.kwargs
        expected_arn = "arn:aws:iam::aws:policy/root-task/SQSUnlockQueuePolicy"
        assert call_kwargs["TaskPolicyArn"] == {"arn": expected_arn}

    def test_uses_account_id_as_target_principal(
        self, patch_sqs_boto3_session, mock_sts_client
    ):
        sqs_lambda.assume_root(ACCOUNT_ID, "SQSUnlockQueuePolicy")
        call_kwargs = mock_sts_client.assume_root.call_args.kwargs
        assert call_kwargs["TargetPrincipal"] == ACCOUNT_ID

    def test_propagates_sts_exception(self, patch_sqs_boto3_session, mock_sts_client):
        mock_sts_client.assume_root.side_effect = Exception("STS unavailable")
        with pytest.raises(Exception, match="STS unavailable"):
            sqs_lambda.assume_root(ACCOUNT_ID, "SQSUnlockQueuePolicy")


# ===========================================================================
# TestLambdaHandlerSQS
# ===========================================================================


class TestLambdaHandlerSQS:
    """Integration-style unit tests for the SQS unlock ``lambda_handler``."""

    # --- input validation ---------------------------------------------------

    def test_missing_account_id_returns_400(self):
        event = {"path": "/unlock-sqs-queue/"}
        response = sqs_lambda.lambda_handler(event, None)
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["message"] == "Missing account_id in path parameters"

    def test_missing_queue_name_returns_400(self):
        event = {"path": f"/unlock-sqs-queue/{ACCOUNT_ID}"}
        response = sqs_lambda.lambda_handler(event, None)
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["message"] == "Missing queue_name in path parameters"

    def test_empty_path_returns_400(self):
        response = sqs_lambda.lambda_handler({"path": ""}, None)
        assert response["statusCode"] == 400

    # --- development / dry-run mode -----------------------------------------

    def test_development_get_delegates_to_dry_run(self, sqs_get_event):
        with patch.object(sqs_lambda, "ENVIRONMENT", "development"), patch.object(
            sqs_lambda, "handle_dry_run_sqs"
        ) as mock_dry:
            mock_dry.return_value = {"statusCode": 200, "body": "{}"}
            sqs_lambda.lambda_handler(sqs_get_event, None)
            mock_dry.assert_called_once_with(ACCOUNT_ID, QUEUE_NAME, "GET")

    def test_development_post_delegates_to_dry_run(self, sqs_post_event):
        with patch.object(sqs_lambda, "ENVIRONMENT", "development"), patch.object(
            sqs_lambda, "handle_dry_run_sqs"
        ) as mock_dry:
            mock_dry.return_value = {"statusCode": 200, "body": "{}"}
            sqs_lambda.lambda_handler(sqs_post_event, None)
            mock_dry.assert_called_once_with(ACCOUNT_ID, QUEUE_NAME, "POST")

    # --- queue not found ----------------------------------------------------

    def test_queue_not_found_returns_404(
        self, sqs_get_event, patch_sqs_boto3_session, mock_sqs_client
    ):
        mock_sqs_client.get_queue_url.side_effect = Exception("Queue does not exist")
        with patch.object(sqs_lambda, "ENVIRONMENT", ""):
            response = sqs_lambda.lambda_handler(sqs_get_event, None)
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["status"] == "not_found"

    # --- GET – read queue policy --------------------------------------------

    def test_get_returns_queue_policy(self, sqs_get_event, patch_sqs_boto3_session):
        with patch.object(sqs_lambda, "ENVIRONMENT", ""):
            response = sqs_lambda.lambda_handler(sqs_get_event, None)
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["status"] == "success"
        assert body["policy"] == SAMPLE_SQS_POLICY

    def test_get_no_queue_policy_returns_404(
        self, sqs_get_event, patch_sqs_boto3_session, mock_sqs_client
    ):
        mock_sqs_client.get_queue_attributes.return_value = {"Attributes": {}}
        with patch.object(sqs_lambda, "ENVIRONMENT", ""):
            response = sqs_lambda.lambda_handler(sqs_get_event, None)
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["status"] == "not_found"

    def test_get_attributes_error_returns_500(
        self, sqs_get_event, patch_sqs_boto3_session, mock_sqs_client
    ):
        mock_sqs_client.get_queue_attributes.side_effect = Exception("SQS error")
        with patch.object(sqs_lambda, "ENVIRONMENT", ""):
            response = sqs_lambda.lambda_handler(sqs_get_event, None)
        assert response["statusCode"] == 500

    # --- POST – unlock queue policy -----------------------------------------

    def test_post_removes_queue_policy_and_returns_unlocked(
        self, sqs_post_event, patch_sqs_boto3_session, mock_sqs_client
    ):
        with patch.object(sqs_lambda, "ENVIRONMENT", ""):
            response = sqs_lambda.lambda_handler(sqs_post_event, None)
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["status"] == "unlocked"
        mock_sqs_client.set_queue_attributes.assert_called_once_with(
            QueueUrl=QUEUE_URL, Attributes={"Policy": ""}
        )

    def test_post_no_policy_returns_not_locked(
        self, sqs_post_event, patch_sqs_boto3_session, mock_sqs_client
    ):
        mock_sqs_client.get_queue_attributes.return_value = {"Attributes": {}}
        with patch.object(sqs_lambda, "ENVIRONMENT", ""):
            response = sqs_lambda.lambda_handler(sqs_post_event, None)
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["status"] == "not_locked"

    def test_post_set_attributes_failure_returns_500(
        self, sqs_post_event, patch_sqs_boto3_session, mock_sqs_client
    ):
        mock_sqs_client.set_queue_attributes.side_effect = Exception(
            "SetQueueAttributes failed"
        )
        with patch.object(sqs_lambda, "ENVIRONMENT", ""):
            response = sqs_lambda.lambda_handler(sqs_post_event, None)
        assert response["statusCode"] == 500

    def test_post_check_policy_error_propagates_to_500(
        self, sqs_post_event, patch_sqs_boto3_session, mock_sqs_client
    ):
        mock_sqs_client.get_queue_attributes.side_effect = Exception(
            "Unexpected error checking policy"
        )
        with patch.object(sqs_lambda, "ENVIRONMENT", ""):
            response = sqs_lambda.lambda_handler(sqs_post_event, None)
        assert response["statusCode"] == 500

    # --- assume_root failure ------------------------------------------------

    def test_assume_root_failure_returns_500(self, sqs_post_event):
        with patch.object(sqs_lambda, "ENVIRONMENT", ""), patch.object(
            sqs_lambda, "assume_root", side_effect=Exception("STS unavailable")
        ):
            response = sqs_lambda.lambda_handler(sqs_post_event, None)
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["status"] == "error"
