#!/usr/bin/env bash
# run_performance_tests.sh
#
# Runs the Lambda performance test suite that verifies both Lambda functions
# can handle at least 10 requests per minute.
#
# Usage:
#   ./scripts/run_performance_tests.sh [pytest options]
#
# Examples:
#   ./scripts/run_performance_tests.sh
#   ./scripts/run_performance_tests.sh -v
#   ./scripts/run_performance_tests.sh -v --tb=short
#   ./scripts/run_performance_tests.sh -k "test_s3"
#
# The script will:
#   1. Locate (or create) a Python virtual environment in .venv/
#   2. Install test dependencies from tests/requirements.txt
#   3. Execute only the performance tests (tests/test_performance.py)
#   4. Print a summary and exit with the pytest exit code

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"
REQUIREMENTS="${REPO_ROOT}/tests/requirements.txt"
TEST_FILE="${REPO_ROOT}/tests/test_performance.py"

# ---------------------------------------------------------------------------
# Colours (disabled when stdout is not a terminal)
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  CYAN='\033[0;36m'
  BOLD='\033[1m'
  RESET='\033[0m'
else
  RED='' GREEN='' YELLOW='' CYAN='' BOLD='' RESET=''
fi

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; }

# ---------------------------------------------------------------------------
# 1. Resolve Python interpreter
# ---------------------------------------------------------------------------
PYTHON=""
for candidate in python3 python; do
  if command -v "$candidate" &>/dev/null; then
    version=$("$candidate" -c 'import sys; print(sys.version_info[:2])')
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
      PYTHON="$candidate"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  error "Python 3.10 or later is required but was not found on PATH."
  exit 1
fi

info "Using Python: $($PYTHON --version)"

# ---------------------------------------------------------------------------
# 2. Set up virtual environment
# ---------------------------------------------------------------------------
if [ ! -d "${VENV_DIR}" ]; then
  info "Creating virtual environment at ${VENV_DIR} ..."
  "$PYTHON" -m venv "${VENV_DIR}"
  success "Virtual environment created."
else
  info "Reusing existing virtual environment at ${VENV_DIR}."
fi

# Activate the virtual environment
# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"

# ---------------------------------------------------------------------------
# 3. Install / refresh dependencies
# ---------------------------------------------------------------------------
info "Installing test dependencies from ${REQUIREMENTS} ..."
pip install --quiet --upgrade pip
pip install --quiet -r "${REQUIREMENTS}"
success "Dependencies installed."

# ---------------------------------------------------------------------------
# 4. Run performance tests
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}=================================================================${RESET}"
echo -e "${BOLD}  Lambda Performance Tests  (target: ≥ 10 requests / minute)    ${RESET}"
echo -e "${BOLD}=================================================================${RESET}"
echo ""

# Default pytest flags + any extra args passed to this script
PYTEST_ARGS=("${TEST_FILE}" "--tb=short" "$@")

set +e
python -m pytest "${PYTEST_ARGS[@]}"
EXIT_CODE=$?
set -e

# ---------------------------------------------------------------------------
# 5. Summary
# ---------------------------------------------------------------------------
echo ""
if [ "${EXIT_CODE}" -eq 0 ]; then
  success "All performance tests passed."
else
  error "One or more performance tests FAILED (exit code ${EXIT_CODE})."
fi

exit "${EXIT_CODE}"
