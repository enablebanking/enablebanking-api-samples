import base64
import datetime
import json
from typing import Dict, Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding



def _prepare_private_key(key_path: str):
    backend = default_backend()
    return backend.load_pem_private_key(open(key_path, "rb").read(), None)


def _encode_data(data: Dict[Any, Any]) -> str:
    return (
        base64.urlsafe_b64encode(json.dumps(data).encode())
        .decode("utf8")
        .replace("=", "")
    )


def get_jwt_header(application_id: str) -> str:
    header_data = {"typ": "JWT", "alg": "RS256", "kid": application_id}
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


def sign_with_key(data: str, key_path: str) -> str:
    encoded_data = data.encode()
    key = _prepare_private_key(key_path)
    signature = key.sign(encoded_data, padding.PKCS1v15(), hashes.SHA256())
    return base64.urlsafe_b64encode(signature).decode("utf8").replace("=", "")


def get_jwt(application_id: str, key_path: str, exp: int = 3600):
    jwt_header = get_jwt_header(application_id)
    jwt_body = get_jwt_body(exp=exp)
    jwt_signature = sign_with_key(f"{jwt_header}.{jwt_body}", key_path)
    return f"{jwt_header}.{jwt_body}.{jwt_signature}"
