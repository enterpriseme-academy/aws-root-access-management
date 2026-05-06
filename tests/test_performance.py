"""
Performance tests for Lambda functions.

Verifies that both Lambda functions can handle at least 10 requests per minute,
meaning 10 sequential invocations complete well within 60 seconds.

Test classes
------------
* ``TestS3LambdaPerformance``   – throughput and latency for unlock_s3_bucket
* ``TestSQSLambdaPerformance``  – throughput and latency for unlock_sqs_queue
* ``TestCombinedPerformance``   – concurrent invocations across both lambdas
"""

import time
import statistics
import math
import threading
from unittest.mock import patch

import pytest

import unlock_s3_bucket as s3_lambda
import unlock_sqs_queue as sqs_lambda
from tests.conftest import (
    ACCOUNT_ID,
    BUCKET_NAME,
    QUEUE_NAME,
)

# ---------------------------------------------------------------------------
# Performance thresholds
# ---------------------------------------------------------------------------

TARGET_REQUESTS_PER_MINUTE = 10
# Each Lambda must complete a single request in under this many seconds so that
# 10 requests fit comfortably within the 60-second window.
MAX_SINGLE_REQUEST_SECONDS = 5.0
# 10 sequential requests must complete within 60 s (1 minute SLA).
MAX_TOTAL_SECONDS_FOR_10_REQUESTS = 60.0
# p95 latency cap for a single invocation.
P95_LATENCY_THRESHOLD_SECONDS = 4.0


# ===========================================================================
# Helpers
# ===========================================================================


def _invoke_n_times(handler_fn, event, n: int):
    """
    Invoke *handler_fn(event, None)* sequentially *n* times.

    Returns a list of per-invocation durations in seconds together with the
    collected responses.
    """
    durations = []
    responses = []
    for _ in range(n):
        start = time.perf_counter()
        resp = handler_fn(event, None)
        elapsed = time.perf_counter() - start
        durations.append(elapsed)
        responses.append(resp)
    return durations, responses


def _invoke_concurrently(handler_fn, event, n: int):
    """
    Invoke *handler_fn(event, None)* concurrently from *n* threads.

    Returns a list of per-invocation durations in seconds together with the
    collected responses.  The total wall-clock time is also returned as the
    third element.
    """
    durations = [None] * n
    responses = [None] * n
    errors = []

    def _worker(idx):
        try:
            start = time.perf_counter()
            resp = handler_fn(event, None)
            elapsed = time.perf_counter() - start
            durations[idx] = elapsed
            responses[idx] = resp
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=_worker, args=(i,)) for i in range(n)]
    wall_start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    wall_elapsed = time.perf_counter() - wall_start

    if errors:
        raise errors[0]

    return durations, responses, wall_elapsed


# ===========================================================================
# TestS3LambdaPerformance
# ===========================================================================


