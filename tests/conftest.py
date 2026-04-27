"""
Shared pytest fixtures for the Lambda function test suite.

This file is automatically loaded by pytest for every test module inside
the ``tests/`` directory. It provides:

* Python path setup so the Lambda modules can be imported without installing them.
* Reusable constants (account IDs, bucket/queue names, fake credentials, sample policies).
* Direct invocation event fixtures for both Lambda functions.
* Mock AWS client fixtures (STS, S3, SQS) built with ``unittest.mock.MagicMock``.
* A composite ``mock_boto3_session`` fixture that routes ``session.client()`` calls
  to the appropriate mock client.
* Module-scoped ``patch_*_boto3_session`` fixtures that patch ``boto3.Session`` inside
  each Lambda module for the duration of a test.
"""

import json
import os
import sys

import pytest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Python path – make lambda modules importable without package install
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LAMBDA_CODE_DIR = os.path.join(_REPO_ROOT, "lambda_code")

sys.path.insert(0, os.path.join(_LAMBDA_CODE_DIR, "unlock_s3_bucket_lambda"))
sys.path.insert(0, os.path.join(_LAMBDA_CODE_DIR, "unlock_sqs_queue_lambda"))

# Required by aws_lambda_powertools at module import time
os.environ.setdefault("POWERTOOLS_SERVICE_NAME", "test-service")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

ACCOUNT_ID = "123456789012"
BUCKET_NAME = "test-bucket"
QUEUE_NAME = "test-queue"
QUEUE_URL = f"https://sqs.us-east-1.amazonaws.com/{ACCOUNT_ID}/{QUEUE_NAME}"

FAKE_CREDENTIALS = {
    "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
    "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "SessionToken": "FQoDYXdzEJr//fake-session-token",
}

SAMPLE_S3_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {"Effect": "Deny", "Principal": "*", "Action": "s3:*", "Resource": "*"}
    ],
}

SAMPLE_SQS_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {"Effect": "Deny", "Principal": "*", "Action": "sqs:*", "Resource": "*"}
    ],
}

# ---------------------------------------------------------------------------
# Direct invocation event fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def s3_get_event():
    """Direct invocation GET event for the S3 unlock Lambda."""
    return {
        "account_id": ACCOUNT_ID,
        "bucket_name": BUCKET_NAME,
        "action": "GET",
    }


@pytest.fixture
def s3_post_event():
    """Direct invocation POST event for the S3 unlock Lambda."""
    return {
        "account_id": ACCOUNT_ID,
        "bucket_name": BUCKET_NAME,
        "action": "POST",
    }


@pytest.fixture
def sqs_get_event():
    """Direct invocation GET event for the SQS unlock Lambda."""
    return {
        "account_id": ACCOUNT_ID,
        "queue_name": QUEUE_NAME,
        "action": "GET",
    }


@pytest.fixture
def sqs_post_event():
    """Direct invocation POST event for the SQS unlock Lambda."""
    return {
        "account_id": ACCOUNT_ID,
        "queue_name": QUEUE_NAME,
        "action": "POST",
    }


# ---------------------------------------------------------------------------
# Mock AWS client fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_sts_client():
    """Mocked STS client whose ``assume_root`` returns ``FAKE_CREDENTIALS``."""
    client = MagicMock()
    client.assume_root.return_value = {"Credentials": FAKE_CREDENTIALS}
    return client


@pytest.fixture
def mock_s3_client():
    """Mocked S3 client pre-configured with ``SAMPLE_S3_POLICY``."""
    client = MagicMock()
    client.get_bucket_policy.return_value = {"Policy": json.dumps(SAMPLE_S3_POLICY)}
    return client


@pytest.fixture
def mock_sqs_client():
    """Mocked SQS client pre-configured with ``SAMPLE_SQS_POLICY``."""
    client = MagicMock()
    client.get_queue_url.return_value = {"QueueUrl": QUEUE_URL}
    client.get_queue_attributes.return_value = {
        "Attributes": {"Policy": json.dumps(SAMPLE_SQS_POLICY)}
    }
    return client


# ---------------------------------------------------------------------------
# Composite boto3 session fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_boto3_session(mock_sts_client, mock_s3_client, mock_sqs_client):
    """
    Mocked ``boto3.Session`` instance.

    ``session.client(service)`` is routed to the matching mock client fixture
    so individual tests can configure or assert on the specific clients.
    """
    session = MagicMock()

    _client_map = {
        "sts": mock_sts_client,
        "s3": mock_s3_client,
        "sqs": mock_sqs_client,
    }

    def _client_factory(service, **kwargs):
        return _client_map[service]

    session.client.side_effect = _client_factory
    return session


# ---------------------------------------------------------------------------
# Module-level boto3.Session patches
# ---------------------------------------------------------------------------


@pytest.fixture
def patch_s3_boto3_session(mock_boto3_session):
    """
    Patches ``boto3.Session`` inside the *unlock_s3_bucket* module for the
    duration of the test.  Yields the ``mock_boto3_session`` so tests can
    assert on session-level calls if needed.
    """
    with patch("unlock_s3_bucket.boto3.Session", return_value=mock_boto3_session):
        yield mock_boto3_session


@pytest.fixture
def patch_sqs_boto3_session(mock_boto3_session):
    """
    Patches ``boto3.Session`` inside the *unlock_sqs_queue* module for the
    duration of the test.  Yields the ``mock_boto3_session`` so tests can
    assert on session-level calls if needed.
    """
    with patch("unlock_sqs_queue.boto3.Session", return_value=mock_boto3_session):
        yield mock_boto3_session
