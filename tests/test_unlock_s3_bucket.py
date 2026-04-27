"""
Unit tests for lambda_code/unlock_s3_bucket_lambda/unlock_s3_bucket.py.

Test classes
------------
* ``TestLambdaResponseS3``    – helper function ``lambda_response``
* ``TestGetBoto3SessionS3``   – helper function ``get_boto3_session``
* ``TestHandleDryRunS3``      – dry-run simulation ``handle_dry_run_s3``
* ``TestAssumeRootS3``        – STS root-assumption helper ``assume_root``
* ``TestLambdaHandlerS3``     – main ``lambda_handler`` entry point
"""

import json
import os

import botocore.exceptions
import pytest
from unittest.mock import MagicMock, patch

import unlock_s3_bucket as s3_lambda
from tests.conftest import (
    ACCOUNT_ID,
    BUCKET_NAME,
    FAKE_CREDENTIALS,
    SAMPLE_S3_POLICY,
)


# ===========================================================================
# TestLambdaResponseS3
# ===========================================================================


class TestLambdaResponseS3:
    """Unit tests for the ``lambda_response`` helper in the S3 unlock Lambda."""

    def test_status_code_is_propagated(self):
        response = s3_lambda.lambda_response(200, {"status": "ok"})
        assert response["statusCode"] == 200

    def test_body_is_returned_as_dict(self):
        body = {"key": "value", "nested": {"n": 1}}
        response = s3_lambda.lambda_response(200, body)
        assert response["body"] == body

    def test_response_contains_status_code_and_body(self):
        response = s3_lambda.lambda_response(404, {"status": "not_found"})
        assert "statusCode" in response
        assert "body" in response


# ===========================================================================
# TestGetBoto3SessionS3
# ===========================================================================


class TestGetBoto3SessionS3:
    """Unit tests for ``get_boto3_session`` in the S3 unlock Lambda."""

    def test_returns_profile_session_when_local_test_is_set(self, monkeypatch):
        monkeypatch.setenv("LOCAL_TEST", "true")
        monkeypatch.delenv("AWS_SAM_LOCAL", raising=False)
        with patch("unlock_s3_bucket.boto3.Session") as mock_session:
            s3_lambda.get_boto3_session()
            mock_session.assert_called_once_with(profile_name=s3_lambda.PROFILE_NAME)

    def test_returns_profile_session_when_sam_local_is_set(self, monkeypatch):
        monkeypatch.setenv("AWS_SAM_LOCAL", "true")
        monkeypatch.delenv("LOCAL_TEST", raising=False)
        with patch("unlock_s3_bucket.boto3.Session") as mock_session:
            s3_lambda.get_boto3_session()
            mock_session.assert_called_once_with(profile_name=s3_lambda.PROFILE_NAME)

    def test_returns_plain_session_in_production(self, monkeypatch):
        monkeypatch.delenv("LOCAL_TEST", raising=False)
        monkeypatch.delenv("AWS_SAM_LOCAL", raising=False)
        with patch("unlock_s3_bucket.boto3.Session") as mock_session:
            s3_lambda.get_boto3_session()
            mock_session.assert_called_once_with()


# ===========================================================================
# TestHandleDryRunS3
# ===========================================================================


class TestHandleDryRunS3:
    """Unit tests for the ``handle_dry_run_s3`` simulation helper."""

    def test_get_present_bucket_returns_200(self):
        response = s3_lambda.handle_dry_run_s3(ACCOUNT_ID, "present-bucket", "GET")
        assert response["statusCode"] == 200
        assert response["body"]["status"] == "success"

    def test_get_absent_bucket_returns_404(self):
        response = s3_lambda.handle_dry_run_s3(ACCOUNT_ID, "absent-bucket", "GET")
        assert response["statusCode"] == 404
        assert response["body"]["status"] == "not_found"

    def test_post_present_bucket_returns_unlocked(self):
        response = s3_lambda.handle_dry_run_s3(ACCOUNT_ID, "present-bucket", "POST")
        assert response["statusCode"] == 200
        assert response["body"]["status"] == "unlocked"

    def test_post_absent_bucket_returns_404(self):
        response = s3_lambda.handle_dry_run_s3(ACCOUNT_ID, "absent-bucket", "POST")
        assert response["statusCode"] == 404
        assert response["body"]["status"] == "not_found"

    def test_dry_run_response_includes_account_id(self):
        response = s3_lambda.handle_dry_run_s3(ACCOUNT_ID, "absent-bucket", "POST")
        assert response["body"]["account_id"] == ACCOUNT_ID

    def test_dry_run_response_includes_resource_name(self):
        response = s3_lambda.handle_dry_run_s3(ACCOUNT_ID, "present-bucket", "GET")
        assert response["body"]["resource_name"] == "present-bucket"


