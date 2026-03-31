# Meridian Payments API — Developer Reference

**Version:** 2.4
**Base URL:** `https://api.meridianpay.io/v2`
**Last updated:** March 2026

---

## Table of Contents

1. [Authentication](#authentication)
2. [Endpoints](#endpoints)
   - [Payments](#payments)
   - [Refunds](#refunds)
   - [Customers](#customers)
   - [Payment Methods](#payment-methods)
3. [Rate Limits](#rate-limits)
4. [Idempotency](#idempotency)
5. [Webhooks](#webhooks)
6. [Error Handling](#error-handling)
7. [Test Cards](#test-cards)
8. [Best Practices](#best-practices)
9. [Changelog](#changelog)

---

## Authentication

The Meridian API uses API keys to authenticate requests. Your keys are available in the [Meridian Dashboard](https://dashboard.meridianpay.io) under **Settings → API Keys**.

### Key types

| Key type | Prefix | Usage |
|---|---|---|
| Secret key | `sk_live_` / `sk_test_` | Server-side only. Never expose in client code or version control. |
| Publishable key | `pk_live_` / `pk_test_` | Safe for client-side use. Only creates tokens and payment intents. |

### How to authenticate

Pass your secret key as a Bearer token in the `Authorization` header of every request:

```http
Authorization: Bearer sk_test_EXAMPLE_KEY_DO_NOT_USE
```

### Test vs. live mode

All test-mode requests use keys prefixed with `_test_` and operate against a sandboxed environment with no real financial movement. Live-mode keys are prefixed with `_live_`. You cannot mix modes in a single request — a test secret key will always return test-mode results.

```bash
# Test mode
curl https://api.meridianpay.io/v2/payments \
  -H "Authorization: Bearer sk_test_EXAMPLE_KEY_DO_NOT_USE"

# Live mode
curl https://api.meridianpay.io/v2/payments \
  -H "Authorization: Bearer sk_live_51NzRQ2GC8U..."
```

---

## Endpoints

### Payments

A **Payment** object represents a single attempt to move money from a customer to your account. Payments can be in one of the following states: `pending`, `processing`, `succeeded`, `failed`, or `canceled`.

---

#### Create a Payment

```
POST /v2/payments
```

Creates a new payment. If successful, returns a Payment object with `status: "processing"`. Use webhooks or polling to confirm the final outcome.

**Request headers**

| Header | Required | Description |
|---|---|---|
| `Authorization` | Yes | `Bearer <secret_key>` |
| `Content-Type` | Yes | `application/json` |
| `Idempotency-Key` | Recommended | Unique key to safely retry this request (see [Idempotency](#idempotency)) |

**Request body parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `amount` | integer | Yes | Amount in the smallest currency unit (e.g., cents for USD). Minimum: 50 ($0.50). |
| `currency` | string | Yes | ISO 4217 currency code, lowercase (e.g., `"usd"`, `"eur"`). |
| `payment_method` | string | Yes | ID of a saved Payment Method, or pass `payment_method_data` instead. |
| `customer` | string | No | ID of a Customer object to associate with this payment. |
| `description` | string | No | Arbitrary string describing the payment (max 1,000 characters). Visible in the dashboard. |
| `metadata` | object | No | Set of key-value pairs for your own use. Keys must be strings; values must be strings or numbers. Max 50 keys. |
| `confirm` | boolean | No | If `true`, confirm the payment immediately (default: `false`). |
| `capture_method` | string | No | `"automatic"` (default) or `"manual"`. Use `manual` to place a hold and capture later. |

**Example request**

```bash
curl -X POST https://api.meridianpay.io/v2/payments \
  -H "Authorization: Bearer sk_test_EXAMPLE_KEY_DO_NOT_USE" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order_12345_attempt_1" \
  -d '{
    "amount": 4999,
    "currency": "usd",
    "payment_method": "pm_1Nz6c2GC8U4eTbh0X3fJ",
    "customer": "cus_PaJRn4B8kA2m",
    "description": "Annual subscription — Pro Plan",
    "confirm": true,
    "metadata": {
      "order_id": "ord_12345",
      "product_id": "pro_annual"
    }
  }'
```

**Example response** `200 OK`

```json
{
  "id": "pay_3NzRQ2GC8U4eTbh0Yw7K",
  "object": "payment",
  "amount": 4999,
  "currency": "usd",
  "status": "succeeded",
  "payment_method": "pm_1Nz6c2GC8U4eTbh0X3fJ",
  "customer": "cus_PaJRn4B8kA2m",
  "description": "Annual subscription — Pro Plan",
  "created": 1711843200,
  "captured_at": 1711843201,
  "capture_method": "automatic",
  "metadata": {
    "order_id": "ord_12345",
    "product_id": "pro_annual"
  },
  "livemode": false
}
```

---

#### Retrieve a Payment

```
GET /v2/payments/{payment_id}
```

Retrieves the details of a Payment object by its ID.

**Path parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `payment_id` | string | Yes | The ID of the payment to retrieve. |

**Example request**

```bash
curl https://api.meridianpay.io/v2/payments/pay_3NzRQ2GC8U4eTbh0Yw7K \
  -H "Authorization: Bearer sk_test_EXAMPLE_KEY_DO_NOT_USE"
```

**Example response** `200 OK`

```json
{
  "id": "pay_3NzRQ2GC8U4eTbh0Yw7K",
  "object": "payment",
  "amount": 4999,
  "currency": "usd",
  "status": "succeeded",
  "created": 1711843200,
  "captured_at": 1711843201,
  "livemode": false
}
```

---

### Refunds

A **Refund** object represents a reversal of a captured payment. Refunds can be full or partial. Once issued, refunds cannot be canceled.

---

#### Create a Refund

```
POST /v2/refunds
```

**Request body parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `payment` | string | Yes | ID of the payment to refund. |
| `amount` | integer | No | Amount to refund in smallest currency unit. Omit to issue a full refund. |
| `reason` | string | No | `"duplicate"`, `"fraudulent"`, or `"requested_by_customer"`. |
| `metadata` | object | No | Key-value metadata for your records. |

**Example request**

```bash
curl -X POST https://api.meridianpay.io/v2/refunds \
  -H "Authorization: Bearer sk_test_EXAMPLE_KEY_DO_NOT_USE" \
  -H "Content-Type: application/json" \
  -d '{
    "payment": "pay_3NzRQ2GC8U4eTbh0Yw7K",
    "amount": 2500,
    "reason": "requested_by_customer",
    "metadata": {
      "support_ticket": "tkt_8821"
    }
  }'
```

**Example response** `200 OK`

```json
{
  "id": "ref_5KpYT1AB9Vr2mNc0Xz3Q",
  "object": "refund",
  "amount": 2500,
  "currency": "usd",
  "payment": "pay_3NzRQ2GC8U4eTbh0Yw7K",
  "status": "succeeded",
  "reason": "requested_by_customer",
  "created": 1711930400,
  "metadata": {
    "support_ticket": "tkt_8821"
  }
}
```

---

### Customers

A **Customer** object stores a customer's contact information and saved payment methods. Using Customer objects is strongly recommended for recurring billing — it enables one-click payments and simplifies PCI compliance.

---

#### Create a Customer

```
POST /v2/customers
```

**Request body parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `email` | string | No | Customer's email address. |
| `name` | string | No | Full name. |
| `phone` | string | No | E.164 format phone number (e.g., `"+14155552671"`). |
| `address` | object | No | Billing address. Contains `line1`, `line2`, `city`, `state`, `postal_code`, `country`. |
| `metadata` | object | No | Key-value metadata. Useful for linking to your own customer ID. |

**Example request**

```bash
curl -X POST https://api.meridianpay.io/v2/customers \
  -H "Authorization: Bearer sk_test_EXAMPLE_KEY_DO_NOT_USE" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alex@example.com",
    "name": "Alex Rivera",
    "metadata": {
      "internal_user_id": "usr_00923"
    }
  }'
```

**Example response** `200 OK`

```json
{
  "id": "cus_PaJRn4B8kA2m",
  "object": "customer",
  "email": "alex@example.com",
  "name": "Alex Rivera",
  "created": 1711790000,
  "default_payment_method": null,
  "metadata": {
    "internal_user_id": "usr_00923"
  },
  "livemode": false
}
```

---

### Payment Methods

A **Payment Method** object stores the details of a payment instrument (card, bank account, etc.) for reuse. Payment Methods must be attached to a Customer before they can be charged without user input.

---

#### Attach a Payment Method

```
POST /v2/payment_methods/{payment_method_id}/attach
```

Attaches a Payment Method to a Customer. After attaching, the method can be used in future payments without re-entering card details.

**Path parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `payment_method_id` | string | Yes | ID of the Payment Method to attach. |

**Request body parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `customer` | string | Yes | ID of the Customer to attach the Payment Method to. |

**Example request**

```bash
curl -X POST https://api.meridianpay.io/v2/payment_methods/pm_1Nz6c2GC8U4eTbh0X3fJ/attach \
  -H "Authorization: Bearer sk_test_EXAMPLE_KEY_DO_NOT_USE" \
  -H "Content-Type: application/json" \
  -d '{ "customer": "cus_PaJRn4B8kA2m" }'
```

**Example response** `200 OK`

```json
{
  "id": "pm_1Nz6c2GC8U4eTbh0X3fJ",
  "object": "payment_method",
  "type": "card",
  "card": {
    "brand": "visa",
    "last4": "4242",
    "exp_month": 12,
    "exp_year": 2028,
    "funding": "credit"
  },
  "customer": "cus_PaJRn4B8kA2m",
  "created": 1711795000,
  "livemode": false
}
```

---

## Rate Limits

To protect the stability of the API for all users, requests are rate-limited per API key.

| Plan | Read requests | Write requests |
|---|---|---|
| Test mode (all plans) | 100 req/sec | 100 req/sec |
| Starter (live) | 100 req/sec | 50 req/sec |
| Growth (live) | 500 req/sec | 250 req/sec |
| Enterprise (live) | Custom | Custom |

When you exceed a rate limit, the API returns a `429 Too Many Requests` response:

```json
{
  "error": {
    "type": "rate_limit_error",
    "code": "rate_limit_exceeded",
    "message": "Too many requests. Please slow down and try again after 1 second.",
    "retry_after": 1
  }
}
```

**Best practice:** Use the `Retry-After` response header to determine how long to wait before retrying. Implement exponential backoff with jitter for retry logic. Do not hard-code fixed wait times.

```javascript
// Example exponential backoff with jitter (Node.js)
async function requestWithRetry(requestFn, maxRetries = 4) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (err) {
      if (err.status !== 429 || attempt === maxRetries) throw err;
      const base = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s, 8s
      const jitter = Math.random() * 500;
      await new Promise(resolve => setTimeout(resolve, base + jitter));
    }
  }
}
```

---

## Idempotency

Network failures and timeouts can leave you uncertain whether a request succeeded. To prevent double charges, include an `Idempotency-Key` header on all write requests (`POST`, `DELETE`).

### How idempotency works

1. You send a request with a unique `Idempotency-Key`.
2. Meridian processes the request and caches the result for **24 hours**.
3. If you retry with the same key, Meridian returns the cached response — no duplicate action is taken.
4. If the original request is still processing when you retry, you receive a `409 Conflict` response until the original completes.

### Generating idempotency keys

Use a value that is unique to the specific operation you are trying to perform — not just a random UUID. This ensures that retrying the same business action is safe.

```python
import uuid

# Good: tied to the specific order and attempt
idempotency_key = f"order_{order_id}_payment_attempt_{attempt_number}"

# Also acceptable: generate a UUID per request and store it before sending
idempotency_key = str(uuid.uuid4())
```

### Key requirements

- Maximum length: 255 characters
- Must be unique per API key (test and live keys have separate namespaces)
- Keys are case-sensitive

### Conflict response

If you send a request with the same idempotency key but a different request body, the API returns:

```json
{
  "error": {
    "type": "idempotency_error",
    "code": "idempotency_key_reuse",
    "message": "An idempotency key can only be used with the same request body. Use a new key for a different request."
  }
}
```

---

## Webhooks

Webhooks allow Meridian to notify your server when events occur asynchronously — for example, when a payment succeeds or a refund is processed.

### Registering a webhook endpoint

1. Go to **Settings → Webhooks** in the Meridian Dashboard.
2. Enter your endpoint URL (must be publicly accessible HTTPS).
3. Select the events you want to receive.
4. Copy your **webhook signing secret** (`whsec_...`). You will need this to verify incoming requests.

### Webhook event structure

Every webhook event is a JSON object with the following top-level fields:

```json
{
  "id": "evt_3PkR2GC8U4eTbh0Zq1M",
  "object": "event",
  "type": "payment.succeeded",
  "created": 1711843205,
  "livemode": false,
  "data": {
    "object": {
      "id": "pay_3NzRQ2GC8U4eTbh0Yw7K",
      "object": "payment",
      "amount": 4999,
      "currency": "usd",
      "status": "succeeded"
    }
  }
}
```

### Common event types

| Event | Triggered when |
|---|---|
| `payment.succeeded` | A payment is captured and funds are secured |
| `payment.failed` | A payment attempt fails |
| `payment.pending` | A payment is created but not yet confirmed |
| `refund.created` | A refund is issued |
| `refund.failed` | A refund cannot be processed |
| `customer.created` | A new Customer object is created |
| `payment_method.attached` | A Payment Method is attached to a Customer |

### Verifying webhook signatures

Meridian signs every webhook payload using HMAC-SHA256. **Always verify the signature** before processing the event — do not trust unverified webhooks.

**How it works:**

1. Meridian sends a `Meridian-Signature` header with each webhook: `t=<timestamp>,v1=<signature>`
2. You construct the signed payload: concatenate the timestamp, a `.` character, and the raw request body
3. Compute the HMAC-SHA256 of that string using your webhook signing secret
4. Compare the result to the `v1` value in the header

**Signature verification — Node.js**

```javascript
const crypto = require('crypto');

function verifyWebhookSignature(payload, header, secret) {
  const sigHeader = header; // e.g., "t=1711843205,v1=abc123..."
  const parts = Object.fromEntries(
    sigHeader.split(',').map(part => part.split('='))
  );

  const timestamp = parts['t'];
  const receivedSig = parts['v1'];

  // Reject events older than 5 minutes to prevent replay attacks
  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - parseInt(timestamp)) > 300) {
    throw new Error('Webhook timestamp is too old — possible replay attack.');
  }

  const signedPayload = `${timestamp}.${payload}`;
  const expectedSig = crypto
    .createHmac('sha256', secret)
    .update(signedPayload, 'utf8')
    .digest('hex');

  if (!crypto.timingSafeEqual(
    Buffer.from(expectedSig, 'hex'),
    Buffer.from(receivedSig, 'hex')
  )) {
    throw new Error('Invalid webhook signature.');
  }

  return true;
}

// Express.js example
app.post('/webhooks/meridian', express.raw({ type: 'application/json' }), (req, res) => {
  const sig = req.headers['meridian-signature'];
  const secret = process.env.MERIDIAN_WEBHOOK_SECRET;

  try {
    verifyWebhookSignature(req.body.toString(), sig, secret);
  } catch (err) {
    return res.status(400).send(`Webhook signature verification failed: ${err.message}`);
  }

  const event = JSON.parse(req.body);

  switch (event.type) {
    case 'payment.succeeded':
      handlePaymentSucceeded(event.data.object);
      break;
    case 'refund.created':
      handleRefundCreated(event.data.object);
      break;
    default:
      console.log(`Unhandled event type: ${event.type}`);
  }

  res.json({ received: true });
});
```

**Signature verification — Python**

```python
import hmac
import hashlib
import time

def verify_webhook_signature(payload: bytes, header: str, secret: str) -> bool:
    parts = dict(item.split("=", 1) for item in header.split(","))
    timestamp = parts.get("t")
    received_sig = parts.get("v1")

    if not timestamp or not received_sig:
        raise ValueError("Invalid Meridian-Signature header format.")

    # Reject stale events (older than 5 minutes)
    if abs(time.time() - int(timestamp)) > 300:
        raise ValueError("Webhook timestamp too old — possible replay attack.")

    signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_sig, received_sig)
```

### Retry behavior

If your endpoint returns any status other than `2xx`, Meridian will retry delivery using exponential backoff:

| Attempt | Delay |
|---|---|
| 1 | Immediately |
| 2 | 5 minutes |
| 3 | 30 minutes |
| 4 | 2 hours |
| 5 | 5 hours |

After 5 failed attempts, the event is marked as failed and no further retries are made. You can manually retry failed events from the Dashboard.

**Recommendation:** Always return `200 OK` immediately upon receiving a valid, verified webhook, then process the event asynchronously. Do not block the HTTP response on downstream operations.

---

## Error Handling

The API uses conventional HTTP response codes to indicate success or failure.

| Code | Meaning |
|---|---|
| `200` | Success |
| `400` | Bad Request — invalid parameters |
| `401` | Unauthorized — invalid or missing API key |
| `402` | Payment Required — card was declined |
| `404` | Not Found — resource does not exist |
| `409` | Conflict — idempotency key reuse with different body |
| `422` | Unprocessable Entity — request was understood but semantically invalid |
| `429` | Too Many Requests — rate limit exceeded |
| `500` | Internal Server Error — something went wrong on Meridian's end |

### Error object structure

All error responses return a JSON body with an `error` object:

```json
{
  "error": {
    "type": "card_error",
    "code": "card_declined",
    "decline_code": "insufficient_funds",
    "message": "Your card has insufficient funds.",
    "param": null,
    "payment": "pay_3NzRQ2GC8U4eTbh0Yw7K"
  }
}
```

### Error types

| Type | Description |
|---|---|
| `api_error` | An unexpected error occurred on the Meridian server. Retry with exponential backoff. |
| `authentication_error` | Your API key is invalid, expired, or lacks permission for this operation. |
| `card_error` | The card was declined. Check `decline_code` for specifics. |
| `idempotency_error` | The idempotency key was reused with a different request body. |
| `invalid_request_error` | A parameter is missing, invalid, or in the wrong format. |
| `rate_limit_error` | You are sending requests too quickly. |

### Common decline codes

| `decline_code` | Cause | Recommended action |
|---|---|---|
| `insufficient_funds` | Card has insufficient balance | Ask customer to use a different card or contact their bank |
| `card_declined` | Generic decline; no further details from issuer | Ask customer to contact their bank |
| `expired_card` | Card expiry date has passed | Prompt customer to update their payment method |
| `incorrect_cvc` | CVC code does not match | Prompt customer to re-enter CVC |
| `do_not_honor` | Issuer blocked the transaction | Ask customer to contact their bank |
| `fraudulent` | Meridian risk engine blocked the transaction | Contact Meridian support if unexpected |
| `lost_card` / `stolen_card` | Card reported lost or stolen | Do not retry. Do not reveal the reason to the cardholder. |

---

## Test Cards

Use these card numbers in test mode to simulate specific outcomes. Use any future expiry date, any 3-digit CVC, and any postal code.

### Successful payments

| Card number | Brand | Description |
|---|---|---|
| `4242 4242 4242 4242` | Visa | Always succeeds |
| `5555 5555 5555 4444` | Mastercard | Always succeeds |
| `3782 822463 10005` | American Express | Always succeeds (4-digit CVC) |
| `6011 1111 1111 1117` | Discover | Always succeeds |
| `4000 0025 0000 3155` | Visa | Requires 3D Secure authentication |
| `4000 0000 0000 3063` | Visa | 3D Secure supported but not required |

### Declined payments

| Card number | Decline code | Description |
|---|---|---|
| `4000 0000 0000 9995` | `insufficient_funds` | Always declines with insufficient funds |
| `4000 0000 0000 0002` | `card_declined` | Always declines (generic) |
| `4000 0000 0000 0069` | `expired_card` | Always declines as expired |
| `4000 0000 0000 0127` | `incorrect_cvc` | Always declines due to incorrect CVC |
| `4000 0000 0000 0119` | `processing_error` | Simulates a processing error |
| `4100 0000 0000 0019` | `fraudulent` | Triggers fraud block |

### Special behavior

| Card number | Description |
|---|---|
| `4000 0000 0000 0077` | Returns `payment.succeeded` immediately, then triggers `payment.refunded` webhook 1 minute later |
| `4000 0000 0000 0044` | Simulates a network timeout — always returns a 500 error |
| `4000 0000 0000 1091` | Returns `pending` status; transitions to `succeeded` after 30 seconds |

---

## Best Practices

### Security

**Never log full card numbers or CVCs.** Meridian's API ensures these values are not returned in responses, but ensure your application does not accidentally log raw request bodies containing cardholder data.

**Restrict API key permissions.** In the Dashboard, create restricted keys with only the scopes your application requires. Avoid using your full secret key in application code.

**Rotate keys promptly if compromised.** In the Dashboard, go to **Settings → API Keys → Revoke** to immediately invalidate a key. New keys take effect instantly.

**Use environment variables for keys.** Never hardcode API keys in source code or commit them to version control.

```bash
# .env (never commit this file)
MERIDIAN_SECRET_KEY=sk_live_51NzRQ2GC8U...
MERIDIAN_WEBHOOK_SECRET=whsec_4mBn8Xz...
```

### Reliability

**Always use idempotency keys** on payment creation requests. This is the single most important step to prevent duplicate charges in production.

**Handle `payment.succeeded` webhooks as the source of truth** for payment confirmation — do not rely solely on the synchronous API response, which may reflect an intermediate state.

**Subscribe to `payment.failed` and `payment.pending` webhooks** to handle edge cases and provide accurate status updates to your users.

**Implement graceful degradation.** If the Meridian API is unavailable, queue the payment request and retry when the service recovers rather than failing the transaction immediately.

### Performance

**Cache Customer and Payment Method IDs** rather than recreating them on each transaction. Meridian charges are cheaper and faster when using saved payment methods.

**Use the `expand` parameter** to fetch nested objects in a single API call rather than making multiple requests:

```bash
curl "https://api.meridianpay.io/v2/payments/pay_3NzRQ2GC8U4eTbh0Yw7K?expand[]=customer&expand[]=payment_method" \
  -H "Authorization: Bearer sk_test_EXAMPLE_KEY_DO_NOT_USE"
```

**Paginate list endpoints** using `limit` and `starting_after` parameters. Default page size is 10; maximum is 100. Never assume all results fit in a single response.

---

## Changelog

### v2.4 — March 2026

- **New:** `capture_method: "manual"` is now supported on all payment types (previously card-only).
- **New:** `expand[]` parameter now supports `payment.customer`, `payment.payment_method`, and `refund.payment`.
- **Improved:** Webhook retry delays updated to use true exponential backoff (previously fixed 1-hour intervals).
- **Fixed:** `payment.pending` webhooks were occasionally not firing for bank transfer payments. This has been resolved.
- **Deprecated:** The `source` parameter on Payment creation is deprecated in favor of `payment_method`. Support will be removed in v3.0 (Q3 2026).

### v2.3 — November 2025

- **New:** Webhook event `payment_method.expiring_soon` added. Fires 30 days before a saved card's expiry date.
- **New:** `metadata` field added to Refund objects.
- **Improved:** Idempotency key cache window extended from 1 hour to 24 hours.
- **Fixed:** Rare race condition where concurrent requests with the same idempotency key could result in duplicate charges. This has been fully resolved.

### v2.2 — July 2025

- **New:** Customer Billing Portal API — programmatically generate links to the hosted portal where customers can manage their payment methods.
- **New:** `decline_code` field added to `card_error` objects for more specific decline handling.
- **Improved:** `POST /v2/customers` now accepts a `default_payment_method` parameter to set a default at creation time.

### v2.1 — March 2025

- **New:** Payment Method attach endpoint (`POST /v2/payment_methods/{id}/attach`).
- **New:** Test card `4000 0000 0000 1091` added to simulate delayed payment confirmation.
- **Breaking change:** The `card` field on Payment objects was renamed to `payment_method_details`. Update any code that references `payment.card` before upgrading.
- **Deprecated:** Endpoint `GET /v2/charges` is deprecated in favor of `GET /v2/payments`. Will be removed in v3.0.

### v2.0 — October 2024

- **Breaking:** Full API rewrite. Resources renamed from `charges`/`sources` to `payments`/`payment_methods`.
- **New:** Customer and Payment Method objects introduced.
- **New:** Idempotency key support added to all write endpoints.
- **New:** Webhook signature verification added (`Meridian-Signature` header).

---

*For integration support, visit the [Meridian Developer Portal](https://developers.meridianpay.io) or contact [support@meridianpay.io](mailto:support@meridianpay.io).*