class TestS3LambdaPerformance:
    """Performance tests for the S3 unlock Lambda."""

    @pytest.fixture
    def s3_perf_event(self):
        return {
            "account_id": ACCOUNT_ID,
            "bucket_name": BUCKET_NAME,
            "action": "GET",
        }

    @pytest.fixture
    def patched_s3_env(self, mock_boto3_session):
        with patch("unlock_s3_bucket.boto3.Session", return_value=mock_boto3_session), \
             patch.object(s3_lambda, "ENVIRONMENT", ""), \
             patch.object(s3_lambda, "PROTECTED_BUCKETS", []):
            yield

    def test_single_request_completes_within_threshold(
        self, s3_perf_event, patched_s3_env
    ):
        """A single S3 Lambda invocation must finish within MAX_SINGLE_REQUEST_SECONDS."""
        start = time.perf_counter()
        response = s3_lambda.lambda_handler(s3_perf_event, None)
        elapsed = time.perf_counter() - start

        assert response["statusCode"] == 200, (
            f"Expected 200, got {response['statusCode']}"
        )
        assert elapsed < MAX_SINGLE_REQUEST_SECONDS, (
            f"Single S3 request took {elapsed:.3f}s, "
            f"threshold is {MAX_SINGLE_REQUEST_SECONDS}s"
        )

    def test_ten_sequential_requests_complete_within_one_minute(
        self, s3_perf_event, patched_s3_env
    ):
        """10 sequential S3 Lambda invocations must complete within 60 seconds."""
        durations, responses = _invoke_n_times(
            s3_lambda.lambda_handler, s3_perf_event, TARGET_REQUESTS_PER_MINUTE
        )
        total = sum(durations)

        # All responses must succeed.
        for i, resp in enumerate(responses):
            assert resp["statusCode"] == 200, (
                f"Request {i + 1} returned {resp['statusCode']}, expected 200"
            )

        assert total < MAX_TOTAL_SECONDS_FOR_10_REQUESTS, (
            f"10 sequential S3 requests took {total:.3f}s, "
            f"SLA is {MAX_TOTAL_SECONDS_FOR_10_REQUESTS}s"
        )

    def test_s3_throughput_exceeds_ten_requests_per_minute(
        self, s3_perf_event, patched_s3_env
    ):
        """Measured throughput must be ≥ 10 requests/minute for the S3 Lambda."""
        durations, responses = _invoke_n_times(
            s3_lambda.lambda_handler, s3_perf_event, TARGET_REQUESTS_PER_MINUTE
        )
        total = sum(durations)
        throughput_per_minute = (TARGET_REQUESTS_PER_MINUTE / total) * 60

        assert throughput_per_minute >= TARGET_REQUESTS_PER_MINUTE, (
            f"S3 Lambda throughput {throughput_per_minute:.1f} req/min is below "
            f"the required {TARGET_REQUESTS_PER_MINUTE} req/min"
        )

    def test_s3_p95_latency_within_threshold(
        self, s3_perf_event, patched_s3_env
    ):
        """p95 latency of 10 S3 Lambda invocations must be within threshold."""
        durations, _ = _invoke_n_times(
            s3_lambda.lambda_handler, s3_perf_event, TARGET_REQUESTS_PER_MINUTE
        )
        sorted_durations = sorted(durations)
        p95_index = math.ceil(len(sorted_durations) * 0.95) - 1
        p95_latency = sorted_durations[p95_index]

        assert p95_latency < P95_LATENCY_THRESHOLD_SECONDS, (
            f"S3 Lambda p95 latency {p95_latency:.3f}s exceeds "
            f"threshold {P95_LATENCY_THRESHOLD_SECONDS}s"
        )

    def test_all_s3_requests_succeed_under_load(
        self, s3_perf_event, patched_s3_env
    ):
        """All 10 S3 Lambda invocations must return HTTP 200."""
        _, responses = _invoke_n_times(
            s3_lambda.lambda_handler, s3_perf_event, TARGET_REQUESTS_PER_MINUTE
        )
        failed = [
            (i + 1, r["statusCode"])
            for i, r in enumerate(responses)
            if r["statusCode"] != 200
        ]
        assert not failed, f"S3 requests failed (index, status): {failed}"

    def test_s3_concurrent_requests_complete_within_one_minute(
        self, s3_perf_event, patched_s3_env
    ):
        """10 concurrent S3 Lambda invocations must all finish within 60 seconds."""
        durations, responses, wall_elapsed = _invoke_concurrently(
            s3_lambda.lambda_handler, s3_perf_event, TARGET_REQUESTS_PER_MINUTE
        )

        for i, resp in enumerate(responses):
            assert resp["statusCode"] == 200, (
                f"Concurrent S3 request {i + 1} returned {resp['statusCode']}"
            )

        assert wall_elapsed < MAX_TOTAL_SECONDS_FOR_10_REQUESTS, (
            f"10 concurrent S3 requests took {wall_elapsed:.3f}s wall time, "
            f"SLA is {MAX_TOTAL_SECONDS_FOR_10_REQUESTS}s"
        )


# ===========================================================================
# TestSQSLambdaPerformance
# ===========================================================================