# ===========================================================================
# TestAssumeRootS3
# ===========================================================================


class TestAssumeRootS3:
    """Unit tests for the ``assume_root`` helper in the S3 unlock Lambda."""

    def test_returns_credentials_on_success(
        self, patch_s3_boto3_session, mock_sts_client
    ):
        creds = s3_lambda.assume_root(ACCOUNT_ID, "S3UnlockBucketPolicy")
        assert creds == FAKE_CREDENTIALS

    def test_calls_sts_assume_root_once(
        self, patch_s3_boto3_session, mock_sts_client
    ):
        s3_lambda.assume_root(ACCOUNT_ID, "S3UnlockBucketPolicy")
        mock_sts_client.assume_root.assert_called_once()

    def test_uses_correct_policy_arn(self, patch_s3_boto3_session, mock_sts_client):
        s3_lambda.assume_root(ACCOUNT_ID, "S3UnlockBucketPolicy")
        call_kwargs = mock_sts_client.assume_root.call_args.kwargs
        expected_arn = "arn:aws:iam::aws:policy/root-task/S3UnlockBucketPolicy"
        assert call_kwargs["TaskPolicyArn"] == {"arn": expected_arn}

    def test_uses_account_id_as_target_principal(
        self, patch_s3_boto3_session, mock_sts_client
    ):
        s3_lambda.assume_root(ACCOUNT_ID, "S3UnlockBucketPolicy")
        call_kwargs = mock_sts_client.assume_root.call_args.kwargs
        assert call_kwargs["TargetPrincipal"] == ACCOUNT_ID

    def test_propagates_sts_exception(self, patch_s3_boto3_session, mock_sts_client):
        mock_sts_client.assume_root.side_effect = Exception("STS unavailable")
        with pytest.raises(Exception, match="STS unavailable"):
            s3_lambda.assume_root(ACCOUNT_ID, "S3UnlockBucketPolicy")


# ===========================================================================
# TestLambdaHandlerS3
# ===========================================================================


