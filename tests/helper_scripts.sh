#! /opt/homebrew/bin/bash
#
# Test Helper Scripts - Provides helper functions for the test suites.
# Usage: source helper_scripts.sh
# Options:
#   -v, --verbose     Enable verbose output
#   -t, --timeout N   Set timeout in seconds (default: 10)
#   -h, --help        Show this help message

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${SCRIPT_DIR}/config.sh"

# Configuration with defaults
TIMEOUT="${GLOBAL_TIMEOUT}"
VERBOSE="${GLOBAL_VERBOSE}"
PARALLEL_MODE="${GLOBAL_PARALLEL_MODE}"

LOG_FILE="${SCRIPT_DIR}/integration-tests.log"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Global counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
START_TIME=$(date +%s)

function log_to_file() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
}

function log_info() {
  local message="$1"
  echo -e "${GREEN}[INFO]${NC} ${message}"
  log_to_file "INFO: ${message}"
}

function log_error() {
  local message="$1"
  echo -e "${RED}[ERROR]${NC} ${message}" >&2 # Print to stderr
  log_to_file "ERROR: ${message}"
}

function log_debug() {
  local message="$1"
  if [[ "${VERBOSE}" == "true" ]]; then
    echo -e "${BLUE}[DEBUG]${NC} ${message}"
    log_to_file "DEBUG: ${message}"
  fi
}

function log_test() {
  local message="$1"
  echo -e "${CYAN}[TEST]${NC} ${message}"
  log_to_file "TEST: ${message}"
}

function log_success() {
  local message="$1"
  echo -e "${GREEN}[SUCCESS]${NC} ${message}"
  log_to_file "SUCCESS: ${message}"
}

function log_failure() {
  local message="$1"
  echo -e "${RED}[FAILURE]${NC} ${message}"
  log_to_file "FAILURE: ${message}"
}

function handle_error() {
  local line_number="$1"
  local error_code="$2"
  log_error "Script failed at line ${line_number} with exit code ${error_code}"
  print_summary
  exit "${error_code}"
}

# Set up error handling
trap 'handle_error ${LINENO} $?' ERR

function show_help() {
  cat << EOF
Integration Test Suite

Usage: $0 [OPTIONS]

Options:
  -v, --verbose       Enable verbose output
  -t, --timeout N     Set timeout in seconds (default: ${TIMEOUT})
  -h, --help          Show this help message

Examples:
  $0                                  # Run with defaults
  $0 -v                               # Run with verbose output
  $0 -t 30                            # Set 30 second timeout

Environment Variables:
  TIMEOUT             Request timeout in seconds
  VERBOSE             Enable verbose output (true/false)
EOF
}

#######################################
# Parse command line arguments and update global configuration.
# Globals:
#   TIMEOUT (modified)
#   VERBOSE (modified)
# Arguments:
#   Command line arguments to parse
# Returns:
#   0 on success, 1 on error
#######################################
function parse_arguments() {
  local cli_verbose="${VERBOSE}"
  local cli_timeout="${TIMEOUT}"

  while [[ $# -gt 0 ]]; do
    case $1 in
      -v|--verbose)
        VERBOSE="true"
        shift
      ;;
      -t|--timeout)
        TIMEOUT="$2"
        shift 2
      ;;
      -h|--help)
        show_help
        exit 0
      ;;
      *)
        log_error "Unknown option: $1"
        show_help
        exit 1
      ;;
    esac
  done

  # Apply command-line arguments (highest priority)
  TIMEOUT="${cli_timeout}"
  VERBOSE="${cli_verbose}"
}

