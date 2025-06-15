# Tests

This directory contains test scripts for the Datadog MCP Server functionality.

## Test Files

### Core Functionality Tests
- `test_server.py` - Basic server functionality and API connectivity
- `test_simple.py` - Simple component imports and basic operations
- `test_modular.py` - Modular architecture component testing

### Feature-Specific Tests
- `test_logs.py` - Service logs functionality testing
- `test_env_logs.py` - Environment-specific log filtering tests
- `test_metrics.py` - Basic metrics functionality testing
- `test_metrics_debug.py` - Metrics API debugging and troubleshooting
- `test_metrics_final.py` - Complete metrics testing with real data
- `test_teams.py` - Team management functionality testing

## Running Tests

### Prerequisites
Make sure you have the required environment variables set:
```bash
export DD_API_KEY="your-datadog-api-key"
export DD_APP_KEY="your-datadog-application-key"
```

### Individual Test Execution
```bash
# From the project root directory
python tests/test_server.py
python tests/test_logs.py
python tests/test_metrics_final.py
python tests/test_teams.py
```

### Running All Tests
```bash
# Run all tests (from project root)
for test in tests/test_*.py; do
    echo "Running $test..."
    python "$test"
    echo "---"
done
```

## Test Coverage

The tests cover:
- ✅ **API Connectivity** - Datadog API authentication and basic connectivity
- ✅ **CI/CD Pipelines** - Pipeline listing and fingerprint extraction
- ✅ **Service Logs** - Log retrieval with environment and time filtering
- ✅ **Service Metrics** - Metrics collection and statistical analysis
- ✅ **Team Management** - Team discovery and member listing
- ✅ **Data Formatting** - Table, summary, and JSON output formats
- ✅ **Error Handling** - Graceful error handling and reporting

## Notes

- Tests require valid Datadog API credentials
- Some tests may return no data depending on your Datadog account setup
- Tests are designed to be non-destructive (read-only operations)
- Debug tests include additional logging for troubleshooting API issues