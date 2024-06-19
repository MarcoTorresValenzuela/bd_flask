import requests
import time
import hmac
import hashlib
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import binascii

def calc_sign(access_id, access_secret, method, path, params=None, body=None):
    str_to_sign = method + "\n"
    content_to_sha256 = "" if body is None or len(body.keys()) == 0 else json.dumps(body)
    str_to_sign += hashlib.sha256(content_to_sha256.encode("utf8")).hexdigest().lower() + "\n"
    str_to_sign += "\n"
    str_to_sign += path
    if params is not None and len(params.keys()) > 0:
        str_to_sign += "?"
        query_builder = "&".join([f"{key}={params[key]}" for key in sorted(params)])
        str_to_sign += query_builder
    t = str(int(time.time() * 1000))
    message = access_id + t + str_to_sign
    sign = hmac.new(access_secret.encode("utf8"), msg=message.encode("utf8"), digestmod=hashlib.sha256).hexdigest().upper()
    return sign, t

def calc_sign_t(access_id, access_secret, access_token, method, path, params=None, body=None):
    str_to_sign = method + "\n"
    content_to_sha256 = "" if body is None or len(body.keys()) == 0 else json.dumps(body)
    str_to_sign += hashlib.sha256(content_to_sha256.encode("utf8")).hexdigest().lower() + "\n"
    str_to_sign += "\n"
    str_to_sign += path
    if params is not None and len(params.keys()) > 0:
        str_to_sign += "?"
        query_builder = "&".join([f"{key}={params[key]}" for key in sorted(params)])
        str_to_sign += query_builder
    t = str(int(time.time() * 1000))
    message = access_id + access_token + t + str_to_sign
    sign = hmac.new(access_secret.encode("utf8"), msg=message.encode("utf8"), digestmod=hashlib.sha256).hexdigest().upper()
    return sign, t

def get_access_token(client_id, secret):
    sign_token, t_token = calc_sign(client_id, secret, "GET", "/v1.0/token", {"grant_type": "1"})
    request_url_token = f"https://openapi.tuyaus.com/v1.0/token?grant_type=1"
    headers_token = {
        "client_id": client_id,
        "sign": sign_token,
        "t": t_token,
        "sign_method": "HMAC-SHA256"
    }
    response_token = requests.get(request_url_token, headers=headers_token)
    if response_token.status_code == 200:
        data_token = response_token.json()
        return data_token.get("result", {}).get("access_token"), data_token.get("result", {}).get("expire_time")
    return None, None

def get_device_info(client_id, secret, access_token, device_id):
    sign_info, t_info = calc_sign_t(client_id, secret, access_token, "GET", f"/v1.0/devices/{device_id}")
    request_url_info = f"https://openapi.tuyaus.com/v1.0/devices/{device_id}"
    headers_info = {
        "client_id": client_id,
        "sign": sign_info,
        "t": t_info,
        "sign_method": "HMAC-SHA256",
        "access_token": access_token,
    }
    response_info = requests.get(request_url_info, headers=headers_info)
    if response_info.status_code == 200:
        return response_info.json().get("result", {})
    return {}

def get_temp_key(client_id, secret, access_token, device_id):
    sign_temp_key, t_tk = calc_sign_t(client_id, secret, access_token, "POST", f"/v1.0/devices/{device_id}/door-lock/password-ticket")
    request_url_temp_key = f"https://openapi.tuyaus.com/v1.0/devices/{device_id}/door-lock/password-ticket"
    headers_temp_key = {
        "client_id": client_id,
        "sign": sign_temp_key,
        "t": t_tk,
        "sign_method": "HMAC-SHA256",
        "access_token": access_token
    }
    response_temp_key = requests.post(request_url_temp_key, headers=headers_temp_key)
    if response_temp_key.status_code == 200:
        return response_temp_key.json().get("result", {})
    return {}

def decrypt_ticket_key(ticket_key_hex, access_secret):
    ticket_key = bytes.fromhex(ticket_key_hex)
    cipher = AES.new(access_secret.encode(), AES.MODE_ECB)
    decrypted_ticket_key = cipher.decrypt(ticket_key)
    decrypted_ticket_key = unpad(decrypted_ticket_key, AES.block_size)
    return binascii.hexlify(decrypted_ticket_key).decode()

def encrypt_password(password, ticket_key):
    cipher = AES.new(bytes.fromhex(ticket_key), AES.MODE_ECB)
    padded_password = pad(password.encode(), AES.block_size)
    encrypted_password = cipher.encrypt(padded_password)
    return encrypted_password.hex()
