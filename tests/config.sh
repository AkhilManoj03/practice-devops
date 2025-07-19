#!/bin/bash
# 
# Centralized Configuration - Defines default values and processes environment variables
# for global settings.

# Default Values (Lowest Priority)
DEFAULT_GLOBAL_TIMEOUT=10
DEFAULT_GLOBAL_VERBOSE="false"
DEFAULT_GLOBAL_PARALLEL_MODE="false"

# Global Configuration Variables (potentially overridden by env vars)
# These will be explicitly overwritten by command-line arguments.
GLOBAL_TIMEOUT="${TIMEOUT:-$DEFAULT_GLOBAL_TIMEOUT}"
GLOBAL_VERBOSE="${VERBOSE:-$DEFAULT_GLOBAL_VERBOSE}"
GLOBAL_PARALLEL_MODE="${PARALLEL_MODE:-$DEFAULT_GLOBAL_PARALLEL_MODE}"

# Placeholder for SERVICE_URL and INITIAL_SERVICE_URL
# These will be set by individual test suites.
SERVICE_URL=""
INITIAL_SERVICE_URL=""