class TestSQSLambdaPerformance:
    """Performance tests for the SQS unlock Lambda."""

    @pytest.fixture
    def sqs_perf_event(self):
        return {
            "account_id": ACCOUNT_ID,
            "queue_name": QUEUE_NAME,
            "action": "GET",
        }

    @pytest.fixture
    def patched_sqs_env(self, mock_boto3_session):
        with patch("unlock_sqs_queue.boto3.Session", return_value=mock_boto3_session), \
             patch.object(sqs_lambda, "ENVIRONMENT", ""):
            yield

    def test_single_request_completes_within_threshold(
        self, sqs_perf_event, patched_sqs_env
    ):
        """A single SQS Lambda invocation must finish within MAX_SINGLE_REQUEST_SECONDS."""
        start = time.perf_counter()
        response = sqs_lambda.lambda_handler(sqs_perf_event, None)
        elapsed = time.perf_counter() - start

        assert response["statusCode"] == 200, (
            f"Expected 200, got {response['statusCode']}"
        )
        assert elapsed < MAX_SINGLE_REQUEST_SECONDS, (
            f"Single SQS request took {elapsed:.3f}s, "
            f"threshold is {MAX_SINGLE_REQUEST_SECONDS}s"
        )

    def test_ten_sequential_requests_complete_within_one_minute(
        self, sqs_perf_event, patched_sqs_env
    ):
        """10 sequential SQS Lambda invocations must complete within 60 seconds."""
        durations, responses = _invoke_n_times(
            sqs_lambda.lambda_handler, sqs_perf_event, TARGET_REQUESTS_PER_MINUTE
        )
        total = sum(durations)

        for i, resp in enumerate(responses):
            assert resp["statusCode"] == 200, (
                f"Request {i + 1} returned {resp['statusCode']}, expected 200"
            )

        assert total < MAX_TOTAL_SECONDS_FOR_10_REQUESTS, (
            f"10 sequential SQS requests took {total:.3f}s, "
            f"SLA is {MAX_TOTAL_SECONDS_FOR_10_REQUESTS}s"
        )

    def test_sqs_throughput_exceeds_ten_requests_per_minute(
        self, sqs_perf_event, patched_sqs_env
    ):
        """Measured throughput must be ≥ 10 requests/minute for the SQS Lambda."""
        durations, responses = _invoke_n_times(
            sqs_lambda.lambda_handler, sqs_perf_event, TARGET_REQUESTS_PER_MINUTE
        )
        total = sum(durations)
        throughput_per_minute = (TARGET_REQUESTS_PER_MINUTE / total) * 60

        assert throughput_per_minute >= TARGET_REQUESTS_PER_MINUTE, (
            f"SQS Lambda throughput {throughput_per_minute:.1f} req/min is below "
            f"the required {TARGET_REQUESTS_PER_MINUTE} req/min"
        )

    def test_sqs_p95_latency_within_threshold(
        self, sqs_perf_event, patched_sqs_env
    ):
        """p95 latency of 10 SQS Lambda invocations must be within threshold."""
        durations, _ = _invoke_n_times(
            sqs_lambda.lambda_handler, sqs_perf_event, TARGET_REQUESTS_PER_MINUTE
        )
        sorted_durations = sorted(durations)
        p95_index = math.ceil(len(sorted_durations) * 0.95) - 1
        p95_latency = sorted_durations[p95_index]

        assert p95_latency < P95_LATENCY_THRESHOLD_SECONDS, (
            f"SQS Lambda p95 latency {p95_latency:.3f}s exceeds "
            f"threshold {P95_LATENCY_THRESHOLD_SECONDS}s"
        )

    def test_all_sqs_requests_succeed_under_load(
        self, sqs_perf_event, patched_sqs_env
    ):
        """All 10 SQS Lambda invocations must return HTTP 200."""
        _, responses = _invoke_n_times(
            sqs_lambda.lambda_handler, sqs_perf_event, TARGET_REQUESTS_PER_MINUTE
        )
        failed = [
            (i + 1, r["statusCode"])
            for i, r in enumerate(responses)
            if r["statusCode"] != 200
        ]
        assert not failed, f"SQS requests failed (index, status): {failed}"

    def test_sqs_concurrent_requests_complete_within_one_minute(
        self, sqs_perf_event, patched_sqs_env
    ):
        """10 concurrent SQS Lambda invocations must all finish within 60 seconds."""
        durations, responses, wall_elapsed = _invoke_concurrently(
            sqs_lambda.lambda_handler, sqs_perf_event, TARGET_REQUESTS_PER_MINUTE
        )

        for i, resp in enumerate(responses):
            assert resp["statusCode"] == 200, (
                f"Concurrent SQS request {i + 1} returned {resp['statusCode']}"
            )

        assert wall_elapsed < MAX_TOTAL_SECONDS_FOR_10_REQUESTS, (
            f"10 concurrent SQS requests took {wall_elapsed:.3f}s wall time, "
            f"SLA is {MAX_TOTAL_SECONDS_FOR_10_REQUESTS}s"
        )


