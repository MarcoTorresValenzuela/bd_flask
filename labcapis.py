import threading
import os
import datetime
import requests
from flask import Flask, request, jsonify
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from utils import calc_sign, calc_sign_t, decrypt_ticket_key, encrypt_password, get_access_token, get_device_info, get_temp_key

app = Flask(__name__)

# Diccionario para almacenar solicitudes procesadas
solicitudes_procesadas = {}

# Crear un bloqueo para evitar concurrencias
lock = threading.Lock()

# Función para verificar token
def verificar_token():
    token_esperado = os.getenv('passkey')  # Reemplaza con tu token esperado
    token_recibido = request.headers.get('Authorization')
    return token_recibido == token_esperado

# Función para verificar duplicación por IP y request_id
def es_solicitud_duplicada(ip, request_id, tipo_peticion):
    clave = (ip, request_id, tipo_peticion)
    return clave in solicitudes_procesadas

# Función para registrar la solicitud como procesada
def registrar_solicitud_procesada(ip, request_id, tipo_peticion):
    clave = (ip, request_id, tipo_peticion)
    solicitudes_procesadas[clave] = datetime.datetime.now()

@app.route('/generate-temp-password', methods=['POST'])
def generate_temp_password():
    if not verificar_token():
        return jsonify({'error': 'Unauthorized'}), 401

    ip_cliente = request.remote_addr  # Obtener la IP del cliente
    data = request.json
    request_id = data.get("request_id")
    name = data.get("name")
    password = data.get("password")
    cabaña = data.get("cabaña")
    personas = int(data.get("personas"))
    effective_date = datetime.datetime.strptime(data.get("effective_time"), "%d-%m-%Y")
    invalid_date = datetime.datetime.strptime(data.get("invalid_time"), "%d-%m-%Y")

    if not request_id:
        return jsonify({'error': 'request_id is required'}), 400

    with lock:  # Bloquea la ejecución para evitar concurrencias
        # Verificar si la solicitud ya fue procesada (basado en IP y request_id)
        if es_solicitud_duplicada(ip_cliente, request_id, 'generate-temp-password'):
            return jsonify({'error': 'Duplicate request'}), 400

        # Registrar la solicitud como procesada
        registrar_solicitud_procesada(ip_cliente, request_id, 'generate-temp-password')

    effective_time = effective_date.replace(hour=19, minute=0)  # Hora efectiva
    invalid_time = invalid_date.replace(hour=18, minute=0)  # Hora inválida

    # Configuración de IDs de cabañas
    if cabaña == "243":
        device_ids = [arrayan_id]
    elif cabaña == "244":
        device_ids = [araucaria_id]
    elif cabaña == "2462":
        if personas == 1:
            device_ids = [maiten_id, maiten2_id]
        else:
            device_ids = [maiten_id]
    elif cabaña == "2915":
        device_ids = [canelo_id]
    else:
        return jsonify({"error": "Invalid cabaña"}), 400

    responses = []

    # Procesar cada dispositivo
    def process_device(device_id):
        access_token, _ = get_access_token(client_id, secret)
        device_info = get_device_info(client_id, secret, access_token, device_id)
        local_key = device_info.get("local_key")

        temp_key_info = get_temp_key(client_id, secret, access_token, device_id)
        ticket_key = temp_key_info.get("ticket_key")
        ticket_id = temp_key_info.get("ticket_id")

        ticket_key_desencriptado = decrypt_ticket_key(ticket_key, secret)
        contraseña_encriptada = encrypt_password(password, ticket_key_desencriptado)

        body = {
            "password": contraseña_encriptada,
            "password_type": "ticket",
            "ticket_id": ticket_id,
            "effective_time": str(int(effective_time.timestamp())),
            "invalid_time": str(int(invalid_time.timestamp())),
            "name": name,
        }

        sign_temp_pass, t_tp = calc_sign_t(client_id, secret, access_token, "POST", f"/v1.0/devices/{device_id}/door-lock/temp-password", body=body)

        headers_temp_pass = {
            "time_zone": "America/Santiago",
            "client_id": client_id,
            "sign": sign_temp_pass,
            "t": t_tp,
            "type": "0",
            "sign_method": "HMAC-SHA256",
            "access_token": access_token,
        }

        response_temp_pass = requests.post(f"{url}/v1.0/devices/{device_id}/door-lock/temp-password", headers=headers_temp_pass, json=body)

        if response_temp_pass.status_code == 200:
            data_temp_pass = response_temp_pass.json()
            return {device_id: data_temp_pass}
        else:
            return {device_id: {"error": "Failed to generate temporary password", "status_code": response_temp_pass.status_code}}

    for device_id in device_ids:
        response = process_device(device_id)
        responses.append(response)

    return jsonify(responses)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

