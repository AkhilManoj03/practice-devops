#! /opt/homebrew/bin/bash
# 
# Authentication Tests - Integration Test Suite.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../helper_scripts.sh"

SERVICE_URL="${AUTHENTICATION_TESTS_SERVICE_URL:-http://localhost:8082}"
INITIAL_SERVICE_URL="${SERVICE_URL}/api/auth/status"
INTERNAL_API_KEY="${INTERNAL_API_KEY:-your-secure-internal-api-key}"

# Test data definitions
readonly STATUS_FIELDS="authenticated message"
readonly REGISTER_FIELDS_REQUEST='{
  "username": "int-test-user",
  "email": "int-test-user@example.com",
  "password": "securepassword"
}'
readonly REGISTER_FIELDS_RESPONSE="message user_id username"
readonly LOGIN_FIELDS_REQUEST='{"username": "int-test-user", "password": "securepassword"}'
readonly LOGIN_FIELDS_RESPONSE="access_token token_type expires_in"
readonly JWKS_FIELDS="keys"
readonly OPENID_CONFIGURATION_FIELDS="issuer \
  jwks_uri \
  authorization_endpoint \
  token_endpoint \
  userinfo_endpoint \
  response_types_supported \
  subject_types_supported \
  id_token_signing_alg_values_supported"

declare -A get_authentication_status
get_authentication_status["name"]="Get authentication status"
get_authentication_status["method"]="GET"
get_authentication_status["endpoint"]="/api/auth/status"
get_authentication_status["payload"]=""
get_authentication_status["api_key"]=""
get_authentication_status["expected_status"]="200"
get_authentication_status["expected_fields"]="${STATUS_FIELDS}"

declare -A register_user
register_user["name"]="Register user"
register_user["method"]="POST"
register_user["endpoint"]="/api/auth/register"
register_user["payload"]="${REGISTER_FIELDS_REQUEST}"
register_user["api_key"]="${INTERNAL_API_KEY}"
register_user["expected_status"]="200"
register_user["expected_fields"]="${REGISTER_FIELDS_RESPONSE}"

declare -A register_user_failed_duplicate_username
register_user_failed_duplicate_username["name"]="Register user failed (duplicate username)"
register_user_failed_duplicate_username["method"]="POST"
register_user_failed_duplicate_username["endpoint"]="/api/auth/register"
register_user_failed_duplicate_username["payload"]="${REGISTER_FIELDS_REQUEST}"
register_user_failed_duplicate_username["api_key"]="${INTERNAL_API_KEY}"
register_user_failed_duplicate_username["expected_status"]="409"
register_user_failed_duplicate_username["expected_fields"]=""

declare -A register_user_failed_invalid_api_key
register_user_failed_invalid_api_key["name"]="Register user failed (invalid API key)"
register_user_failed_invalid_api_key["method"]="POST"
register_user_failed_invalid_api_key["endpoint"]="/api/auth/register"
register_user_failed_invalid_api_key["payload"]="${REGISTER_FIELDS_REQUEST}"
register_user_failed_invalid_api_key["api_key"]="invalid-api-key"
register_user_failed_invalid_api_key["expected_status"]="401"
register_user_failed_invalid_api_key["expected_fields"]=""

declare -A register_user_failed_no_api_key
register_user_failed_no_api_key["name"]="Register user failed (no API key)"
register_user_failed_no_api_key["method"]="POST"
register_user_failed_no_api_key["endpoint"]="/api/auth/register"
register_user_failed_no_api_key["payload"]="${REGISTER_FIELDS_REQUEST}"
register_user_failed_no_api_key["api_key"]=""
register_user_failed_no_api_key["expected_status"]="401"
register_user_failed_no_api_key["expected_fields"]=""

declare -A login_user
login_user["name"]="Login user"
login_user["method"]="POST"
login_user["endpoint"]="/api/auth/login"
login_user["payload"]="${LOGIN_FIELDS_REQUEST}"
login_user["api_key"]=""
login_user["expected_status"]="200"
login_user["expected_fields"]="${LOGIN_FIELDS_RESPONSE}"

declare -A login_user_failed_invalid_credentials
login_user_failed_invalid_credentials["name"]="Login user failed (invalid credentials)"
login_user_failed_invalid_credentials["method"]="POST"
login_user_failed_invalid_credentials["endpoint"]="/api/auth/login"
login_user_failed_invalid_credentials["payload"]=""
login_user_failed_invalid_credentials["api_key"]=""
login_user_failed_invalid_credentials["expected_status"]="400"
login_user_failed_invalid_credentials["expected_fields"]=""

declare -A get_jwks
get_jwks["name"]="Get JWKS"
get_jwks["method"]="GET"
get_jwks["endpoint"]="/.well-known/jwks.json"
get_jwks["payload"]=""
get_jwks["api_key"]=""
get_jwks["expected_status"]="200"
get_jwks["expected_fields"]="${JWKS_FIELDS}"

declare -A get_openid_configuration
get_openid_configuration["name"]="Get OpenID configuration"
get_openid_configuration["method"]="GET"
get_openid_configuration["endpoint"]="/.well-known/openid-configuration"
get_openid_configuration["payload"]=""
get_openid_configuration["api_key"]=""
get_openid_configuration["expected_status"]="200"
get_openid_configuration["expected_fields"]="${OPENID_CONFIGURATION_FIELDS}"

AUTHENTICATION_TESTS_ARRAY=(
  # Authentication API tests
  get_authentication_status
  register_user
  register_user_failed_duplicate_username
  register_user_failed_invalid_api_key
  register_user_failed_no_api_key
  login_user
  login_user_failed_invalid_credentials

  # Standards & Discovery tests
  get_jwks
  get_openid_configuration
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
    
  run_tests "AUTHENTICATION_TESTS_ARRAY"
    
  print_summary
    
  exit ${FAILED_TESTS}
}

main "$@"
