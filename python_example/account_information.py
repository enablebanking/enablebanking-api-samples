import os
import json
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs
import uuid

import requests

from utils import get_jwt


file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.json')
with open(file_path, 'r') as f:
    config = json.load(f)
KEY_PATH = config["keyPath"]
APPLICATION_ID = config["applicationId"]


if __name__ == "__main__":
    JWT = get_jwt(APPLICATION_ID, KEY_PATH)
    BASE_URL = "https://api.tilisy.com"
    REDIRECT_URL = config["redirectUrl"]
    # we are going to use that bank for reference
    BANK_NAME = "Nordea"
    BANK_COUNTRY = "FI"
    base_headers = {"Authorization": f"Bearer {JWT}"}
    application_response = requests.get(f"{BASE_URL}/application", headers=base_headers)
    print(f"Application data: {application_response.json()}")

    aspsps_response = requests.get(f"{BASE_URL}/aspsps", headers=base_headers)
    # If you want, you can override BANK_NAME and BANK_COUNTRY with any bank from this list
    print(f"ASPSPS data: {aspsps_response.json()}")

    start_authorization_body = {
        "access": {
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
        },
        "aspsp": {"name": BANK_NAME, "country": BANK_COUNTRY},
        "state": str(uuid.uuid4()),
        "redirect_url": REDIRECT_URL,
        "psu_type": "personal",
    }
    psu_headers = base_headers.copy()
    psu_headers["psu-ip-address"] = "10.10.10.10"
    psu_headers["psu-user-agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:80.0) Gecko/20100101 Firefox/80.0"
    start_authorization_response = requests.post(
        f"{BASE_URL}/auth", json=start_authorization_body, headers=psu_headers
    )
    start_authorization_data = start_authorization_response.json()
    print(f"Start authorization data: {start_authorization_data}")

    redirected_url = input(
        f"Please go to {start_authorization_data['url']}, authorize consent and"
        "paste here the url you have been redirected to: "
    )
    code = parse_qs(urlparse(redirected_url).query)["code"][0]
    create_session_body = {"code": code}

    create_session_response = requests.post(
        f"{BASE_URL}/sessions", json=create_session_body, headers=psu_headers
    )
    create_session_data = create_session_response.json()
    print(f"Create session data: {create_session_data}")

    session_id = create_session_data["session_id"]

    session_response = requests.get(
        f"{BASE_URL}/sessions/{session_id}", headers=base_headers
    )
    session_data = session_response.json()
    print(f"Session data: {session_data}")

    account_id = session_data["accounts"][0]
    account_balances_response = requests.get(
        f"{BASE_URL}/accounts/{account_id}/balances", headers=psu_headers
    )
    print(f"Account balances data: {account_balances_response.json()}")

    account_transactions_response = requests.get(
        f"{BASE_URL}/accounts/{account_id}/transactions", headers=psu_headers
    )
    print(f"Account transactions data: {account_transactions_response.json()}")
