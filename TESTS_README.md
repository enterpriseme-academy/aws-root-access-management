# Lambda Function Tests

This document describes how to run the existing unit tests and how to add new ones for the Lambda functions in this repository.

---

## Project structure

```
tests/
├── __init__.py
├── conftest.py                  # Shared pytest fixtures (mock clients, events, constants)
├── requirements.txt             # Test-only dependencies
├── test_unlock_s3_bucket.py     # Tests for unlock_s3_bucket Lambda
└── test_unlock_sqs_queue.py     # Tests for unlock_sqs_queue Lambda
pytest.ini                       # Pytest configuration
```

---

## Prerequisites

Python 3.10 or later is required.  All test dependencies are listed in `tests/requirements.txt`.

### Installing dependencies

```bash
pip install -r tests/requirements.txt
```

> **Tip:** use a virtual environment to keep dependencies isolated.
>
> ```bash
> python -m venv .venv
> source .venv/bin/activate        # Linux / macOS
> .venv\Scripts\activate           # Windows
> pip install -r tests/requirements.txt
> ```

---

## Running the tests

### Run all tests

```bash
pytest
```

### Run with verbose output

```bash
pytest -v
```

### Run a specific test file

```bash
pytest tests/test_unlock_s3_bucket.py
pytest tests/test_unlock_sqs_queue.py
```

### Run a specific test class

```bash
pytest tests/test_unlock_s3_bucket.py::TestLambdaHandlerS3
```

### Run a single test

```bash
pytest tests/test_unlock_s3_bucket.py::TestLambdaHandlerS3::test_get_returns_bucket_policy
```

### Run tests matching a keyword

```bash
pytest -k "dry_run"
```

### Generate a coverage report (requires `pytest-cov`)

```bash
pip install pytest-cov
pytest --cov=lambda_code --cov-report=term-missing
```

---

## How the tests are organised

Each Lambda function has its own test file.  Inside each file the tests are split into dedicated classes, one class per logical concern:

| Class | What it tests |
|---|---|
| `TestLambdaResponseS3 / SQS` | `lambda_response()` helper – correct shape, body returned as dict |
| `TestGetBoto3SessionS3 / SQS` | `get_boto3_session()` – local vs. production session |
| `TestHandleDryRunS3 / SQS` | `handle_dry_run_s3/sqs()` – dry-run mode with present/absent resources |
| `TestAssumeRootS3 / SQS` | `assume_root()` – STS call, policy ARN construction, error propagation |
| `TestLambdaHandlerS3 / SQS` | `lambda_handler()` – full handler integration: validation, happy paths, error paths |

---

## Fixtures (`tests/conftest.py`)

`conftest.py` is loaded automatically by pytest and provides all shared fixtures.  Never import it directly — just declare the fixture name as a test parameter.

### Available fixtures

| Fixture | Description |
|---|---|
| `s3_get_event` | Direct invocation GET event for the S3 Lambda |
| `s3_post_event` | Direct invocation POST event for the S3 Lambda |
| `sqs_get_event` | Direct invocation GET event for the SQS Lambda |
| `sqs_post_event` | Direct invocation POST event for the SQS Lambda |
| `mock_sts_client` | `MagicMock` STS client; `assume_root` returns `FAKE_CREDENTIALS` |
| `mock_s3_client` | `MagicMock` S3 client; `get_bucket_policy` returns `SAMPLE_S3_POLICY` |
| `mock_sqs_client` | `MagicMock` SQS client; `get_queue_url` and `get_queue_attributes` return pre-configured values |
| `mock_boto3_session` | Composite session that routes `session.client(service)` to the matching mock client |
| `patch_s3_boto3_session` | Patches `boto3.Session` inside `unlock_s3_bucket` for the duration of the test |
| `patch_sqs_boto3_session` | Patches `boto3.Session` inside `unlock_sqs_queue` for the duration of the test |

### Shared constants (importable from `tests.conftest`)

```python
from tests.conftest import (
    ACCOUNT_ID,       # "123456789012"
    BUCKET_NAME,      # "test-bucket"
    QUEUE_NAME,       # "test-queue"
    QUEUE_URL,        # full SQS URL for QUEUE_NAME
    FAKE_CREDENTIALS, # dict with AccessKeyId / SecretAccessKey / SessionToken
    SAMPLE_S3_POLICY, # minimal Deny-all S3 bucket policy
    SAMPLE_SQS_POLICY,# minimal Deny-all SQS queue policy
)
```

---

## Writing new tests

### 1. Adding a test to an existing file

Open the relevant test file and add a method to the appropriate class.  Method names must start with `test_`.

```python
class TestLambdaHandlerS3:

    def test_my_new_scenario(self, s3_post_event, patch_s3_boto3_session):
        # Arrange
        ...
        # Act
        response = s3_lambda.lambda_handler(s3_post_event, None)
        # Assert
        assert response["statusCode"] == 200
```

### 2. Creating a test file for a new Lambda function

1. Add the new Lambda module directory to `sys.path` in `tests/conftest.py`:

   ```python
   sys.path.insert(0, os.path.join(_LAMBDA_CODE_DIR, "my_new_lambda"))
   ```

2. Create `tests/test_my_new_lambda.py` following the existing file structure:
   - One class per logical concern (helpers, dry-run, handler, …)
   - Import the module at the top: `import my_new_lambda as new_lambda`
   - Add Lambda-specific event fixtures and mock clients to `conftest.py` if they are reusable across tests.

3. Run `pytest tests/test_my_new_lambda.py -v` to confirm the new tests are collected and pass.

### 3. Simulating AWS errors

Use `botocore.exceptions.ClientError` to simulate AWS API errors in tests:

```python
import botocore.exceptions

def test_access_denied_returns_500(self, s3_get_event, patch_s3_boto3_session, mock_s3_client):
    mock_s3_client.get_bucket_policy.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        "GetBucketPolicy",
    )
    response = s3_lambda.lambda_handler(s3_get_event, None)
    assert response["statusCode"] == 500
```

Use pytest's built-in `monkeypatch` fixture to set/delete **runtime** environment variables (i.e. ones read inside the function body):

```python
def test_local_session(self, monkeypatch):
    monkeypatch.setenv("LOCAL_TEST", "true")
    ...
```

### 4. Overriding module-level environment variables

Some Lambda functions read `os.environ` at module import time (e.g. `ENVIRONMENT`, `PROTECTED_BUCKETS`).  Override those module attributes directly with `unittest.mock.patch.object`:

```python
from unittest.mock import patch

def test_protected_bucket(self):
    event = {"account_id": "123456789012", "bucket_name": "my-bucket", "action": "POST"}
    with patch.object(s3_lambda, "PROTECTED_BUCKETS", ["my-bucket"]):
        response = s3_lambda.lambda_handler(event, None)
    assert response["statusCode"] == 403
```

---

## Continuous integration

Add the following step to your CI pipeline after installing dependencies:

```yaml
- name: Run unit tests
  run: pytest -v
```
