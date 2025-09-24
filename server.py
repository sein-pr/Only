import logging
import os

from flask import Flask, request, Response
from paypalserversdk.http.auth.o_auth_2 import ClientCredentialsAuthCredentials
from paypalserversdk.logging.configuration.api_logging_configuration import (
    LoggingConfiguration,
    RequestLoggingConfiguration,
    ResponseLoggingConfiguration,
)
from paypalserversdk.paypal_serversdk_client import PaypalServersdkClient
from paypalserversdk.controllers.orders_controller import OrdersController
from paypalserversdk.models.amount_with_breakdown import AmountWithBreakdown
from paypalserversdk.models.checkout_payment_intent import CheckoutPaymentIntent
from paypalserversdk.models.order_request import OrderRequest
from paypalserversdk.models.purchase_unit_request import PurchaseUnitRequest
from paypalserversdk.api_helper import ApiHelper

app = Flask(__name__)

# Fix: Use environment variables properly or hardcode temporarily for testing
PAYPAL_CLIENT_ID = "AQZyS9RlDUHmcfGfNA8XZYIP1jtcMhr5E0GmNL3PxCGAHwVfO-5XAwLXABEZpLTHNn_7RYJHLK9637v-"
PAYPAL_CLIENT_SECRET = "EHSwVlk5tFSqJ1c9wS8jGdsvmisEREsA35P5L50jilgxUXT8WTzuHsA1lnxcRQu2DbD6t2upgrj25PhD"

paypal_client: PaypalServersdkClient = PaypalServersdkClient(
    client_credentials_auth_credentials=ClientCredentialsAuthCredentials(
        o_auth_client_id=PAYPAL_CLIENT_ID,
        o_auth_client_secret=PAYPAL_CLIENT_SECRET,
    ),
    logging_configuration=LoggingConfiguration(
        log_level=logging.INFO,
        mask_sensitive_headers=False,
        request_logging_config=RequestLoggingConfiguration(
            log_headers=True, log_body=True
        ),
        response_logging_config=ResponseLoggingConfiguration(
            log_headers=True, log_body=True
        ),
    ),
)

orders_controller: OrdersController = paypal_client.orders

@app.route("/", methods=["GET"])
def index():
    return {"message": "Server is running"}

@app.route("/api/orders", methods=["POST"])
def create_order():
    try:
        request_body = request.get_json()
        cart = request_body.get("cart", [])
        
        # Calculate total amount
        total_amount = sum(float(item['price']) * int(item['quantity']) for item in cart)
        
        order = orders_controller.create_order(
            {
                "body": OrderRequest(
                    intent=CheckoutPaymentIntent.CAPTURE,
                    purchase_units=[
                        PurchaseUnitRequest(
                            amount=AmountWithBreakdown(
                                currency_code="USD", 
                                value=f"{total_amount:.2f}"
                            )
                        )
                    ],
                ),
                "prefer": "return=representation",
            }
        )
        return Response(
            ApiHelper.json_serialize(order.body), 
            status=200, 
            mimetype="application/json"
        )
    except Exception as e:
        return Response(
            f'{{"error": "{str(e)}"}}',
            status=500,
            mimetype="application/json"
        )

@app.route("/api/orders/<order_id>/capture", methods=["POST"])
def capture_order(order_id):
    try:
        order = orders_controller.capture_order(
            {"id": order_id, "prefer": "return=representation"}
        )
        return Response(
            ApiHelper.json_serialize(order.body), 
            status=200, 
            mimetype="application/json"
        )
    except Exception as e:
        return Response(
            f'{{"error": "{str(e)}"}}',
            status=500,
            mimetype="application/json"
        )

if __name__ == "__main__":
    app.run(debug=True, port=5001)  # Run on different port than main app
