import json
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pprint import pprint
from urllib.parse import urlparse, parse_qs

import requests
import jwt as pyjwt


API_ORIGIN = "https://api.tilisy.com"
ASPSP_NAME = "Nordea"
ASPSP_COUNTRY = "FI"


def main():
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
    with open(file_path, "r") as f:
        config = json.load(f)
    iat = int(datetime.now().timestamp())
    jwt_body = {
        "iss": "enablebanking.com",
        "aud": "api.tilisy.com",
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
    if r.status_code == 200:
        app = r.json()
        print("Application details:")
        pprint(app)
    else:
        print(f"Error response {r.status_code}:", r.text)
        return

    # Requesting available ASPSPs
    r = requests.get(f"{API_ORIGIN}/aspsps", headers=base_headers)
    if r.status_code == 200:
        print("Available ASPSPs:")
        pprint(r.json()["aspsps"])
    else:
        print(f"Error response {r.status_code}:", r.text)
        return

    # Starting authorization"
    body = {
        "access": {
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
        },
        "aspsp": {"name": ASPSP_NAME, "country": ASPSP_COUNTRY},
        "state": str(uuid.uuid4()),
        "redirect_url": app["redirect_urls"][0],
        "psu_type": "personal",
    }
    r = requests.post(f"{API_ORIGIN}/auth", json=body, headers=base_headers)
    if r.status_code == 200:
        auth_url = r.json()["url"]
        print(f"To authenticate open URL {auth_url}")
    else:
        print(f"Error response {r.status_code}:", r.text)
        return

    # Reading auth code and creating user session
    redirected_url = input("Paste here the URL you have been redirected to: ")
    auth_code = parse_qs(urlparse(redirected_url).query)["code"][0]
    r = requests.post(f"{API_ORIGIN}/sessions", json={"code": auth_code}, headers=base_headers)
    if r.status_code == 200:
        session = r.json()
        print("New user session has been created:")
        pprint(session)
    else:
        print(f"Error response {r.status_code}:", r.text)
        return

    # Fetching session details again
    session_id = session["session_id"]
    r = requests.get(f"{API_ORIGIN}/sessions/{session_id}", headers=base_headers)
    if r.status_code == 200:
        print("Stored session data:")
        pprint(r.json())
    else:
        print(f"Error response {r.status_code}:", r.text)
        return

    # Using the first available account for the following API calls
    account_uid = session["accounts"][0]["uid"]

    # Retrieving account balances
    r = requests.get(f"{API_ORIGIN}/accounts/{account_uid}/balances", headers=base_headers)
    if r.status_code == 200:
        print("Balances:")
        pprint(r.json())
    else:
        print(f"Error response {r.status_code}:", r.text)
        return

    # Retrieving account transactions (since 90 days ago)
    query = {
        "date_from": (datetime.now(timezone.utc) - timedelta(days=90)).date().isoformat(),
    }
    continuation_key = None
    while True:
        if continuation_key:
            query["continuation_key"] = continuation_key
        r = requests.get(
            f"{API_ORIGIN}/accounts/{account_uid}/transactions",
            params=query,
            headers=base_headers,
        )
        if r.status_code == 200:
            resp_data = r.json()
            print("Transactions:")
            pprint(resp_data["transactions"])
            continuation_key = resp_data.get("continuation_key")
            if not continuation_key:
                print("No continuation key. All transactions were fetched")
                break
            print(f"Going to fetch more transactions with continuation key {continuation_key}")
        else:
            print(f"Error response {r.status_code}:", r.text)
            return

    print("All done!")


if __name__ == "__main__":
    main()
