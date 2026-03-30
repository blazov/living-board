# API Reference Documentation
## Meridian Payments API — v2.1

**Base URL:** `https://api.meridianpay.io/v2`
**Documentation Version:** 2.1.4
**Last Updated:** March 2026

---

## Overview

The Meridian Payments API is a RESTful API that allows you to accept payments, manage subscriptions, issue refunds, and retrieve transaction data programmatically. The API uses standard HTTP methods, accepts JSON request bodies, and returns JSON responses.

All API requests must be made over HTTPS. Requests made over plain HTTP will be rejected.

### What you can do with this API

- Charge cards, wallets, and bank accounts (one-time and recurring)
- Create and manage subscription plans and customer billing cycles
- Issue full or partial refunds
- Retrieve payment history, invoices, and payout schedules
- Register webhooks to receive real-time event notifications

---

## Authentication

All API requests require authentication using your API keys. Meridian uses two types of API keys:

| Key Type | Prefix | Usage |
|---|---|---|
| Secret key | `sk_live_` / `sk_test_` | Server-side requests only. Never expose in client-side code. |
| Publishable key | `pk_live_` / `pk_test_` | Client-side (browser/mobile). Safe to include in frontend code. |

Authenticate by including your secret key in the `Authorization` header using HTTP Basic Auth. Pass the secret key as the username with an empty password:

```bash
curl https://api.meridianpay.io/v2/charges \
  -u sk_live_4xKj9...AbC2:
```

Or as a Bearer token:

```bash
curl https://api.meridianpay.io/v2/charges \
  -H "Authorization: Bearer sk_live_4xKj9...AbC2"
```

