#!/bin/bash
#
# Integration Test Runner - Orchestrates all integration test suites.
#
# Usage: ./test_runner.sh [OPTIONS]
# Options:
#   -v, --verbose     Enable verbose output
#   -t, --timeout N   Set timeout in seconds (default: 10)
#   -s, --suite NAME  Run specific test suite only
#   -p, --parallel    Run test suites in parallel
#   -h, --help        Show this help message

set -uo pipefail

# Import common functionality
INTEGRATION_SUITES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${INTEGRATION_SUITES_DIR}/../helper_scripts.sh"

# Global aggregated counters
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0
TOTAL_FAILED_TESTS=0

# Test suite definitions
AVAILABLE_SUITES=(
  "product"
  "frontend"
  "recommendation"
  "authentication"
)

function show_help() {
  cat << EOF
Test Runner - Integration Test Suite Orchestrator

Usage: $0 [OPTIONS]

Options:
  -v, --verbose       Enable verbose output
  -t, --timeout N     Set timeout in seconds (default: ${TIMEOUT})
  -s, --suite NAME    Run specific test suite only
  -p, --parallel      Run test suites in parallel
  -h, --help          Show this help message

Available Test Suites:
$(printf '%s\n' "${AVAILABLE_SUITES[@]}" | sed 's/^/    /')

Examples:
  $0                                  # Run all test suites
  $0 -v                               # Run with verbose output
  $0 -s product                       # Run only product tests
  $0 -p                               # Run suites in parallel

Environment Variables:
  TIMEOUT             Request timeout in seconds
  VERBOSE             Enable verbose output (true/false)
  PARALLEL_MODE       Run suites in parallel (true/false)
EOF
}

function parse_runner_arguments() {
  local specific_suite=""
  local cli_timeout="${TIMEOUT}"
  local cli_verbose="${VERBOSE}"
  local cli_parallel_mode="${PARALLEL_MODE}"
    
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      -s|--suite)
        specific_suite="${2}"
        shift 2
        ;;
      -p|--parallel)
        PARALLEL_MODE="true"
        shift
        ;;
      -v|--verbose)
        VERBOSE="true"
        shift
        ;;
      -t|--timeout)
        TIMEOUT="${2}"
        shift 2
        ;;
      -h|--help)
        show_help
        exit 0
        ;;
      *)
        log_error "Unknown option: ${1}"
        show_help
        exit 1
        ;;
    esac
  done

  TIMEOUT="${cli_timeout}"
  VERBOSE="${cli_verbose}"
  PARALLEL_MODE="${cli_parallel_mode}"
    
  if [[ -z "${specific_suite}" || "${specific_suite}" == "all" ]]; then
    return 0
  fi

  if [[ " ${AVAILABLE_SUITES[*]} " =~ " ${specific_suite} " ]]; then
    AVAILABLE_SUITES=("${specific_suite}")
  else
    log_error "Unknown test suite: ${specific_suite}"
    log_info "Available suites: ${AVAILABLE_SUITES[*]}"
    exit 1
  fi
}

#######################################
# Execute a single test suite and capture its results.
# Globals:
#   TOTAL_SUITES (incremented)
#   TOTAL_FAILED_TESTS (incremented)
#   INTEGRATION_SUITES_DIR
# Arguments:
#   suite_name - Name of the test suite to run
# Returns:
#   Number of failed tests in the suite
#   Exit code 124 if suite times out
#######################################
function run_test_suite() {
  local suite_name="${1}"
  local suite_file="${suite_name}_tests.sh"
  local suite_path="${INTEGRATION_SUITES_DIR}/${suite_file}"
    
  TOTAL_SUITES=$((TOTAL_SUITES + 1))
    
  echo # Add spacing between suites
  log_info "═══════════════════════════════════════════"
  log_info "Running test suite: ${suite_name}"
  log_info "═══════════════════════════════════════════"
    
  if [[ ! -f "${suite_path}" ]]; then
    log_error "Test suite file not found: ${suite_path}"
    return 1
  fi
  if [[ ! -x "${suite_path}" ]]; then
    log_error "Test suite file not executable: ${suite_path}"
    return 1
  fi
    
	# Run the test suite and capture its exit code
	local suite_exit_code=0
	timeout 300 "${suite_path}" 2>&1
	suite_exit_code=$?
	if [[ "${suite_exit_code}" -eq 124 ]]; then # timeout
		log_error "❌ Test suite '${suite_name}' timed out after 5 minutes"
		return 124
	fi	
	# The exit code from the test suite represents the number of failed tests
	local suite_failed_tests="${suite_exit_code}"
	
	TOTAL_FAILED_TESTS=$((TOTAL_FAILED_TESTS + suite_failed_tests))
	if [[ "${suite_exit_code}" -eq 0 ]]; then
		log_success "✅ Test suite '${suite_name}' completed successfully"
	else
		log_failure "❌ Test suite '${suite_name}' failed with ${suite_failed_tests} test failure(s)"
	fi
	
	return "${suite_failed_tests}"
}

