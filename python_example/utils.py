import os
import base64
import datetime
import json
from typing import Dict, Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding


file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.json')
with open(file_path, 'r') as f:
    config = json.load(f)
KEY_PATH = config["keyPath"]
APPLICATION_ID = config["applicationId"]


def _prepare_private_key(key_path: str):
    backend = default_backend()
    return backend.load_pem_private_key(open(key_path, "rb").read(), None)


def _encode_data(data: Dict[Any, Any]) -> str:
    return (
        base64.urlsafe_b64encode(json.dumps(data).encode())
        .decode("utf8")
        .replace("=", "")
    )


def get_jwt_header() -> str:
    header_data = {"typ": "JWT", "alg": "RS256", "kid": APPLICATION_ID}
    return _encode_data(header_data)


def get_jwt_body(exp) -> str:
    timestamp = int(datetime.datetime.now().timestamp())
    body_data = {
        "iss": "enablebanking.com",
        "aud": "api.tilisy.com",
        "iat": timestamp,
        "exp": timestamp + exp,
    }
    return _encode_data(body_data)


def signWithKey(data: str) -> str:
    encoded_data = data.encode()
    key = _prepare_private_key(KEY_PATH)
    signature = key.sign(encoded_data, padding.PKCS1v15(), hashes.SHA256())
    return base64.urlsafe_b64encode(signature).decode("utf8").replace("=", "")


def get_jwt(exp: int = 3600):
    jwt_header = get_jwt_header()
    jwt_body = get_jwt_body(exp=exp)
    jwt_signature = signWithKey(f"{jwt_header}.{jwt_body}")
    return f"{jwt_header}.{jwt_body}.{jwt_signature}"