> **Security warning:** Never include your secret key in client-side code, GitHub repositories, or any location accessible to end users. Rotate your key immediately if you suspect it has been exposed. See [Key Management](#key-management).

### Test vs. Live Mode

Keys prefixed with `sk_test_` and `pk_test_` operate in test mode. Test mode transactions do not process real money and do not affect your live data. Use the [test card numbers](#test-cards) provided in the Testing section.

Keys prefixed with `sk_live_` and `pk_live_` process real payments. Switch to live mode only when you are ready to go live.

---

## Rate Limits

| Plan | Requests per second | Requests per minute |
|---|---|---|
| Starter | 25 | 1,000 |
| Growth | 100 | 5,000 |
| Enterprise | Custom | Custom |

When you exceed the rate limit, the API returns a `429 Too Many Requests` response. Implement exponential backoff in your retry logic.

```json
{
  "error": {
    "type": "rate_limit_error",
    "code": "rate_limit_exceeded",
    "message": "Too many requests. Please retry after 1 second.",
    "retry_after": 1
  }
}
```

---

## Request & Response Format

### Request format

- All `POST` and `PUT` requests must include a `Content-Type: application/json` header
- Request bodies must be valid JSON
- Timestamps should be ISO 8601 format (`2026-03-15T14:32:00Z`)
- Currency amounts are expressed as integers in the **smallest currency unit** (e.g., cents for USD, pence for GBP). A charge of $12.50 USD is represented as `1250`.

### Response format

All responses return a JSON object. Successful responses include the requested resource. Error responses include an `error` object (see [Error Handling](#error-handling)).

### Idempotency

For `POST` requests, you can include an `Idempotency-Key` header to safely retry requests without creating duplicate charges. The key must be a unique string (UUID recommended). Idempotency keys expire after 24 hours.

```bash
curl https://api.meridianpay.io/v2/charges \
  -H "Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000" \
  -u sk_live_4xKj9...AbC2 \
  ...
```

---

## Endpoints

---

### Charges

A `Charge` object represents a payment attempt. Charges can succeed, fail, or be refunded.

#### The Charge object

```json
{
  "id": "ch_1A2B3C4D5E6F",
  "object": "charge",
  "amount": 2499,
  "currency": "usd",
  "status": "succeeded",
  "captured": true,
  "description": "Pro plan — March 2026",
  "customer": "cus_9Z8Y7X6W",
  "payment_method": "pm_3E4F5G6H",
  "receipt_url": "https://receipt.meridianpay.io/r/ch_1A2B3C4D5E6F",
  "metadata": {
    "order_id": "ord_98765",
    "user_id": "usr_44321"
  },
  "created": "2026-03-15T14:32:00Z",
  "failure_code": null,
  "failure_message": null,
  "refunded": false,
  "amount_refunded": 0
}
```

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier for the charge. Prefix: `ch_` |
| `amount` | integer | Amount in the smallest currency unit (e.g., cents) |
| `currency` | string | Three-letter ISO 4217 currency code (lowercase) |
| `status` | string | `pending`, `succeeded`, or `failed` |
| `captured` | boolean | Whether the charge has been captured. Uncaptured charges are authorized but not yet settled. |
| `customer` | string | ID of the customer, if associated |
| `payment_method` | string | ID of the payment method used |
| `metadata` | object | Up to 20 key-value pairs for your own reference. Keys and values are strings. |
| `failure_code` | string | Error code if the charge failed. See [Failure Codes](#failure-codes). |
| `failure_message` | string | Human-readable failure description |

---

#### `POST /charges` — Create a charge

Creates a new payment charge.

**Parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `amount` | integer | Yes | Amount in smallest currency unit |
| `currency` | string | Yes | Three-letter ISO 4217 currency code |
| `payment_method` | string | Yes* | ID of a saved payment method (*required unless `customer` with default method is provided) |
| `customer` | string | No | ID of an existing customer. If provided with a default payment method, `payment_method` can be omitted. |
| `description` | string | No | Arbitrary description shown on receipts and in the dashboard |
| `capture` | boolean | No | Default: `true`. Set to `false` to authorize only (two-step auth/capture flow). |
| `metadata` | object | No | Key-value pairs for your reference (not visible to customers) |
| `receipt_email` | string | No | Email address to send a receipt to. Overrides customer's email if both are set. |
| `statement_descriptor` | string | No | Text that appears on the customer's bank statement (max 22 characters) |

**Example request**

```bash
curl https://api.meridianpay.io/v2/charges \
  -u sk_live_4xKj9...AbC2 \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "amount": 2499,
    "currency": "usd",
    "payment_method": "pm_3E4F5G6H",
    "customer": "cus_9Z8Y7X6W",
    "description": "Pro plan — March 2026",
    "receipt_email": "user@example.com",
    "metadata": {
      "order_id": "ord_98765"
    }
  }'
```

**Example response** — `200 OK`

```json
{
  "id": "ch_1A2B3C4D5E6F",
  "object": "charge",
  "amount": 2499,
  "currency": "usd",
  "status": "succeeded",
  "captured": true,
  "description": "Pro plan — March 2026",
  "customer": "cus_9Z8Y7X6W",
  "payment_method": "pm_3E4F5G6H",
  "receipt_url": "https://receipt.meridianpay.io/r/ch_1A2B3C4D5E6F",
  "metadata": {
    "order_id": "ord_98765"
  },
  "created": "2026-03-15T14:32:00Z",
  "failure_code": null,
  "failure_message": null,
  "refunded": false,
  "amount_refunded": 0
}
```

---

#### `GET /charges/:id` — Retrieve a charge

Returns a charge object by ID.

```bash
curl https://api.meridianpay.io/v2/charges/ch_1A2B3C4D5E6F \
  -u sk_live_4xKj9...AbC2
```

**Response** — `200 OK`: Returns the [Charge object](#the-charge-object).

---

#### `GET /charges` — List charges

Returns a paginated list of charges.

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `customer` | string | Filter by customer ID |
| `status` | string | Filter by status: `pending`, `succeeded`, `failed` |
| `created[gte]` | timestamp | Filter charges created on or after this timestamp |
| `created[lte]` | timestamp | Filter charges created on or before this timestamp |
| `limit` | integer | Number of results per page. Default: 10. Max: 100. |
| `starting_after` | string | Pagination cursor. Returns results after this charge ID. |

**Example request**

```bash
curl "https://api.meridianpay.io/v2/charges?customer=cus_9Z8Y7X6W&limit=25&status=succeeded" \
  -u sk_live_4xKj9...AbC2
```

**Example response** — `200 OK`

```json
{
  "object": "list",
  "data": [
    { "id": "ch_1A2B3C4D5E6F", ... },
    { "id": "ch_2B3C4D5E6F7G", ... }
  ],
  "has_more": true,
  "next_cursor": "ch_2B3C4D5E6F7G",
  "total_count": 143
}
```

---

### Refunds

A `Refund` object represents a refund issued against a charge. Partial refunds are supported.

#### `POST /refunds` — Create a refund

| Parameter | Type | Required | Description |
|---|---|---|---|
| `charge` | string | Yes | ID of the charge to refund |
| `amount` | integer | No | Amount to refund in smallest currency unit. Omit for full refund. |
| `reason` | string | No | `duplicate`, `fraudulent`, or `requested_by_customer` |
| `metadata` | object | No | Key-value pairs for your reference |

**Example request — Partial refund**

```bash
curl https://api.meridianpay.io/v2/refunds \
  -u sk_live_4xKj9...AbC2 \
  -H "Content-Type: application/json" \
  -d '{
    "charge": "ch_1A2B3C4D5E6F",
    "amount": 1000,
    "reason": "requested_by_customer"
  }'
```

**Example response** — `200 OK`

```json
{
  "id": "re_7G8H9I0J1K2L",
  "object": "refund",
  "charge": "ch_1A2B3C4D5E6F",
  "amount": 1000,
  "currency": "usd",
  "status": "succeeded",
  "reason": "requested_by_customer",
  "created": "2026-03-15T16:00:00Z"
}
```

> **Note:** Refunds typically take 5–10 business days to appear on the customer's statement, depending on their bank. Refunds on card charges are settled within 3–7 business days in most cases.

---

### Customers

Customer objects store payment methods, billing details, and subscription information for repeat users.

#### `POST /customers` — Create a customer

| Parameter | Type | Required | Description |
|---|---|---|---|
| `email` | string | No | Customer email (used for receipts) |
| `name` | string | No | Full name |
| `phone` | string | No | E.164 format (e.g., `+14155552671`) |
| `payment_method` | string | No | ID of a payment method to attach as default |
| `metadata` | object | No | Key-value pairs for your reference |

**Example request**

```bash
curl https://api.meridianpay.io/v2/customers \
  -u sk_live_4xKj9...AbC2 \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jane@example.com",
    "name": "Jane Doe",
    "metadata": {
      "internal_user_id": "usr_44321"
    }
  }'
```

**Example response** — `201 Created`

```json
{
  "id": "cus_9Z8Y7X6W",
  "object": "customer",
  "email": "jane@example.com",
  "name": "Jane Doe",
  "phone": null,
  "default_payment_method": null,
  "metadata": {
    "internal_user_id": "usr_44321"
  },
  "created": "2026-03-15T12:00:00Z"
}
```

---

### Payment Methods

Payment method objects represent a customer's payment instrument (card, bank account, etc.). Use your publishable key with the Meridian.js client library to collect and tokenize payment details on the frontend. Never send raw card numbers to your server.

#### `POST /payment_methods` — Attach a payment method to a customer

```bash
curl https://api.meridianpay.io/v2/payment_methods/pm_3E4F5G6H/attach \
  -u sk_live_4xKj9...AbC2 \
  -H "Content-Type: application/json" \
  -d '{"customer": "cus_9Z8Y7X6W"}'
```

---

## Webhooks

Webhooks allow Meridian to push real-time event notifications to your server, so you don't need to poll the API for status changes.

### Configuring webhooks

Register a webhook endpoint in the Meridian Dashboard under **Settings → Webhooks**, or via the API:

```bash
curl https://api.meridianpay.io/v2/webhooks \
  -u sk_live_4xKj9...AbC2 \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/meridian",
    "events": ["charge.succeeded", "charge.failed", "refund.created"]
  }'
```

### Available events

| Event | Triggered when |
|---|---|
| `charge.created` | A charge object is created |
| `charge.succeeded` | A charge is successfully captured |
| `charge.failed` | A charge attempt fails |
| `charge.refunded` | A charge is refunded (full or partial) |
| `refund.created` | A refund is issued |
| `customer.created` | A new customer is created |
| `payment_method.attached` | A payment method is attached to a customer |
| `subscription.created` | A subscription is created |
| `subscription.canceled` | A subscription is canceled |
| `invoice.paid` | A subscription invoice is paid |
| `invoice.payment_failed` | A subscription invoice payment fails |

### Webhook payload format

```json
{
  "id": "evt_5M6N7O8P9Q0R",
  "object": "event",
  "type": "charge.succeeded",
  "created": "2026-03-15T14:32:00Z",
  "data": {
    "object": {
      "id": "ch_1A2B3C4D5E6F",
      "object": "charge",
      "amount": 2499,
      "status": "succeeded",
      ...
    }
  }
}
```

### Verifying webhook signatures

Meridian signs all webhook payloads with a signature in the `Meridian-Signature` header. Always verify this signature before processing the event.

```python
import hmac
import hashlib

def verify_webhook_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """
    Verify the Meridian webhook signature.

    Args:
        payload_body: Raw request body bytes (do not parse JSON first)
        signature_header: Value of the Meridian-Signature header
        secret: Your webhook signing secret (from the Dashboard)

    Returns:
        True if the signature is valid, False otherwise
    """
    # Parse the header: "t=timestamp,v1=signature"
    parts = dict(item.split("=", 1) for item in signature_header.split(","))
    timestamp = parts.get("t")
    received_sig = parts.get("v1")

    if not timestamp or not received_sig:
        return False

    # Construct the signed payload string
    signed_payload = f"{timestamp}.{payload_body.decode('utf-8')}"

    # Compute expected signature
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_sig, received_sig)
```

> **Important:** Use the raw request body bytes for signature verification — not the parsed JSON. Parsing and re-serializing will change whitespace and may invalidate the signature.

---

## Error Handling

The API uses standard HTTP status codes to indicate success or failure.

### HTTP status codes

| Code | Meaning |
|---|---|
| `200 OK` | Request succeeded |
| `201 Created` | Resource created successfully |
| `400 Bad Request` | Invalid parameters or request body |
| `401 Unauthorized` | Missing or invalid API key |
| `402 Payment Required` | The payment was declined |
| `403 Forbidden` | API key does not have permission for this action |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | Duplicate idempotency key with different parameters |
| `422 Unprocessable Entity` | Request was well-formed but could not be processed |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Unexpected server error |
| `503 Service Unavailable` | Temporary service disruption |

### Error object format

```json
{
  "error": {
    "type": "card_error",
    "code": "card_declined",
    "message": "Your card was declined. Please contact your bank or try a different payment method.",
    "param": "payment_method",
    "charge": "ch_1A2B3C4D5E6F",
    "decline_code": "insufficient_funds",
    "doc_url": "https://docs.meridianpay.io/errors/card_declined"
  }
}
```

| Field | Description |
|---|---|
| `type` | Error category (see table below) |
| `code` | Machine-readable error code |
| `message` | Human-readable description — safe to display to users for `card_error` types |
| `param` | The request parameter that caused the error, if applicable |
| `decline_code` | For `card_error` type: the issuer's specific decline reason |

### Error types

| Type | Description | Suggested handling |
|---|---|---|
| `api_error` | Unexpected error on Meridian's side | Log and retry with exponential backoff |
| `authentication_error` | Invalid API key | Check key, do not retry |
| `card_error` | Card was declined by issuer | Show `message` to user; prompt retry |
| `idempotency_error` | Idempotency key reused with different params | Use a new idempotency key |
| `invalid_request_error` | Missing or invalid parameter | Fix the request; do not retry |
| `rate_limit_error` | Too many requests | Retry after `retry_after` seconds |

### Failure codes

Card charge failure codes appear in `charge.failure_code`:

| Failure Code | Description |
|---|---|
| `card_declined` | Card declined by issuer (see `decline_code` for specifics) |
| `expired_card` | Card expiration date has passed |
| `incorrect_cvc` | CVC number does not match |
| `incorrect_number` | Card number is invalid |
| `insufficient_funds` | Insufficient funds on the card |
| `lost_card` | Card reported as lost |
| `stolen_card` | Card reported as stolen |
| `processing_error` | Error processing the card — retry |
| `do_not_honor` | Generic decline from issuer |

---

## Testing

Use test mode keys (`sk_test_...`) to test without processing real payments.

### Test cards

| Card Number | Brand | Behavior |
|---|---|---|
| `4242 4242 4242 4242` | Visa | Succeeds |
| `4000 0000 0000 0002` | Visa | Declines with `card_declined` |
| `4000 0000 0000 9995` | Visa | Declines with `insufficient_funds` |
| `4000 0000 0000 0069` | Visa | Declines with `expired_card` |
| `4000 0000 0000 0127` | Visa | Declines with `incorrect_cvc` |
| `5555 5555 5555 4444` | Mastercard | Succeeds |
| `3782 822463 10005` | American Express | Succeeds |

Use any future expiration date (e.g., `12/30`), any 3-digit CVC, and any 5-digit ZIP code for test cards.

### Simulating webhooks

In test mode, you can trigger webhook events from the Dashboard under **Developers → Webhooks → Send test event**, or via the CLI:

```bash
meridian trigger charge.succeeded
```

---

## Best Practices

### Security

**Never log raw card numbers or CVCs.** Even in test mode, treat card data as sensitive.

**Rotate API keys regularly** and immediately if you suspect a compromise. Set up key rotation alerts in the Dashboard.

**Validate webhook signatures** before acting on any event. Do not assume a request to your webhook URL is legitimate without verification.

**Use idempotency keys** on all `POST` requests to prevent duplicate charges from network retries.

### Reliability

**Implement exponential backoff** for retries on `5xx` errors and `rate_limit_error`. A simple pattern:

```python
import time
import random

def retry_with_backoff(fn, max_retries=4):
    for attempt in range(max_retries):
        try:
            return fn()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait)
```

**Subscribe to status updates** at status.meridianpay.io to receive alerts about service disruptions.

**Use separate API keys** for each environment (development, staging, production) and each service in your infrastructure.

### Performance

**Avoid polling** — use webhooks to receive real-time state changes instead of repeatedly calling `GET /charges/:id`.

**Use cursor-based pagination** (`starting_after`) rather than offset pagination for large datasets. Offset pagination can miss records when data changes between requests.

**Cache customer and payment method IDs** in your database to avoid repeated lookups. Don't store sensitive card data — only the IDs returned by Meridian.

---

## Key Management

| Action | How |
|---|---|
| View API keys | Dashboard → Settings → API Keys |
| Create a new key | Dashboard → Settings → API Keys → Create key |
| Rotate a key | Create a new key, update your services, then revoke the old key |
| Revoke a key | Dashboard → Settings → API Keys → Revoke |
| Restrict key permissions | Set key scopes to limit to specific resources (e.g., read-only) |

**Never commit API keys to source control.** Store them in environment variables or a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.).

---

## Changelog

| Version | Date | Changes |
|---|---|---|
| v2.1 | Jan 2026 | Added `statement_descriptor` parameter to charges; new `invoice.*` webhook events |
| v2.0 | Aug 2025 | Introduced cursor-based pagination; deprecated `offset` param; new unified error format |
| v1.9 | Mar 2025 | Added partial refund support; `decline_code` field on charge failures |
| v1.8 | Nov 2024 | Webhook signature verification; new `payment_method.attached` event |

---

## Support

- **Documentation:** docs.meridianpay.io
- **API Status:** status.meridianpay.io
- **Developer community:** community.meridianpay.io
- **Email support:** api-support@meridianpay.io (response within 1 business day)
- **Enterprise support:** Dedicated Slack channel and 4-hour SLA (Enterprise plan)

---

*Documentation written by [Freelancer Name] — Technical Writer specializing in API documentation and developer experience*
*Available for documentation projects on Upwork and Fiverr*
