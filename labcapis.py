from flask import Flask, request, jsonify
from database import get_db_connection, crear_tabla, insertar_persona
import datetime

app = Flask(__name__)

# Crear la tabla cuando se inicie la aplicación
crear_tabla()

@app.route('/agregar-persona', methods=['POST'])
def agregar_persona():
    # Obtener los datos del JSON en la solicitud POST
    data = request.json
    nombre = data.get("nombre")
    apellido = data.get("apellido")
    dia = datetime.datetime.now().date()  # Obtener la fecha actual
    
    # Insertar los datos en la base de datos
    insertar_persona(nombre, apellido, dia)
    
    return jsonify({"message": "Persona agregada exitosamente"}), 201

@app.route('/', methods=['GET'])
def index():
    return '¡Bienvenido! Esta es una aplicación para agregar personas.'

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
