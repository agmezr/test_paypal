# Test Paypal API

A test using the API of Paypal using Flask as a middleware
for the responses.

`Client Id` and `Secret id` are stored in an `.env` file

Paypal token is stored in Redis and will be generated only
when the token is `None` or `expired`

```bash
SECRET_KEY="Some-secret-key"
PAYPAL_CLIENT_ID="Client id"
PAYPAL_SECRET_ID="Secret id"
REDIS_URL = "redis://:password@localhost:6379/0"
```