class TestLambdaHandlerS3:
    """Integration-style unit tests for the S3 unlock ``lambda_handler``."""

    # --- input validation ---------------------------------------------------

    def test_missing_account_id_returns_400(self):
        event = {"bucket_name": BUCKET_NAME}
        response = s3_lambda.lambda_handler(event, None)
        assert response["statusCode"] == 400
        assert response["body"]["message"] == "Missing account_id in path parameters"

    def test_missing_bucket_name_returns_400(self):
        event = {"account_id": ACCOUNT_ID}
        response = s3_lambda.lambda_handler(event, None)
        assert response["statusCode"] == 400
        assert response["body"]["message"] == "Missing bucket_name in path parameters"

    def test_empty_event_returns_400(self):
        response = s3_lambda.lambda_handler({}, None)
        assert response["statusCode"] == 400

    # --- protected bucket guard ---------------------------------------------

    def test_bucket_in_protected_list_returns_403(self):
        event = {"account_id": ACCOUNT_ID, "bucket_name": "protected-bucket"}
        with patch.object(s3_lambda, "PROTECTED_BUCKETS", ["protected-bucket"]):
            response = s3_lambda.lambda_handler(event, None)
        assert response["statusCode"] == 403
        assert "protected" in response["body"]["message"]

    def test_tf_state_pattern_bucket_returns_403(self):
        tf_bucket = f"{ACCOUNT_ID}-tf-state"
        event = {"account_id": ACCOUNT_ID, "bucket_name": tf_bucket}
        with patch.object(s3_lambda, "PROTECTED_BUCKETS", []):
            response = s3_lambda.lambda_handler(event, None)
        assert response["statusCode"] == 403

    # --- development / dry-run mode -----------------------------------------

    def test_development_get_delegates_to_dry_run(self, s3_get_event):
        with patch.object(s3_lambda, "ENVIRONMENT", "development"), patch.object(
            s3_lambda, "handle_dry_run_s3"
        ) as mock_dry:
            mock_dry.return_value = {"statusCode": 200, "body": {}}
            s3_lambda.lambda_handler(s3_get_event, None)
            mock_dry.assert_called_once_with(ACCOUNT_ID, BUCKET_NAME, "GET")

    def test_development_post_delegates_to_dry_run(self, s3_post_event):
        with patch.object(s3_lambda, "ENVIRONMENT", "development"), patch.object(
            s3_lambda, "handle_dry_run_s3"
        ) as mock_dry:
            mock_dry.return_value = {"statusCode": 200, "body": {}}
            s3_lambda.lambda_handler(s3_post_event, None)
            mock_dry.assert_called_once_with(ACCOUNT_ID, BUCKET_NAME, "POST")

    # --- GET – read bucket policy -------------------------------------------

    def test_get_returns_bucket_policy(
        self, s3_get_event, patch_s3_boto3_session
    ):
        with patch.object(s3_lambda, "ENVIRONMENT", ""), patch.object(
            s3_lambda, "PROTECTED_BUCKETS", []
        ):
            response = s3_lambda.lambda_handler(s3_get_event, None)
        assert response["statusCode"] == 200
        assert response["body"]["status"] == "success"
        assert response["body"]["policy"] == SAMPLE_S3_POLICY

    def test_get_no_bucket_policy_returns_404(
        self, s3_get_event, patch_s3_boto3_session, mock_s3_client
    ):
        mock_s3_client.get_bucket_policy.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "NoSuchBucketPolicy", "Message": "No policy"}},
            "GetBucketPolicy",
        )
        with patch.object(s3_lambda, "ENVIRONMENT", ""), patch.object(
            s3_lambda, "PROTECTED_BUCKETS", []
        ):
            response = s3_lambda.lambda_handler(s3_get_event, None)
        assert response["statusCode"] == 404
        assert response["body"]["status"] == "not_found"

    def test_get_s3_client_error_returns_500(
        self, s3_get_event, patch_s3_boto3_session, mock_s3_client
    ):
        mock_s3_client.get_bucket_policy.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "GetBucketPolicy",
        )
        with patch.object(s3_lambda, "ENVIRONMENT", ""), patch.object(
            s3_lambda, "PROTECTED_BUCKETS", []
        ):
            response = s3_lambda.lambda_handler(s3_get_event, None)
        assert response["statusCode"] == 500

    # --- POST – unlock bucket policy ----------------------------------------

    def test_post_deletes_bucket_policy_and_returns_unlocked(
        self, s3_post_event, patch_s3_boto3_session, mock_s3_client
    ):
        with patch.object(s3_lambda, "ENVIRONMENT", ""), patch.object(
            s3_lambda, "PROTECTED_BUCKETS", []
        ):
            response = s3_lambda.lambda_handler(s3_post_event, None)
        assert response["statusCode"] == 200
        assert response["body"]["status"] == "unlocked"
        mock_s3_client.delete_bucket_policy.assert_called_once_with(Bucket=BUCKET_NAME)

    def test_post_no_policy_returns_not_locked(
        self, s3_post_event, patch_s3_boto3_session, mock_s3_client
    ):
        mock_s3_client.get_bucket_policy.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "NoSuchBucketPolicy", "Message": "No policy"}},
            "GetBucketPolicy",
        )
        with patch.object(s3_lambda, "ENVIRONMENT", ""), patch.object(
            s3_lambda, "PROTECTED_BUCKETS", []
        ):
            response = s3_lambda.lambda_handler(s3_post_event, None)
        assert response["statusCode"] == 200
        assert response["body"]["status"] == "not_locked"

    def test_post_delete_policy_failure_returns_500(
        self, s3_post_event, patch_s3_boto3_session, mock_s3_client
    ):
        mock_s3_client.delete_bucket_policy.side_effect = Exception("Delete failed")
        with patch.object(s3_lambda, "ENVIRONMENT", ""), patch.object(
            s3_lambda, "PROTECTED_BUCKETS", []
        ):
            response = s3_lambda.lambda_handler(s3_post_event, None)
        assert response["statusCode"] == 500

    def test_post_check_policy_unexpected_error_propagates_to_500(
        self, s3_post_event, patch_s3_boto3_session, mock_s3_client
    ):
        mock_s3_client.get_bucket_policy.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "InternalError", "Message": "Unexpected"}},
            "GetBucketPolicy",
        )
        with patch.object(s3_lambda, "ENVIRONMENT", ""), patch.object(
            s3_lambda, "PROTECTED_BUCKETS", []
        ):
            response = s3_lambda.lambda_handler(s3_post_event, None)
        assert response["statusCode"] == 500

    # --- assume_root failure ------------------------------------------------

    def test_assume_root_failure_returns_500(self, s3_post_event):
        with patch.object(s3_lambda, "ENVIRONMENT", ""), patch.object(
            s3_lambda, "PROTECTED_BUCKETS", []
        ), patch.object(
            s3_lambda, "assume_root", side_effect=Exception("STS unavailable")
        ):
            response = s3_lambda.lambda_handler(s3_post_event, None)
        assert response["statusCode"] == 500
        assert response["body"]["status"] == "error"