#######################################
# Check if required system dependencies are available.
# Globals:
#   VERBOSE
# Arguments:
#   None
# Returns:
#   0 if all dependencies are available, 1 if any are missing
#######################################
function check_dependencies() {
  local dependencies=("curl" "jq")
  local missing_deps=()

  for dep in "${dependencies[@]}"; do
    if ! command -v "${dep}" &> /dev/null; then
      missing_deps+=("${dep}")
    fi
  done
    
  if [[ ${#missing_deps[@]} -eq 0 ]]; then
    log_debug "All dependencies are available"
    return 0
  fi

  log_error "Missing dependencies: ${missing_deps[*]}"
  log_error "Please install missing dependencies and try again"
  log_info "On Ubuntu/Debian: sudo apt-get install ${missing_deps[*]}"
  exit 1
}

#######################################
# Initialize the logging system and create log file.
# Globals:
#   LOG_FILE
#   TIMEOUT
#   VERBOSE
# Arguments:
#   None
# Outputs:
#   Creates log file with header information
#######################################
function init_logging() {
  mkdir -p "$(dirname "${LOG_FILE}")"

  echo "Integration Test Log - $(date)" > "${LOG_FILE}"
  echo "Timeout: ${TIMEOUT}s" >> "${LOG_FILE}"
  echo "Verbose: ${VERBOSE}" >> "${LOG_FILE}"
  echo "----------------------------------------" >> "${LOG_FILE}"
}

#######################################
# Execute a collection of test cases from an array.
# Globals:
#   None
# Arguments:
#   test_cases_array_name - Name of the array containing test case definitions
# Outputs:
#   Calls test_service for each test case in the array
#######################################
function run_tests() {
  local test_cases_array_name="${1}"
  declare -n test_cases_ref="${test_cases_array_name}"

  log_info "Running test suite..."

  for test_case_name in "${test_cases_ref[@]}"; do
    test_service "${test_case_name}"
  done
}

#######################################
# Execute a single test case with HTTP request and validation.
# Globals:
#   TOTAL_TESTS (incremented)
#   PASSED_TESTS (incremented)
#   FAILED_TESTS (incremented)
#   TIMEOUT
#   VERBOSE
#   SERVICE_URL
# Arguments:
#   test_case_array_name - Name of the array containing the test case definition
# Returns:
#   0 if test passes, 1 if test fails
#######################################
function test_service() {
  local test_case_array_name="${1}"
  declare -n current_test="${test_case_array_name}"

  TOTAL_TESTS=$((TOTAL_TESTS + 1))

  local test_name="${current_test["name"]}"
  local method="${current_test["method"]}"
  local endpoint="${current_test["endpoint"]}"
  local payload="${current_test["payload"]}"
  local api_key="${current_test["api_key"]}"
  local expected_status="${current_test["expected_status"]}"
  local expected_fields_str="${current_test["expected_fields"]}"
    
  log_test "Running: ${test_name}"
  log_debug "Method: ${method}, Endpoint: ${endpoint}"
  log_debug "Expected Status: ${expected_status}"
  log_debug "Expected Fields: ${expected_fields_str:-none}"

  local -a expected_fields=()
  if [[ -n "${expected_fields_str}" ]]; then
    IFS=' ' read -r -a expected_fields <<< "${expected_fields_str}"
  fi
    
  local response_body_file response_headers_file
  response_body_file=$(mktemp)
  response_headers_file=$(mktemp)

  # Ensure cleanup is called on any exit from this function
  trap "rm -f \"${response_body_file}\" \"${response_headers_file}\"" EXIT

  local curl_cmd=(
    curl
    --silent
    --show-error
    --max-time "${TIMEOUT}"
    --connect-timeout 5
    --retry 2
    --retry-delay 1
    --request "${method}"
    --url "${SERVICE_URL}${endpoint}"
    --header 'Content-Type: application/json'
    --header 'User-Agent: Integration-Test-Suite/1.0'
    --output "${response_body_file}"
    --dump-header "${response_headers_file}"
    --write-out "%{http_code}|%{time_total}|%{size_download}"
  )
    
    # Add authorization if provided
  if [[ -n "${api_key}" && "${api_key}" != "FALSE" ]]; then
    curl_cmd+=(--header "X-Internal-API-Key: ${api_key}")
    log_debug "Using API key authentication"
  fi

  # Add payload for non-GET requests
  if [[ "${method}" != "GET" && -n "${payload}" && "${payload}" != "{}" ]]; then
    curl_cmd+=(--data "${payload}")
    log_debug "Request payload: ${payload}"
  fi
    
  local curl_output
  if ! curl_output=$("${curl_cmd[@]}" 2>&1); then
    log_failure "Network error for ${test_name}: ${curl_output}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    return 1
  fi
    
  # Parse curl output (status|time|size)
  IFS='|' read -r http_code response_time response_size <<< "${curl_output}"
    
  log_debug "HTTP Status: ${http_code}"
  log_debug "Response Time: ${response_time}s"
  log_debug "Response Size: ${response_size} bytes"
    
  if [[ "${VERBOSE}" == "true" ]]; then
    log_debug "Response Body: $(cat "${response_body_file}")"
    log_debug "Response Headers: $(cat "${response_headers_file}")"
  fi
    
  if [[ "${http_code}" != "${expected_status}" ]]; then
    log_failure "HTTP status mismatch for ${test_name}"
    log_error "Expected: ${expected_status}, Got: ${http_code}"
    log_error "Response: $(cat "${response_body_file}")"
    log_error "Headers: $(head -5 "${response_headers_file}")"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    return 1
  fi
    
  if [[ ${#expected_fields[@]} -eq 0 ]]; then
    log_success "✅ ${test_name} - PASSED (${response_time}s)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    return 0
  fi

  if ! jq empty "${response_body_file}" 2>/dev/null; then
    log_failure "Invalid JSON response for ${test_name}"
    log_error "Response body: $(cat "${response_body_file}")"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    return 1
  fi

  for field in "${expected_fields[@]}"; do
    # Handle both object and array responses
		local jq_expr="if type == \"array\" then .[0] | has(\"${field}\") else has(\"${field}\") end"
    if ! jq -e "${jq_expr}" "${response_body_file}" >/dev/null 2>&1; then
      log_failure "Missing field '${field}' in ${test_name}"
      log_error "Response: $(cat "${response_body_file}")"
      FAILED_TESTS=$((FAILED_TESTS + 1))
      return 1
    fi
    log_debug "Field '${field}' found in response"
  done

  log_success "✅ ${test_name} - PASSED (${response_time}s)"
  PASSED_TESTS=$((PASSED_TESTS + 1))
  return 0
}

#######################################
# Wait for a service to become available with exponential backoff.
# Globals:
#   SERVICE_URL
#   INITIAL_SERVICE_URL
# Arguments:
#   None
# Returns:
#   0 if service becomes ready, 124 if service fails to become ready
#######################################
function wait_for_service() {
  local max_attempts=2
  local attempt=0
  local wait_time=1

  log_info "Waiting for service at ${SERVICE_URL} to be ready..."
    
  while [[ ${attempt} -lt ${max_attempts} ]]; do
    log_debug "Attempt $((attempt + 1))/${max_attempts}"

		curl_cmd=(
			curl
			--silent
			--fail
			--max-time 5
			--connect-timeout 3
			"${INITIAL_SERVICE_URL}"
		)
		
    if "${curl_cmd[@]}" >/dev/null 2>&1; then
      log_success "Service is ready!"
      return 0
    fi
        
    attempt=$((attempt + 1))
        
    if [[ ${attempt} -lt ${max_attempts} ]]; then
      log_debug "Service not ready, waiting ${wait_time}s..."
      sleep "${wait_time}"
      wait_time=$((wait_time < 8 ? wait_time * 2 : 8))
    fi
  done
    
  log_error "Service failed to become ready after ${max_attempts} attempts"
  log_error "Please check if the service is running at ${SERVICE_URL}"
  return 124
}

function print_summary() {
  local end_time=$(date +%s)
  local duration=$((end_time - START_TIME))
    
  echo "==========================================="
  echo "Integration Test Results Summary"
  echo "==========================================="
  echo "Total Tests:    ${TOTAL_TESTS}"
  echo "Passed:         ${PASSED_TESTS}"
  echo "Failed:         ${FAILED_TESTS}"
  echo "Success Rate:   $((TOTAL_TESTS > 0 ? PASSED_TESTS * 100 / TOTAL_TESTS : 0))%"
  echo "Duration:       ${duration}s"
  echo "Log File:       ${LOG_FILE}"
  echo "==========================================="
    
  if [[ ${FAILED_TESTS} -eq 0 ]]; then
    log_success "🎉 All tests passed!"
  else
    log_error "❌ ${FAILED_TESTS} test(s) failed"
    log_info "Check the log file for detailed error information: ${LOG_FILE}"
  fi
    
  log_to_file "Test Summary: ${PASSED_TESTS}/${TOTAL_TESTS} passed in ${duration}s"
}
