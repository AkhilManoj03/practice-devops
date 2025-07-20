#!/bin/bash
#
# Product Tests - Integration Test Suite.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../helper_scripts.sh"

SERVICE_URL="${PRODUCT_SERVICE_URL:-http://localhost:8000}"
INITIAL_SERVICE_URL="${SERVICE_URL}/status"

# Test data definitions
readonly PRODUCT_FIELDS=("id" "name" "description" "image_url" "votes")
readonly ORIGAMI_FIELDS=("id" "name" "description" "image_url" "votes")
readonly HEALTH_FIELDS=("status" "timestamp" "version")
readonly SYSTEM_INFO_FIELDS=("hostname" "ip_address" "is_container" "is_kubernetes")
readonly VOTE_RESPONSE_FIELDS="origami_id new_vote_count message"

declare -A get_product_by_id
get_product_by_id["name"]="Get product by ID"
get_product_by_id["method"]="GET"
get_product_by_id["endpoint"]="/api/products/1"
get_product_by_id["payload"]=""
get_product_by_id["api_key"]=""
get_product_by_id["expected_status"]="200"
get_product_by_id["expected_fields"]="${PRODUCT_FIELDS}"

declare -A get_non_existent_product
get_non_existent_product["name"]="Get non-existent product"
get_non_existent_product["method"]="GET"
get_non_existent_product["endpoint"]="/api/products/9999"
get_non_existent_product["payload"]=""
get_non_existent_product["api_key"]=""
get_non_existent_product["expected_status"]="404"
get_non_existent_product["expected_fields"]=""

declare -A get_all_products
get_all_products["name"]="Get all products"
get_all_products["method"]="GET"
get_all_products["endpoint"]="/api/products"
get_all_products["payload"]=""
get_all_products["api_key"]=""
get_all_products["expected_status"]="200"
get_all_products["expected_fields"]="${PRODUCT_FIELDS}"

declare -A get_origami_by_id
get_origami_by_id["name"]="Get origami by ID"
get_origami_by_id["method"]="GET"
get_origami_by_id["endpoint"]="/api/origamis/1"
get_origami_by_id["payload"]=""
get_origami_by_id["api_key"]=""
get_origami_by_id["expected_status"]="200"
get_origami_by_id["expected_fields"]="${ORIGAMI_FIELDS}"

declare -A get_non_existent_origami
get_non_existent_origami["name"]="Get non-existent origami"
get_non_existent_origami["method"]="GET"
get_non_existent_origami["endpoint"]="/api/origamis/9999"
get_non_existent_origami["payload"]=""
get_non_existent_origami["api_key"]=""
get_non_existent_origami["expected_status"]="404"
get_non_existent_origami["expected_fields"]=""

declare -A get_origami_votes
get_origami_votes["name"]="Get origami votes"
get_origami_votes["method"]="GET"
get_origami_votes["endpoint"]="/api/origamis/1/votes"
get_origami_votes["payload"]=""
get_origami_votes["api_key"]=""
get_origami_votes["expected_status"]="200"
get_origami_votes["expected_fields"]="votes"

declare -A get_non_existent_origami_votes
get_non_existent_origami_votes["name"]="Get votes for non-existent origami"
get_non_existent_origami_votes["method"]="GET"
get_non_existent_origami_votes["endpoint"]="/api/origamis/9999/votes"
get_non_existent_origami_votes["payload"]=""
get_non_existent_origami_votes["api_key"]=""
get_non_existent_origami_votes["expected_status"]="404"
get_non_existent_origami_votes["expected_fields"]=""

declare -A get_all_origamis
get_all_origamis["name"]="Get all origamis"
get_all_origamis["method"]="GET"
get_all_origamis["endpoint"]="/api/origamis"
get_all_origamis["payload"]=""
get_all_origamis["api_key"]=""
get_all_origamis["expected_status"]="200"
get_all_origamis["expected_fields"]="${ORIGAMI_FIELDS}"

declare -A get_health
get_health["name"]="Health check"
get_health["method"]="GET"
get_health["endpoint"]="/health"
get_health["payload"]=""
get_health["api_key"]=""
get_health["expected_status"]="200"
get_health["expected_fields"]="${HEALTH_FIELDS}"

declare -A get_system_info
get_system_info["name"]="Get system info"
get_system_info["method"]="GET"
get_system_info["endpoint"]="/api/system-info"
get_system_info["payload"]=""
get_system_info["api_key"]=""
get_system_info["expected_status"]="200"
get_system_info["expected_fields"]="${SYSTEM_INFO_FIELDS}"

declare -A get_root_endpoint
get_root_endpoint["name"]="Root endpoint"
get_root_endpoint["method"]="GET"
get_root_endpoint["endpoint"]="/"
get_root_endpoint["payload"]=""
get_root_endpoint["api_key"]=""
get_root_endpoint["expected_status"]="200"
get_root_endpoint["expected_fields"]=""

PRODUCT_TESTS_ARRAY=(
    # Product API tests
    get_product_by_id
    get_non_existent_product
    get_all_products

    # Origami API tests
    get_origami_by_id
    get_non_existent_origami
    get_origami_votes
    get_non_existent_origami_votes
    get_all_origamis

    # System endpoints tests
    get_health
    get_system_info
    get_root_endpoint
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
        exit 1
    fi
    
    run_tests "PRODUCT_TESTS_ARRAY"
    
    print_summary
     
    exit ${FAILED_TESTS}
}

main "$@"