#######################################
# Execute all test suites concurrently in parallel.
# Globals:
#   AVAILABLE_SUITES
# Arguments:
#   None
# Returns:
#   Number of suites that failed during parallel execution
#######################################
function run_suites_parallel() {
  local pids=()
  local suite_results=()
    
  log_info "Running ${#AVAILABLE_SUITES[@]} test suites in parallel..."
    
  # Start all suites in background
  for suite in "${AVAILABLE_SUITES[@]}"; do
    log_debug "Starting suite: ${suite}"
    run_test_suite "${suite}" &
    pids+=("${!}")
    suite_results+=("${suite}")
  done
    
  # Wait for all suites to complete
  local failed_pids=()
  for i in "${!pids[@]}"; do
    local pid="${pids[$i]}"
    local suite="${suite_results[$i]}"
        
    if wait "${pid}"; then
      log_debug "Suite '${suite}' completed successfully"
    else
      log_debug "Suite '${suite}' failed"
      failed_pids+=("${pid}")
    fi
  done
    
  return "${#failed_pids[@]}"
}

#######################################
# Execute all test suites sequentially one after another.
# Globals:
#   AVAILABLE_SUITES
#   PASSED_SUITES (incremented)
#   FAILED_SUITES (incremented)
# Arguments:
#   None
# Returns:
#   Number of suites that failed during sequential execution
#######################################
function run_suites_sequential() {
  log_info "Running ${#AVAILABLE_SUITES[@]} test suites sequentially..."
    
  for suite in "${AVAILABLE_SUITES[@]}"; do
    if run_test_suite "${suite}"; then
      PASSED_SUITES=$((PASSED_SUITES + 1))
    else
      FAILED_SUITES=$((FAILED_SUITES + 1))
    fi

    sleep 1 # Add small delay between suites
  done
    
  return "${FAILED_SUITES}"
}

#######################################
# Display comprehensive summary of test execution results.
# Globals:
#   TOTAL_SUITES
#   PASSED_SUITES
#   FAILED_SUITES
#   TOTAL_FAILED_TESTS
#   PARALLEL_MODE
#   LOG_FILE
#   START_TIME
# Arguments:
#   None
# Outputs:
#   Writes summary report to stdout and log file
#######################################
function print_runner_summary() {
  local end_time=$(date +%s)
  local duration=$((end_time - START_TIME))
    
  echo
  echo "=============================================="
  echo "Test Runner Summary"
  echo "=============================================="
  echo "Test Suites:"
  echo "  Total Suites:    ${TOTAL_SUITES}"
  echo "  Passed Suites:   ${PASSED_SUITES}"
  echo "  Failed Suites:   ${FAILED_SUITES}"
  echo "  Suite Success:   $((TOTAL_SUITES > 0 ? PASSED_SUITES * 100 / TOTAL_SUITES : 0))%"
  echo
  echo "Test Results:"
  echo "  Total Failed:    ${TOTAL_FAILED_TESTS}"
  echo
  echo "Execution Info:"
  echo "  Duration:        ${duration}s"
  echo "  Parallel Mode:   ${PARALLEL_MODE}"
  echo "  Log File:        ${LOG_FILE}"
  echo "=============================================="
    
  if [[ "${FAILED_SUITES}" -eq 0 && "${TOTAL_FAILED_TESTS}" -eq 0 ]]; then
    log_success "🎉 All test suites passed!"
  else
    if [[ "${FAILED_SUITES}" -gt 0 ]]; then
      log_error "❌ ${FAILED_SUITES} test suite(s) failed"
    fi
    if [[ "${TOTAL_FAILED_TESTS}" -gt 0 ]]; then
      log_error "❌ ${TOTAL_FAILED_TESTS} total test(s) failed across all suites"
    fi
    log_info "Check individual suite logs for detailed error information"
  fi
  log_to_file "Runner Summary: ${PASSED_SUITES}/${TOTAL_SUITES} suites passed"
  log_to_file "Total test failures: ${TOTAL_FAILED_TESTS}"
  log_to_file "Duration: ${duration}s"
}

function init_runner_logging() {
  init_logging
    
  # Add runner-specific header to the shared log file
  log_to_file "=========================================="
  log_to_file "TEST RUNNER SESSION STARTED"
  log_to_file "Parallel Mode: ${PARALLEL_MODE}"
  log_to_file "Available Suites: ${AVAILABLE_SUITES[*]}"
  log_to_file "=========================================="
}

#######################################
# Main execution function that orchestrates the entire test runner.
# Globals:
#   TIMEOUT
#   VERBOSE
#   PARALLEL_MODE
#   AVAILABLE_SUITES
#   TOTAL_FAILED_TESTS
# Arguments:
#   Command line arguments passed to the script
# Returns:
#   Total number of failed tests across all suites
#######################################
function main() {
  init_runner_logging
    
  parse_runner_arguments "$@"
    
  check_dependencies
    
  log_info "Starting test runner..."
  log_info "Configuration:"
  log_info "  Timeout: ${TIMEOUT}s"
  log_info "  Verbose: ${VERBOSE}"
  log_info "  Parallel: ${PARALLEL_MODE}"
  log_info "  Test Suites: ${AVAILABLE_SUITES[*]}"
    
  if [[ "${PARALLEL_MODE}" == "true" ]]; then
    run_suites_parallel
  else
    run_suites_sequential
  fi
    
  print_runner_summary
    
  exit "${TOTAL_FAILED_TESTS}"
}

main "$@"
