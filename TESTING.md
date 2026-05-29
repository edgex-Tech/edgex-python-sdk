# EdgeX Python SDK Testing Documentation

This document provides an overview of the testing strategy for the EdgeX Python SDK, including which components are covered by tests and which are not.

## Table of Contents

- [Test Structure](#test-structure)
- [Unit Tests](#unit-tests)
  - [EIP-712 Signing Tests](#eip-712-signing-tests)
  - [Client Tests](#client-tests)
  - [Async Client Tests](#async-client-tests)
- [Integration Tests](#integration-tests)
  - [Account API Tests](#account-api-tests)
  - [Metadata API Tests](#metadata-api-tests)
  - [Order API Tests](#order-api-tests)
  - [Quote API Tests](#quote-api-tests)
  - [WebSocket API Tests](#websocket-api-tests)
- [Test Coverage](#test-coverage)
  - [Well-Covered Components](#well-covered-components)
  - [Partially Covered Components](#partially-covered-components)
  - [Components Lacking Coverage](#components-lacking-coverage)
- [Running Tests](#running-tests)
  - [Running Unit Tests](#running-unit-tests)
  - [Running Integration Tests](#running-integration-tests)
  - [Running Mock Tests](#running-mock-tests)
- [Test Environment](#test-environment)
- [Future Test Improvements](#future-test-improvements)

## Test Structure

The EdgeX Python SDK test suite is organized into two main categories:

1. **Unit Tests**: Located in `python_sdk/tests/`, these tests focus on individual components and functions without requiring external API connections.

2. **Integration Tests**: Located in `python_sdk/tests/integration/`, these tests verify the SDK's interaction with the EdgeX API endpoints.

## Unit Tests

### EIP-712 Signing Tests

File: `tests/test_eip712_signing.py`

These tests verify the v2 EIP-712 signing helpers used by order creation and signer address derivation.

**Coverage:**

- ✅ Address derivation from private keys
- ✅ Typed-data signing
- ✅ Basic signature shape validation

**Test Cases:**
- `test_derive_address_from_private_key`: Tests address derivation from a v2 trading key
- `test_sign_typed_data`: Tests typed-data signature generation

### Client Tests

File: `tests/test_client.py`

These tests verify the functionality of the main client class, which serves as the entry point for the SDK.

**Coverage:**

- ✅ Client initialization
- ✅ Parameter validation
- ✅ Method delegation to specialized clients

**Test Cases:**
- `test_init`: Tests client initialization with valid parameters
- `test_init_invalid_params`: Tests client initialization with invalid parameters

### Async Client Tests

File: `tests/test_async_client.py`

These tests verify the functionality of the async client helpers that handle low-level request preparation and signing helpers.

**Coverage:**

- ✅ Request signing
- ✅ Timestamp generation
- ✅ Header construction
- ✅ Parameter validation

**Test Cases:**
- `test_parse_resolution`: Tests resolution parsing
- `test_resolve_trading_signer_address`: Tests trading signer address derivation
- `test_sign_typed_data_with_trading_key`: Tests typed-data signing with the trading private key

## Integration Tests

Integration tests verify the SDK's interaction with the EdgeX API endpoints. Most of these tests require valid API credentials to pass, except for tests of public endpoints.

> **Note**: For information about public endpoints that can be tested without credentials, see [PUBLIC_ENDPOINTS.md](PUBLIC_ENDPOINTS.md).

### Account API Tests

File: `tests/integration/test_account.py`

**Coverage:**

- ✅ Account retrieval
- ✅ Asset information retrieval
- ✅ Position information retrieval
- ✅ Transaction history retrieval

**Test Cases:**
- `test_get_account_by_id`: Tests retrieving account information
- `test_get_account_asset`: Tests retrieving account asset information
- `test_get_account_positions`: Tests retrieving account positions
- `test_get_position_transaction_page`: Tests retrieving position transaction history
- `test_get_collateral_transaction_page`: Tests retrieving collateral transaction history

### Metadata API Tests

File: `tests/integration/test_metadata.py`

**Coverage:**

- ✅ Contract metadata retrieval
- ✅ Server time retrieval

**Test Cases:**
- `test_get_metadata`: Tests retrieving contract metadata
- `test_get_server_time`: Tests retrieving server time
- `test_contract_exists`: Tests checking if a contract exists

### Order API Tests

File: `tests/integration/test_order.py`

**Coverage:**

- ✅ Order creation
- ✅ Order cancellation
- ✅ Active order retrieval
- ✅ Order fill transaction retrieval
- ✅ Maximum order size retrieval

**Test Cases:**
- `test_create_and_cancel_order`: Tests creating and canceling an order
- `test_get_active_orders`: Tests retrieving active orders
- `test_get_order_fill_transactions`: Tests retrieving order fill transactions
- `test_get_max_order_size`: Tests retrieving maximum order size

### Quote API Tests

File: `tests/integration/test_quote.py`

**Coverage:**

- ✅ 24-hour quote retrieval
- ✅ K-line data retrieval
- ✅ Order book depth retrieval
- ✅ Multi-contract K-line data retrieval

**Test Cases:**
- `test_get_24_hour_quote`: Tests retrieving 24-hour quotes
- `test_get_k_line`: Tests retrieving K-line data
- `test_get_order_book_depth`: Tests retrieving order book depth
- `test_get_multi_contract_k_line`: Tests retrieving multi-contract K-line data

### WebSocket API Tests

File: `tests/integration/test_websocket.py`

**Coverage:**

- ✅ Public WebSocket connection
- ✅ Private WebSocket connection
- ✅ Subscription to various channels
- ✅ Message handling

**Test Cases:**
- `test_public_websocket`: Tests connecting to the public WebSocket
- `test_private_websocket`: Tests connecting to the private WebSocket

## Test Coverage

### Well-Covered Components

The following components have good test coverage:

1. **EIP-712 Signing Helpers**: Comprehensive unit tests for the v2 order-signing flow
2. **Client Initialization**: Thorough testing of parameter validation and initialization
3. **API Endpoint Structure**: Integration tests cover all major API endpoints

### Partially Covered Components

The following components have partial test coverage:

1. **Error Handling**: Some error conditions are tested, but not all possible error scenarios
2. **WebSocket Message Handling**: Basic connection is tested, but not all message types
3. **Response Parsing**: Basic parsing is tested, but not all edge cases

### Components Lacking Coverage

The following components could benefit from additional test coverage:

1. **Reconnection Logic**: WebSocket reconnection logic is not thoroughly tested
2. **Rate Limiting**: Handling of API rate limits is not tested
3. **Long-Running Operations**: Tests for long-running operations or pagination
4. **Concurrency**: Tests for concurrent API calls
5. **Transfer and Asset Clients**: Missing dedicated integration tests

## Running Tests

### Running Unit Tests

To run all unit tests:

```bash
cd python_sdk
python -m unittest discover tests
```

To run a specific test file:

```bash
cd python_sdk
python -m unittest tests/test_eip712_signing.py
```

### Running Integration Tests

To run integration tests with real API credentials:

```bash
cd python_sdk
python run_integration_tests.py
```

**Note**: This requires setting the following environment variables:
- `EDGEX_BASE_URL`: The base URL for the EdgeX API
- `EDGEX_WS_URL`: The WebSocket URL for the EdgeX API
- `EDGEX_ACCOUNT_ID`: Your EdgeX account ID
- `EDGEX_TRADING_PRIVATE_KEY`: Your trading private key
- `EDGEX_API_KEY`: Your API key
- `EDGEX_API_PASSPHRASE`: Your API passphrase
- `EDGEX_API_SECRET`: Your API secret

Example:
```bash
export EDGEX_ACCOUNT_ID="your_account_id_here"
export EDGEX_TRADING_PRIVATE_KEY="your_trading_private_key_here"
export EDGEX_API_KEY="your_api_key_here"
export EDGEX_API_PASSPHRASE="your_api_passphrase_here"
export EDGEX_API_SECRET="your_api_secret_here"
```

**⚠️ SECURITY WARNING**: Never commit these credentials to version control. Always use environment variables or secure credential management systems.

### Running Public Endpoint Tests

To run only the tests for public endpoints (which don't require authentication):

```bash
cd python_sdk
python run_public_tests.py
```

This script uses dummy values for the required environment variables and only tests endpoints that don't require authentication.

**Note**: Some tests, particularly the WebSocket test, may be skipped due to connection issues or API limitations. This is expected behavior and doesn't indicate a problem with the SDK.

### Running Mock Tests

To run integration tests with mock values (for testing the SDK structure without real API calls):

```bash
cd python_sdk
python run_mock_tests.py
```

## Test Environment

The tests are designed to run in the following environments:

- **Unit Tests**: Can run in any environment with Python 3.7+
- **Integration Tests**: Require access to the EdgeX API
- **Mock Tests**: Can run in any environment with Python 3.7+

## Future Test Improvements

The following improvements could be made to the test suite:

1. **Separate Public and Private Endpoint Tests**: Fully separate tests for public endpoints from those requiring authentication

1. **Increased Unit Test Coverage**: Add tests for edge cases and error conditions
2. **Mocking External Dependencies**: Use mocks for API responses to test more scenarios
3. **Property-Based Testing**: Implement property-based testing for cryptographic operations
4. **Performance Testing**: Add tests for performance and resource usage
5. **Dedicated Transfer and Asset Tests**: Add dedicated integration tests for these clients
6. **WebSocket Message Testing**: Add more tests for different WebSocket message types
7. **Concurrency Testing**: Add tests for concurrent API calls
8. **Long-Running Operation Testing**: Add tests for pagination and long-running operations
