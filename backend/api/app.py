"""Main file used to config the app and create the endpoint.
Used on the same file since there is only one endpoint.
"""
import os

import flask
from flask_cors import CORS
from flask_redis import FlaskRedis

from api import config

# possible configs
configs = {
    "dev": config.DevConfig,
    "test": config.TestConfig,
}

app = flask.Flask(__name__)
env = os.getenv("ENV", "test")
app.config.from_object(configs[env])

CORS(app, resources={r"/api/*": {"origins": "http://localhost"}})
redis_client = FlaskRedis(app)

app.logger.debug(f"App initialized using env: {env}")

# import here the modules to avoid circular dependencies
from api import paypal


@app.route("/api/paypal/order/create", methods=["POST"])
def order():
    """Endpoint to order a payment from the Paypal API."""
    data = flask.request.json
    data_total = data.get("total", -1)
    if data_total:
        total = float(data_total)
    else:
        total = -1

    if total <= 0:
        return {"msg": "Total should be a positive number"}, 500
    response = paypal.create_order(total)
    app.logger.debug(response)
    return response


@app.route("/api/paypal/order/capture", methods=["POST"])
def capture():
    """Endpoint to capture a payment from the Paypal API."""
    data = flask.request.json
    response = paypal.capture_order(data["orderID"])
    app.logger.debug(response)
    return response
