#!/bin/bash
#
# Frontend Tests - Integration Test Suite.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../helper_scripts.sh"

SERVICE_URL="${FRONTEND_TESTS_SERVICE_URL:-http://localhost:3000}"
INITIAL_SERVICE_URL="${SERVICE_URL}"

declare -A get_home_page
get_home_page["name"]="Get Home Page"
get_home_page["method"]="GET"
get_home_page["endpoint"]="/"
get_home_page["payload"]=""
get_home_page["api_key"]=""
get_home_page["expected_status"]="200"
get_home_page["expected_fields"]=""

declare -A get_login_page
get_login_page["name"]="Get Login Page"
get_login_page["method"]="GET"
get_login_page["endpoint"]="/login"
get_login_page["payload"]=""
get_login_page["api_key"]=""
get_login_page["expected_status"]="200"
get_login_page["expected_fields"]=""

FRONTEND_TESTS_ARRAY=(
  get_home_page
  get_login_page
)

function main() {
  parse_arguments "$@"

  export SERVICE_URL INITIAL_SERVICE_URL

  log_info "Starting integration test suite..."
  log_info "Configuration:"
  log_info "  Service URL: ${SERVICE_URL}"
  log_info "  Timeout: ${TIMEOUT}s"
  log_info "  Verbose: ${VERBOSE}"
  log_info "  Log file: ${LOG_FILE}"
    
  if ! wait_for_service; then
    log_error "Cannot proceed with tests - service not ready"
    exit 124
  fi
    
  run_tests "FRONTEND_TESTS_ARRAY"
    
  print_summary
    
  exit ${FAILED_TESTS}
}

main "$@"
