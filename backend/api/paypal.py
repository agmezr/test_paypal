import datetime
import os
import requests
import functools

import dotenv

from api.app import redis_client

dotenv.load_dotenv()

PAYPAL_TOKEN = "paypal_token"
PAYPAL_TOKEN_EXPIRE = "paypal_expire"
PAYPAL_API = "https://api.sandbox.paypal.com"

# Read from .env file
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET_ID = os.getenv("PAYPAL_SECRET_ID")


def _get_token():
    """Creates a new token and store it in session"""
    endpoint = f"{PAYPAL_API}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
    response = requests.post(
        endpoint,
        headers=headers,
        auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET_ID),
        data="grant_type=client_credentials",
    )
    response_value = response.json()

    token = response_value["access_token"]
    expire_time = int(response_value["expires_in"])
    datetime_expire = str(
        datetime.datetime.now() + datetime.timedelta(seconds=expire_time)
    )

    redis_client.set(PAYPAL_TOKEN, token)
    redis_client.set(PAYPAL_TOKEN_EXPIRE, datetime_expire)


def validate_token(fn):
    """Decorator used to validate token or create a new one."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        token = redis_client.get(PAYPAL_TOKEN)
        if not token:
            _get_token()
        else:
            expire = redis_client.get(PAYPAL_TOKEN_EXPIRE).decode("utf-8")
            expire_time = datetime.datetime.strptime(expire, "%Y-%m-%d %H:%M:%S.%f")
            print("Expires", expire_time)
            if not expire or expire_time < datetime.datetime.now():
                _get_token()

        return fn(*args, **kwargs)

    return wrapper


@validate_token
def make_payment(subtotal):
    """Sends payment to Paypal API."""
    access_token = redis_client.get(PAYPAL_TOKEN).decode("utf-8")
    endpoint = f"{PAYPAL_API}/v1/payments/payment"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    shipping = 0.30
    total = subtotal + shipping

    data = {
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "transactions": [
            {
                "amount": {
                    "total": total,
                    "currency": "USD",
                    "details": {
                        "subtotal": subtotal,
                        "tax": "0.00",
                        "shipping": shipping,
                    },
                },
                "description": "The payment transaction description.",
                "custom": "ALEX_TEST_12345",
                "item_list": {
                    "items": [
                        {
                            "name": "An item",
                            "description": "Some random item.",
                            "quantity": "1",
                            "price": subtotal,
                            "tax": "0.00",
                            "sku": "1",
                            "currency": "USD",
                        },
                    ],
                },
            }
        ],
        "note_to_payer": "This is a test.",
        "redirect_urls": {
            "return_url": "http://localhost?success=true",
            "cancel_url": "http://localhost?cancel=true",
        },
    }

    response = requests.post(endpoint, headers=headers, json=data)
    return response.json()


@validate_token
def execute_payment(payment_id, payer_id):
    """Executes the payment in Paypal API."""
    endpoint = f"{PAYPAL_API}/v1/payments/payment/{payment_id}/execute"
    access_token = redis_client.get(PAYPAL_TOKEN).decode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    data = {"payer_id": payer_id}
    response = requests.post(endpoint, headers=headers, json=data)

    return response.json()
