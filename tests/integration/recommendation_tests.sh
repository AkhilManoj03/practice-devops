#! /opt/homebrew/bin/bash
#
# Recommendation Tests - Integration Test Suite.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../helper_scripts.sh"

SERVICE_URL="${RECOMMENDATION_TESTS_SERVICE_URL:-http://localhost:8080}"
INITIAL_SERVICE_URL="${SERVICE_URL}/api/recommendation-status"

declare -A get_recommendation_status
get_recommendation_status["name"]="Get Recommendation status"
get_recommendation_status["method"]="GET"
get_recommendation_status["endpoint"]="/api/recommendation-status"
get_recommendation_status["payload"]=""
get_recommendation_status["api_key"]=""
get_recommendation_status["expected_status"]="200"
get_recommendation_status["expected_fields"]="database_status status"

declare -A get_home_page
get_home_page["name"]="Get Home Page"
get_home_page["method"]="GET"
get_home_page["endpoint"]="/"
get_home_page["payload"]=""
get_home_page["api_key"]=""
get_home_page["expected_status"]="200"
get_home_page["expected_fields"]=""

declare -A get_origami_of_the_day
get_origami_of_the_day["name"]="Get Origami of the Day"
get_origami_of_the_day["method"]="GET"
get_origami_of_the_day["endpoint"]="/api/origami-of-the-day"
get_origami_of_the_day["payload"]=""
get_origami_of_the_day["api_key"]=""
get_origami_of_the_day["expected_status"]="200"
get_origami_of_the_day["expected_fields"]="id name description image_url votes"

RECOMMENDATION_TESTS_ARRAY=(
  get_recommendation_status
  get_home_page
  get_origami_of_the_day
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
    
  run_tests "RECOMMENDATION_TESTS_ARRAY"
    
  print_summary
    
  exit ${FAILED_TESTS}
}

main "$@"