# ===========================================================================
# TestCombinedPerformance
# ===========================================================================


class TestCombinedPerformance:
    """Combined performance tests invoking both Lambda functions together."""

    @pytest.fixture
    def s3_perf_event(self):
        return {
            "account_id": ACCOUNT_ID,
            "bucket_name": BUCKET_NAME,
            "action": "GET",
        }

    @pytest.fixture
    def sqs_perf_event(self):
        return {
            "account_id": ACCOUNT_ID,
            "queue_name": QUEUE_NAME,
            "action": "GET",
        }

    @pytest.fixture
    def patched_both_envs(self, mock_boto3_session):
        with patch("unlock_s3_bucket.boto3.Session", return_value=mock_boto3_session), \
             patch("unlock_sqs_queue.boto3.Session", return_value=mock_boto3_session), \
             patch.object(s3_lambda, "ENVIRONMENT", ""), \
             patch.object(s3_lambda, "PROTECTED_BUCKETS", []), \
             patch.object(sqs_lambda, "ENVIRONMENT", ""):
            yield

    def test_combined_ten_requests_per_lambda_within_one_minute(
        self, s3_perf_event, sqs_perf_event, patched_both_envs
    ):
        """
        10 sequential requests to each Lambda (20 total) must all finish within
        60 seconds when the two functions are exercised back-to-back.
        """
        all_durations = []
        all_responses = []

        for _ in range(TARGET_REQUESTS_PER_MINUTE):
            start = time.perf_counter()
            resp = s3_lambda.lambda_handler(s3_perf_event, None)
            all_durations.append(time.perf_counter() - start)
            all_responses.append(("s3", resp))

            start = time.perf_counter()
            resp = sqs_lambda.lambda_handler(sqs_perf_event, None)
            all_durations.append(time.perf_counter() - start)
            all_responses.append(("sqs", resp))

        total = sum(all_durations)

        failed = [
            (fn, i + 1, r["statusCode"])
            for i, (fn, r) in enumerate(all_responses)
            if r["statusCode"] != 200
        ]
        assert not failed, f"Combined requests failed (fn, index, status): {failed}"

        assert total < MAX_TOTAL_SECONDS_FOR_10_REQUESTS, (
            f"20 combined requests took {total:.3f}s, "
            f"SLA is {MAX_TOTAL_SECONDS_FOR_10_REQUESTS}s"
        )

    def test_average_latency_both_lambdas_within_threshold(
        self, s3_perf_event, sqs_perf_event, patched_both_envs
    ):
        """Average latency across all invocations of both Lambdas must be within threshold."""
        s3_durations, _ = _invoke_n_times(
            s3_lambda.lambda_handler, s3_perf_event, TARGET_REQUESTS_PER_MINUTE
        )
        sqs_durations, _ = _invoke_n_times(
            sqs_lambda.lambda_handler, sqs_perf_event, TARGET_REQUESTS_PER_MINUTE
        )

        all_durations = s3_durations + sqs_durations
        avg_latency = statistics.mean(all_durations)

        assert avg_latency < MAX_SINGLE_REQUEST_SECONDS, (
            f"Average latency {avg_latency:.3f}s across both Lambdas exceeds "
            f"threshold {MAX_SINGLE_REQUEST_SECONDS}s"
        )
