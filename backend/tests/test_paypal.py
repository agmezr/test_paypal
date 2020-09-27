import json
import requests
import unittest
from unittest import mock

from api.app import app
from api.app import redis_client
from api import paypal


TOKEN_RESPONSE = {'scope': 'https://uri.paypal.com/services/invoicing',
                  'access_token': 'some-access-token',
                  'token_type': 'Bearer',
                  'app_id': 'APP-0000123456',
                  'expires_in': 32400,
                  'nonce': '2020-09-27T17:47133'
                  }

MOCK_PAYMENT_RESPONSE = {
  "id": "PAY-1B56960729604235TKQQIYVY",
  "create_time": "2017-09-22T20:53:43Z",
  "update_time": "2017-09-22T20:53:44Z",
  "state": "CREATED",
  "intent": "sale",
  "payer": {
    "payment_method": "paypal",
  },
}

MOCK_EXECUTE_RESPONSE = {
  "id": "PAY-9N9834337A9191208KOZOQWI",
  "create_time": "2017-07-01T16:56:57Z",
  "update_time": "2017-07-01T17:05:41Z",
  "state": "APPROVED",
  "intent": "order",
  "payer": {
    "payment_method": "paypal",
    "payer_info": {
      "email": "qa152-biz@example.com",
      "first_name": "Thomas",
      "last_name": "Miller",
      "payer_id": "PUP87RBJV8HPU",
      "shipping_address": {
        "line1": "4th Floor, One Lagoon Drive",
        "line2": "Unit #34",
        "city": "Redwood City",
        "state": "CA",
        "postal_code": "94065",
        "country_code": "US",
        "phone": "011862212345678",
        "recipient_name": "Thomas Miller"
      }
    }
  },
  "transactions": [
    {
      "amount": {
        "total": "41.15",
        "currency": "USD",
        "details": {
          "subtotal": "30.00",
          "tax": "0.15",
          "shipping": "11.00"
        }
      },
    }
  ],
}


class MockRequest:
    """Mock used to mock API for the sources."""

    def __init__(self, json_response, status_code):
        self.json_response = json_response
        self.status_code = status_code

    def json(self):
        return self.json_response


class PaypalTest(unittest.TestCase):

    def test_generate_token(self):
        """Tests function to retrieve a token."""
        mock_request = MockRequest(TOKEN_RESPONSE, 200)
        with mock.patch.object(requests, 'post', return_value=mock_request) as mock_response:
            with mock.patch.object(redis_client, 'set') as mock_redis:
                paypal._get_token()
                mock_response.assert_called_once()
                mock_redis.assert_called()

    @mock.patch.object(redis_client, 'get', return_value=b'1900-01-01 00:00:00.0')
    @mock.patch.object(redis_client, 'get', return_value='Some token')
    @mock.patch.object(paypal, '_get_token')
    def test_validate_token(self, mock_token, mock_redis, mock_expires):
        """Tests method for validate token."""
        fn = mock.Mock()
        paypal.validate_token(fn)()
        mock_token.assert_called()
        mock_expires.assert_called()

    @mock.patch.object(paypal, '_get_token')
    @mock.patch.object(requests, 'post')
    def test_make_payment(self, mock_post, mock_token):
        """Tests make payment for Paypal API."""
        mock_request = MockRequest(MOCK_PAYMENT_RESPONSE, 200)
        mock_post.return_value = mock_request
        with mock.patch.object(redis_client, 'get') as mock_redis:
            mock_redis.side_effect = ['some token', b'1900-01-01 00:00:00.0', b'token']
            response = paypal.make_payment(10)
            mock_redis.assert_called()
            mock_token.assert_called()
            self.assertEqual(response, MOCK_PAYMENT_RESPONSE)

    @mock.patch.object(paypal, '_get_token')
    @mock.patch.object(requests, 'post')
    def test_execute_payment(self, mock_post, mock_token):
        """Tests execute payment for Paypal API."""
        mock_request = MockRequest(MOCK_PAYMENT_RESPONSE, 200)
        mock_post.return_value = mock_request
        with mock.patch.object(redis_client, 'get') as mock_redis:
            mock_redis.side_effect = ['some token', b'1900-01-01 00:00:00.0', b'token']
            response = paypal.execute_payment('id', 'id2')
            mock_redis.assert_called()
            mock_token.assert_called()
            self.assertEqual(response, MOCK_PAYMENT_RESPONSE)

    @mock.patch.object(paypal, 'make_payment')
    def test_make_payment_endpoint(self, mock_payment):
        """Tests endpoint to make payment for Paypal API."""
        mock_payment.return_value = MOCK_PAYMENT_RESPONSE
        with app.test_client() as client:
            endpoint = "api/payment"
            rv = client.post(endpoint, data={"total": 12})
            data = json.loads(rv.data)
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(data, MOCK_PAYMENT_RESPONSE)

    @mock.patch.object(paypal, 'make_payment')
    def test_execute_payment_invalid_amount(self, mock_payment):
        """Tests endpoint payment for Paypal API with an invalid amount."""
        mock_payment.return_value = MOCK_PAYMENT_RESPONSE
        with app.test_client() as client:
            endpoint = "api/payment"
            rv = client.post(endpoint, data={"total": -1})
            data = json.loads(rv.data)
            self.assertEqual(rv.status_code, 500)

    @mock.patch.object(paypal, 'execute_payment')
    def test_execute_payment_endpoint(self, mock_payment):
        """Tests endpoint to execute payment for Paypal API."""
        mock_payment.return_value = MOCK_EXECUTE_RESPONSE
        with app.test_client() as client:
            endpoint = "api/execute"
            rv = client.post(endpoint, data={'paymentID': 123, 'payerID': 123})
            data = json.loads(rv.data)
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(data, MOCK_EXECUTE_RESPONSE)


if __name__ == '__main__':
    unittest.main()
