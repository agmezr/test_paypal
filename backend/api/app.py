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


@app.route("/api/payment", methods=["POST"])
def payment():
    """Endpoint to return the current exchange_rate."""
    data = flask.request.form
    data_total = data.get("total", -1)
    if data_total:
        total = float(data_total)
    else:
        total = -1

    if total <= 0:
        return {"msg": "Total should be a positive number"}, 500
    response = paypal.make_payment(total)
    app.logger.debug(response)
    return response


@app.route("/api/execute", methods=["POST"])
def execute():
    """Endpoint to return the current exchange_rate."""
    data = flask.request.form
    response = paypal.execute_payment(data["paymentID"], data["payerID"])
    app.logger.debug(response)
    return response
