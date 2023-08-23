import json
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pprint import pprint
from urllib.parse import urlparse, parse_qs

import requests
import jwt as pyjwt


API_ORIGIN = "https://api.enablebanking.com"
ASPSP_NAME = "S-Pankki"
ASPSP_COUNTRY = "FI"

def main():
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
    with open(file_path, "r") as f:
        config = json.load(f)
    iat = int(datetime.now().timestamp())
    jwt_body = {
        "iss": "enablebanking.com",
        "aud": "api.enablebanking.com",
        "iat": iat,
        "exp": iat + 3600,
    }
    jwt = pyjwt.encode(
        jwt_body,
        open(os.path.join('..', config["keyPath"]), "rb").read(),
        algorithm="RS256",
        headers={"kid": config["applicationId"]},
    )
    print(jwt)

    base_headers = {"Authorization": f"Bearer {jwt}"}

    # Requesting application details
    r = requests.get(f"{API_ORIGIN}/application", headers=base_headers)
    if r.status_code != 200:
        print(f"Error response {r.status_code}:", r.text)
        return
    app = r.json()
    print("Application details:")
    pprint(app)

    # Requesting available ASPSPs
    r = requests.get(f"{API_ORIGIN}/aspsps", headers=base_headers)
    if r.status_code != 200:
        print(f"Error response {r.status_code}:", r.text)
        return
    print("Available ASPSPs:")
    pprint(r.json()["aspsps"])

    # Initiating payment
    body = {
        "payment_type": "SEPA",
        "payment_request": {
            "credit_transfer_transaction": [
                {
                    "beneficiary": {
                        "creditor_account": {
                            "scheme_name": "IBAN",
                            "identification": "FI7473834510057469",
                        },
                        "creditor": {
                            "name": "Test",
                        },
                    },
                    "instructed_amount": {"amount": "2.00", "currency": "EUR"},
                    "reference_number": "123",
                }
            ],
        },
        "aspsp": {"name": ASPSP_NAME, "country": ASPSP_COUNTRY},
        "state": str(uuid.uuid4()),
        "redirect_url": config["redirectUrl"],
        "psu_type": "personal",
    }
    r = requests.post(f"{API_ORIGIN}/payments", json=body, headers=base_headers)
    if r.status_code != 200:
        print(f"Error response {r.status_code}:", r.text)
        return

    payment = r.json()
    print("Use following credentials to authenticate: customera / 12345678")
    print("To authenticate open URL:")
    print(payment["url"])

    # Getting payment status
    # This request can be called multiple times to check the status of the payment
    payment_id = payment["payment_id"]
    r = requests.get(f"{API_ORIGIN}/payments/{payment_id}", headers=base_headers)
    if r.status_code != 200:
        print(f"Error response {r.status_code}:", r.text)
        return
    print("Payment status:")
    pprint(r.json())



if __name__ == "__main__":
    main()
