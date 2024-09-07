import os
import datetime
from flask import Flask, request, jsonify
import requests
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from utils import calc_sign, calc_sign_t, decrypt_ticket_key, encrypt_password, get_access_token, get_device_info, get_temp_key

app = Flask(__name__)

# Configuraciones para el primer código
def verificar_token():
    token_esperado = os.getenv('passkey')  # Reemplaza con tu token esperado
    token_recibido = request.headers.get('Authorization')
    if token_recibido != token_esperado:
        return False
    return True

def enviar_mensaje(sender, recipient, content):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.getenv('API_KEY')

    api_instance = sib_api_v3_sdk.TransactionalSMSApi(sib_api_v3_sdk.ApiClient(configuration))
    send_transac_sms = sib_api_v3_sdk.SendTransacSms(sender=sender, recipient=recipient, content=content)

    try:
        api_response = api_instance.send_transac_sms(send_transac_sms)
        return api_response.to_dict()
    except ApiException as e:
        return {'error': str(e)}

@app.route('/send_sms', methods=['POST'])
def send_sms():
    # Verificar si el token es válido
    if not verificar_token():
        return jsonify({'error': 'Unauthorized'}), 401
     # Continuar con el envío de SMS
    data = request.json
    sender = data.get('sender')
    recipient = data.get('recipient')
    content = data.get('content')

    if not sender or not recipient or not content:
        return jsonify({'error': 'Missing data'}), 400

    response = enviar_mensaje(sender, recipient, content)
    return jsonify(response)

# Configuraciones para el segundo código
url = "https://openapi.tuyaus.com"
client_id = "nnvgkh44nmp3d7myx5x5"
secret = "ceef72f07adb416d9d0e2e1c8b0cfb5b"
arrayan_id = "ebe1294b3db744f4cdnkww"
araucaria_id = "eb239c162bd8d0a036bivl"
maiten_id = "ebbc95369829715271pjwv"
maiten2_id = "eb3fca956ac0559b3bf41p"
canelo_id = "eb2b767d79ec7b926am0pa"

hora_efectiva = datetime.time(15, 0)  # 15:00 horas
hora_invalida = datetime.time(14, 0)  # 14:00 horas

@app.route('/generate-temp-password', methods=['POST'])
def generate_temp_password():
    # Verificar si el token es válido
    if not verificar_token():
        return jsonify({'error': 'Unauthorized'}), 401
    # Configuraciones para la clave de la puerta
    data = request.json
    name = data.get("name")
    password = data.get("password")
    cabaña = data.get("cabaña")
    personas = data.get("personas")
    effective_date = datetime.datetime.strptime(data.get("effective_time"), "%d-%m-%Y")
    invalid_date = datetime.datetime.strptime(data.get("invalid_time"), "%d-%m-%Y")

    effective_time = effective_date.replace(hour=hora_efectiva.hour, minute=hora_efectiva.minute)
    invalid_time = invalid_date.replace(hour=hora_invalida.hour, minute=hora_invalida.minute)
    
    # Configuraciones id para las cabañas
    if cabaña == "131":
        device_ids = [arrayan_id]
    elif cabaña == "132":
        device_ids = [araucaria_id]
    elif cabaña == "2462":
        if personas == "0":
            device_ids = [maiten_id]
        else:
            # Enviar a ambos dispositivos si personas es "1"
            device_ids = [maiten_id, maiten2_id]
    elif cabaña == "2915":
        device_ids = [canelo_id]
    else:
        return jsonify({"error": "Invalid cabaña"}), 400


    # Preparacion para envio de contraseñas a tuyasmart

    for device_id in device_ids:   
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
            return jsonify(data_temp_pass)
        else:
            return jsonify({"error": "Failed to generate temporary password"}), response_temp_pass.status_code

# Maneja solicitudes GET a la raíz de la aplicación
@app.route('/', methods=['GET'])
def index():
    return '¡Bienvenido! Esta es una aplicación para enviar mensajes SMS y configurar puertas de seguridad.'

# Maneja solicitudes GET a favicon.ico
@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
